
import random
import checks
import Deck
import Meld
import ast 

from Constants import *

class Opponent:

    def __init__(self) -> None:
        self.messages = []

    def get_bid(self, current) -> str:
        if random.random() > 0.5:
            return "PASS" 
        else:
            return 10 + current
        
    def get_trumps(self):
        return "HEARTS"
        
    def get_pass(self, hand : dict) -> str:
        lst = []
        count = 0
        suit_counter = 0
        for suit in SUITS:
            while count < 4 and len(hand[suit]) > suit_counter:
                value = hand[suit][suit_counter]
                lst.append([suit, value])
                suit_counter += 1
                count += 1
            else:
                suit_counter = 0
        return str(lst)

    def get_meld(self, hand, trumps) -> str:
        meld = Meld.get_melds(hand, trumps)
        return meld 

    def get_tricks(self) -> str:
        pass 


class Pinochle:

    def __init__(self) -> None:
        self.players = [Opponent(), Opponent(), Opponent(), Opponent()]
        self.move_index = 0
        self.stage = "BID"
        self.current_bid = 250
        self.hands = []
        self.point_values = [0, 0]

        self.setup()

    def setup(self):
        deck = Deck.generate_ordered_deck()
        for i in range(4):
            self.hands.append(Deck.draw_hand(deck, 12))

    def define_order(self):
        self.order = []
        for i in range(self.move_index, 4):
            self.order.append(i)
        for i in range(0, self.move_index):
            self.order.append(i)

    def step(self) -> dict:
        self.define_order()
        if self.stage == "BID":
            self.bid_taker_index = self.do_bid()
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

    def do_bid(self):
        player_left_count = 4
        players_left = {0:True, 1:True, 2:True, 3:True}
        while True:
            for i in self.order:
                if player_left_count > 1:
                    if players_left[i]:
                        bid = self.players[i].get_bid(self.current_bid)
                        while not checks.is_a_bid(bid, self.current_bid):
                            bid = self.players[i].get_bid(self.current_bid)
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
        request = self.players[self.bid_taker_index].get_trumps() 
        while not checks.is_a_suit(request):
            request = self.players[self.bid_taker_index].get_trumps() 
        return request.upper()
    
    def get_valid_pass(self, index):
        p = self.players[index].get_pass(self.hands[index])
        while not checks.check_passed(self.hands[index], p):
            p = self.players[index].get_pass(self.hands[index])
        return p 

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
                points += MELD_POINTS[p[0]]
        return points

    def do_meld(self):
        for i in range(len(self.players)):
            meld = self.players[i].get_meld(self.hands[i], self.trumps).strip()
            while not checks.check_meld_valid(self.hands[i], str(meld), self.trumps):
                meld = self.players[0].get_meld(self.hands[i], self.trumps)
            if i == 0 or i == 2:
                self.point_values[0] += self.meld_value(meld)
            else:
                self.point_values[1] += self.meld_value(meld)

    def do_tricks(self):
        pass 

p = Pinochle()
p.step()
p.step()
p.step()
p.step()


