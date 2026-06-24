

import random


import checks

import Meld

from Constants import *

class Opponent:

    def __init__(self) -> None:
        self.messages = []
        self._add_system()
        self.ui = -1

    def _add_system(self, system_file_name="Prompts/System.txt"):
        f = open(system_file_name)
        prompt_content = f.read()
        prompt = {'role':'system', 'content':prompt_content}
        self.messages.append(prompt)

    def get_bid(self, current, hand, additional_message="") -> str:
        if random.random() > 0.5:
            return "PASS" 
        else:
            return str(10 + int(current))
        
    def get_trumps(self, hand,  additional_message="") -> str:
        return "HEARTS"
        
    def get_pass(self, hand : dict, trumps : str,  additional_message="") -> str:
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

    def get_meld(self, hand, trumps,  additional_message="") -> str:
        meld = Meld.get_melds(hand, trumps)
        return meld 

    def get_tricks(self, hand, trumps, played,  additional_message="") -> str:
        for suit in SUITS:
            for rank in hand[suit]:
                card = (suit.upper(), rank)
                if checks.check_trick(played, hand, card, trumps):
                    return str(card)

