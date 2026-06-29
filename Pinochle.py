
import random
import checks
import Deck
import Meld
import ast 
import copy
from UI import PinochleUI, index_to_Direction_name

from Constants import *

from Opponent import Opponent
from Ollama_opponent import Ollama_Opponent
from Multi_Agent_Opponent import Multi_Agent_Opponent
from Model_Agains_User import Model_Against_User
from User_Opponenet import User_Opponent

class Pinochle:

    def __init__(self) -> None:
        self.players = [Opponent(), Opponent(), Opponent(), Opponent()]
        self.move_index = 0
        self.stage = "BID"
        self.current_bid = 240
        self.hands = []
        self.point_values = [0, 0]
        self.tricks_left = 12
        self.ui = PinochleUI()

        self.player_index = 1
        self.winner = -1
        self.points_to_win = 250

        self.round_point_values = [0,0]

        self.files = open("logs/log.txt", 'w')

        self.has_user = True

        # Timing
        self.trick_sleep_time = 0
        self.bid_sleep_time = 0
        self.trumps_sleep_time = 0

        for i in range(4):
            if self.players[i].ui == 1:
                self.players[i].ui = self.ui 
                direction = index_to_Direction_name(i)
                self.ui.is_user[direction] = True
                self.ui.user_direction = direction
                self.has_user = True

        self.setup()

    def setup(self):
        self.hands = []
        deck = Deck.generate_ordered_deck()
        for i in range(4):
            self.hands.append(Deck.draw_hand(deck, 12))
        self.ui.update_hands(self.hands)
        self.stage = "BID"
        self.tricks_left = 12 
        self.current_bid = 240
        self.round_point_values = [0,0]
        
        # Reset scoreboards
        self._reset_scoreboard()
        self.ui.set_team_scores(self.point_values[0], self.point_values[1])

        # Reset Center
        self.ui.clear_table()

    def _reset_scoreboard(self):
        for i in range(4):
            direction = index_to_Direction_name(i)
            self.ui.set_score(direction, 0)
            self.ui.reset_score_transparency(direction)

    def define_order(self):
        self.order = []
        for i in range(self.move_index, 4):
            self.order.append(i)
        for i in range(0, self.move_index):
            self.order.append(i)

    def clear_messages(self):
        for i in range(4):
            system_prompt = self.players[i].messages[0]
            self.players[i].messages.clear()
            self.players[i].messages.append(system_prompt)

    def step(self) -> dict:

        # Work to do when the round is over
        if self.round_over():
            index = 1
            other_index = 0
            if self.bid_taker_index == 0 or self.bid_taker_index == 2:
                index = 0
                other_index = 1
            if self.round_point_values[index] < int(self.current_bid):
                self.point_values[index] -= int(self.current_bid)
                self.point_values[other_index] += self.round_point_values[other_index]
            else:
                self.point_values[index] += self.round_point_values[index]
                self.point_values[other_index] += self.round_point_values[other_index]

            # Update team scores
            self.ui.set_team_scores(self.point_values[0], self.point_values[1])
            
            # Work to do if the game is over
            if self.game_over() != -1:
                print("Game won by", self.game_over(), "team")
                last_winner = self.game_over()
                self.setup()
                return last_winner

            # Reset the board
            self.setup()

        self.files.close()
        self.files = open("logs/log.txt", 'a')
        print(self.stage)
        self.define_order()
        if self.stage == "BID":
            self.bid_taker_index = int(self.do_bid())
            if self.bid_taker_index != None:
                self.ui.set_score(['North', 'East', 'South', 'West'][self.bid_taker_index], self.current_bid)
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
            self.clear_messages()
            self.ui.clear_table()
            self.do_tricks()
        return self.game_over()

    def _add_to_logs(self, adding, player=""):
        self.files.write(adding + "\n")
        if player == "":
            self.files.write('---------------------------\n')
        else:
            self.files.write('---------- Played by ' + str(player) + '----------\n')

    def do_bid(self):
        player_left_count = 4
        players_left = {0: True, 1: True, 2: True, 3: True}
        while True:
            for i in self.order:
                if player_left_count > 1:
                    if players_left[i]:

                        # Highlight the bidder
                        player_direction = index_to_Direction_name(i)
                        self.ui.highlight_bidder(player_direction)
                        self.ui.render()

                        # Get the bid from the player
                        bid = self.players[i].get_bid(self.current_bid, self.hands[i])
                        
                        # Add the bid from the player to the log
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

                        # Pause the display for a time
                        self.ui.sleep(self.bid_sleep_time)
                        self.ui.remove_bidder_highlight(player_direction)

                        if bid == "PASS":
                            self.ui.set_score_translucent(player_direction)
                        
                else:
                    for i in range(4):
                        if players_left[i]:
                            self.move_index = i
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

        # Display selection
        self.ui.set_displayed_trump(request.upper())
        self.ui.display_trump_panel()
        self.ui.sleep(self.trumps_sleep_time)
        self.ui.clear_displayed_trump()

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
                meld = self.players[0].get_meld(self.hands[i], self.trumps).strip()
                self._add_to_logs(meld, i)
                attempts += 1
            if attempts >= ATTEMPTS_TILL_FAILURE:
                if i == 0 or i == 2:
                    self.winner = 1
                else:
                    self.winner = 0
            if i == 0 or i == 2:
                self.round_point_values[0] += self.meld_value(meld)
            else:
                self.round_point_values[1] += self.meld_value(meld)

    def game_over(self):
        if self.round_over():
            if self.winner != -1:
                return self.winner
            elif self.point_values[0] >= self.points_to_win:
                return 0
            elif self.point_values[1] >= self.points_to_win:
                return 1
        return -1
    
    def round_over(self):
        for i in range(4):
            for suit in SUITS:
                if len(self.hands[i][suit]) > 0:
                    return False
        return True
    
    def _add_trick_points(self):
        points = 0
        for i in range(4):
            rank = self.played[i][1]
            points += TRICK_VALUE_DICT[rank]
        if self.move_index == 0 or self.move_index == 2:
            self.round_point_values[0] += points
        else:
            self.round_point_values[1] += points

    def _set_move_index_to_winner_of_trick(self):

        # Set max to the rank of the first card
        highest_rank = self.played[0][1]
        highest_rank_index = 0

        # Set suit used to the first suit
        suit_used = self.played[0][0]

        # Loop through cards
        for i in range(1,4):

            # If a higher non-trumps has been played, or trumps was played first
            ith_value = CARDS.index(self.played[i][1])
            highest_rank_value = CARDS.index(highest_rank)


            if ith_value > highest_rank_value and self.played[i][0].lower() == suit_used.lower():
                highest_rank_index = self.order[i]
                highest_rank =  self.played[i][1]

            # If the trick was trumped
            elif self.played[i][0].lower() == self.trumps.lower() and suit_used.lower() != self.trumps.lower():
                suit_used = self.trumps
                highest_rank_index = self.order[i]
                highest_rank =  self.played[i][1]

        # Update the index of the first move
        self.move_index = highest_rank_index

    def do_tricks(self):

        # List to keep all played cards, given to agents 
        self.played = []

        # Play loop
        for i in self.order:

            # Get the turn order
            self.define_order()

            # First attempt to get trick
            trick = self.players[i].get_tricks(self.hands[i], self.trumps, self.played) 
            self._add_to_logs(trick)
            attempts = 1

            # Future attempts
            while attempts < ATTEMPTS_TILL_FAILURE and not checks.check_trick(self.played, self.hands[i], trick, self.trumps):
                trick = self.players[i].get_tricks(self.hands[i], self.trumps, self.played, TRICK_FAILURE_MESSAGE + trick) 
                self._add_to_logs(trick)
                attempts += 1

            # If valid response could not be generated
            if attempts >= ATTEMPTS_TILL_FAILURE:
                if i == 0 or i == 2:
                    self.winner = 1
                else:
                    self.winner = 0
            else: # Valid response generated
                # Play trick
                trick = checks.parse_card(trick)
                self.hands[i][trick[0]].remove(trick[1])
                self.played.append(trick)

                # Update the UI
                player_name = index_to_Direction_name(i)
                self.ui.play_card(player_name, trick)
                self.ui.update_hands(self.hands)
                self.ui.render()
                self.ui.sleep(self.trick_sleep_time)

        # Update Turn Order and add points
        if attempts < ATTEMPTS_TILL_FAILURE:
            self._set_move_index_to_winner_of_trick()
            self._add_trick_points()

        # Update the number of tricks
        self.tricks_left -= 1

        # Sleep at very end of trick
        self.ui.render()
        self.ui.sleep(self.trick_sleep_time)

    def run(self):
        self.ui.render()
        while self.step() == -1:
            self.ui.update_hands(self.hands)
            self.ui.render()
        return self.game_over()


