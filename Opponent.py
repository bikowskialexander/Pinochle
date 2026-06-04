

import random
import ast 
from ollama import chat 

import Meld

from Constants import *

class Opponent:

    def __init__(self) -> None:
        self.messages = []

    def get_bid(self, current, hand) -> str:
        if random.random() > 0.5:
            return "PASS" 
        else:
            return 10 + current
        
    def get_trumps(self, hand):
        return "HEARTS"
        
    def get_pass(self, hand : dict, trumps : str) -> str:
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

    def get_tricks(self, hand, trumps, played) -> str:
        suit = SUITS[random.randint(0,3)]
        value = CARDS[random.randint(0, len(CARDS)-1)]
        return (suit, value)


class Ollama_Opponent(Opponent):

    def __init__(self) -> None:
        super().__init__()
        self.model = "llama3.1:8b"

    def _valid_trick_format(self, trick):
        try:
            ast.literal_eval(trick)
            return True
        except:
            return False

    def get_tricks(self, hand, trumps, played) -> str:
        new_message_content = "You are playing Pinochle. Output only a card in (SUIT, value) form."
        new_message_content += "\n trumps is " + str(trumps) + " and you have: \n"
        new_message_content += str(hand)
        new_message_content += "\n the cards " + str(played) + " have been played."
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        response = chat(model=self.model, messages=self.messages)['message']['content']
        while not self._valid_trick_format(response):
            print(response)
            response = chat(model=self.model, messages=self.messages)['message']['content']
        return ast.literal_eval(response)

