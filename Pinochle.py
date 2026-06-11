
import random
import checks
import Deck
import Meld
import ast 
import copy
from UI import PinochleUI

from Constants import *

from Opponent import Opponent
from Ollama_opponent import Ollama_Opponent

class Pinochle:

    def __init__(self) -> None:
        self.players = [Ollama_Opponent(), Opponent(), Ollama_Opponent(), Opponent()]
        self.move_index = 0
        self.stage = "BID"
        self.current_bid = 250
        self.hands = []
        self.point_values = [0, 0]
        self.tricks_left = 12
        self.ui = PinochleUI()

        self.player_index = 1

        self.files = open("logs/log.txt", 'w')

        self.setup()

    def setup(self):
        deck = Deck.generate_ordered_deck()
        for i in range(4):
            self.hands.append(Deck.draw_hand(deck, 12))
        self.ui.update_hands(self.hands)
        self.winner = -1
        self.stage = "BID"
        self.tricks_left = 12 

    def define_order(self):
        self.order = []
        for i in range(self.move_index, 4):
            self.order.append(i)
        for i in range(0, self.move_index):
            self.order.append(i)

    def step(self) -> dict:
        if self.game_over() != -1:
            print("Game won by", self.winner, "team")
            last_winner = self.winner
            self.setup()
            return last_winner
        self.files.close()
        self.files = open("logs/log.txt", 'a')
        print(self.stage)
        self.define_order()
        if self.stage == "BID":
            self.bid_taker_index = self.do_bid()
            if self.bid_taker_index != None:
                self.ui.set_score(['North', 'South', 'East', 'West'][self.bid_taker_index], self.current_bid)
            self.stage = "TRUMPS"
        elif self.stage == "TRUMPS":
            self.trumps = self.do_trumps()
            self.stage = "PASS"
        elif self.stage == "PASS":
            self.do_pass()
            self.stage = "MELD"
        elif self.stage == "MELD":
            self.do_meld()
            self.stage = "TRICKS"
        elif self.stage == "TRICKS":
            self.do_tricks()
        return -1

    def _add_to_logs(self, adding, player=""):
        self.files.write(adding + "\n")
        if player == "":
            self.files.write('---------------------------\n')
        else:
            self.files.write('---------- Played by ' + str(player) + '---\n')

    def do_bid(self):
        player_left_count = 4
        players_left = {0:True, 1:True, 2:True, 3:True}
        while True:
            for i in self.order:
                if player_left_count > 1:
                    if players_left[i]:
                        bid = self.players[i].get_bid(self.current_bid, self.hands[i])
                        self._add_to_logs(bid)
                        # Number of attempts the llm has taken
                        attempts = 1

                        while not checks.is_a_bid(bid, self.current_bid) and attempts < ATTEMPTS_TILL_FAILURE:
                            bid = self.players[i].get_bid(self.current_bid, self.hands[i])
                            
                            # Add attempt
                            attempts += 1
                            
                            self._add_to_logs(bid)
                        if attempts >= ATTEMPTS_TILL_FAILURE:
                            if i == 0 or i == 2:
                                self.winner = 1
                            else:
                                self.winner = 0
                            self.bid_taker_index = None 
                            return None 
                        if bid != "PASS":
                            self.current_bid = bid
                        else:
                            players_left[i] = False
                            player_left_count -= 1
                else:
                    for i in range(4):
                        if players_left[i]:
                            return i

    def do_trumps(self):
        request = self.players[self.bid_taker_index].get_trumps(self.hands[self.bid_taker_index]) 
        self._add_to_logs(request)

        attempts = 1
        while not checks.is_a_suit(request) and attempts < ATTEMPTS_TILL_FAILURE:
            request = self.players[self.bid_taker_index].get_trumps(self.hands[self.bid_taker_index]) 
            self._add_to_logs(request)
            attempts += 1

        # If too many attempts taken, the bidding team loses
        if attempts >= ATTEMPTS_TILL_FAILURE:
            if self.bid_taker_index == 0 or self.bid_taker_index == 2:
                self.winner = 1
            else:
                self.winner = 0

        return request.upper()
    
    def get_valid_pass(self, index):
        request = self.players[index].get_pass(self.hands[index], self.trumps).upper()
        self._add_to_logs(request)
        attempts = 1
        while not checks.check_passed(self.hands[index], request) and attempts < ATTEMPTS_TILL_FAILURE:
            request = self.players[index].get_pass(self.hands[index], self.trumps, PASS_FAILURE_MESSAGE).upper()
            self._add_to_logs(request)
            attempts += 1
        if attempts >= ATTEMPTS_TILL_FAILURE:
            if index == 0 or index == 2:
                self.winner = 1
            else:
                self.winner = 0
        return request 

    def do_pass(self):
        other_index = 0
        if self.bid_taker_index == 1:
            other_index = 3 
        elif self.bid_taker_index == 3:
            other_index = 1
        elif self.bid_taker_index == 0:
            other_index = 2

        p1 = self.get_valid_pass(self.bid_taker_index)
        p2 = self.get_valid_pass(other_index)

        for card in ast.literal_eval(p1):
            self.hands[other_index][card[0]].append(card[1])
            self.hands[self.bid_taker_index][card[0]].remove(card[1])
        for card in ast.literal_eval(p2):
            self.hands[self.bid_taker_index][card[0]].append(card[1])
            self.hands[other_index][card[0]].remove(card[1])

    def meld_value(self, meld_str):
        meld = meld_str.split('\n')
        points = 0
        for m in meld:
            p = checks.parse_game_string(m)
            if len(p) > 0:
                points += MELD_POINTS[p[0].lower()]
        return points

    def do_meld(self):
        for i in range(len(self.players)):
            meld = self.players[i].get_meld(self.hands[i], self.trumps).strip()
            self._add_to_logs(meld, i)
            attempts = 1
            while attempts < ATTEMPTS_TILL_FAILURE and not checks.check_meld_valid(self.hands[i], str(meld), self.trumps):
                meld = self.players[0].get_meld(self.hands[i], self.trumps)
                self._add_to_logs(meld)
                attempts += 1
            if attempts >= ATTEMPTS_TILL_FAILURE:
                if i == 0 or i == 2:
                    self.winner = 1
                else:
                    self.winner = 0
            if i == 0 or i == 2:
                self.point_values[0] += self.meld_value(meld)
            else:
                self.point_values[1] += self.meld_value(meld)

    def game_over(self):
        if self.winner != -1:
            return self.winner
        elif self.point_values[0] >= 250:
            return 0
        elif self.point_values[1] >= 250:
            return 1
        return -1

    def do_tricks(self):
        self.move_index = self.bid_taker_index
        self.define_order()
        self.played = []
        for i in self.order:
            trick = self.players[i].get_tricks(self.hands[i], self.trumps, self.played) 
            self._add_to_logs(trick)
            attempts = 1
            while attempts < ATTEMPTS_TILL_FAILURE and not checks.check_trick(self.played, self.hands[i], trick, self.trumps):
                trick = self.players[i].get_tricks(self.hands[i], self.trumps, self.played) 
                self._add_to_logs(trick)
                attempts += 1
            if attempts >= ATTEMPTS_TILL_FAILURE:
                if i == 0 or i == 2:
                    self.winner = 1
                else:
                    self.winner = 0
            trick = checks.parse_card(trick)
            self.hands[i][trick[0]].remove(trick[1])
            self.played.append(trick)
            print(str(i), "Played:", trick)
        self.tricks_left -= 1

    def run(self):
        self.ui.render()
        while self.step() == -1:
            self.ui.update_hands(self.hands)
            self.ui.render()

p = Pinochle()
p.run()


