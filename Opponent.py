

import random
import ast 
import re
from typing import Tuple

from ollama import chat 

import checks

import Meld

from Constants import *

class Opponent:

    def __init__(self) -> None:
        self.messages = []
        self._add_system()

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


class Ollama_Opponent(Opponent):

    def __init__(self) -> None:
        super().__init__()
        self.model = DEFAULT_MODEL

    def _parse_card(self, card_str: str) -> Tuple[str, str]:
        return checks.parse_card(card_str)

    def _valid_trick_format(self, trick):
        try:
            self._parse_card(trick)
            return True
        except ValueError:
            return False
        
    def _message_and_response(self, new_message_content):
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        response = chat(model=self.model, messages=self.messages)['message']['content']
        structured_response = {'role':'assistant', 'content':response}
        self.messages.append(structured_response)
        return response.strip()
        
    def get_bid(self, current, hand, additional_message=""):
        new_message_content = "You are in the bid phase. Either output PASS or a bid higher than the current."
        new_message_content += "\nThe current bid is " + str(current)
        new_message_content += "Here is your hand: " + str(hand)
        new_message_content += "\nCRITICAL: Output either PASS or a number"
        new_message_content += "\n - example A: PASS"
        new_message_content += "\n - example B: 260"
        return self._message_and_response(new_message_content)

    def get_trumps(self, hand, additional_message=""):
        new_message_content = "You are picking trumps. Here is your hand " + str(hand)
        new_message_content += "\nOut only a suit" 
        return self._message_and_response(new_message_content)
    
    def get_pass(self, hand: dict, trumps: str, additional_message="") -> str:
        new_message_content = (
            "You are playing Pinochle and are in the passing phase.\n"
            "You must select exactly FOUR cards from your hand to pass to your teammate.\n\n"
            "CRITICAL OUTPUT FORMAT RULES:\n"
            "- You must output the cards as a single, flat Python list containing exactly four card tuples.\n"
            "- Each card tuple must strictly follow the format: ('SUIT', 'rank') with uppercase suits.\n"
            "- Do not wrap the output in markdown code blocks like ```python ... ```. Output raw text only.\n"
            "- Do not include any commentary, reasoning, intro, or outro text.\n\n"
            "EXACT STRUCTURAL EXAMPLE:\n"
            "[('SPADES', 'A'), ('SPADES', '10'), ('HEARTS', 'K'), ('DIAMONDS', 'Q')]\n\n"
        )
        
        # Inject game state details
        new_message_content += f"The trump suit is: {str(trumps).upper()}\n"
        new_message_content += f"Your current hand is: {str(hand)}\n\n"
        new_message_content += "Select your FOUR best passing cards and output them now matching the structural example layout exactly:"
        
        return self._message_and_response(new_message_content)
    
    def get_meld(self, hand, trumps, additional_message="") -> str:
        new_message_content = (
            "You are playing Pinochle and are in the Meld phase.\n"
            "Your task is to declare your melds using the cards from your hand.\n\n"
            "CRITICAL OUTPUT FORMAT RULES:\n"
            "- You must output your melds as a valid Python list of lists.\n"
            "- Each inner list must represent ONE meld, starting with the meld name string followed by the card tuples.\n"
            "- The card tuples must strictly use the format: ('SUIT', 'rank') with uppercase suits.\n"
            "- EACH MELD LIST MUST BE ON ITS OWN LINE.\n"
            "- Do not wrap the output in markdown code blocks like ```python ... ```. Output raw text only.\n"
            "- Do not include any analysis, introduction, or commentary.\n\n"
            "EXACT LINE-SEPARATED STRUCTURAL EXAMPLE:\n"
            "  [\"Marriage\", ('DIAMONDS', 'K'), ('DIAMONDS', 'Q')]\n"
            "  [\"Pinochle\", ('SPADES', 'Q'), ('DIAMONDS', 'J')]\n"
        )
        
        # Inject current game state
        new_message_content += f"Your current hand is: {str(hand)}\n"
        new_message_content += f"The trump suit is: {str(trumps).upper()}\n"
        new_message_content += f"Valid meld names you can use: {str(MELD_OPTIONS)}\n\n"
        new_message_content += "Construct your highest scoring valid melds and output them now following the line-separated example structure exactly:"
        
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        response = chat(model=self.model, messages=self.messages)['message']['content']
        return response.strip()

    def get_tricks(self, hand, trumps, played, additional_message="") -> str:
        # Enforce strict uppercase system formatting instructions
        new_message_content = (
            "You are playing Pinochle and are in the trick-taking phase.\n"
            "Your output must be strictly limited to a single valid Python tuple in the format: ('SUIT', 'rank').\n"
            "Example valid outputs: ('HEARTS', 'A') or ('SPADES', '10').\n"
            "Do not include any introductory commentary, thinking text, or surrounding markdown code blocks.\n\n"
        )
        
        # Inject game state context
        new_message_content += f"The trump suit for this hand is: {str(trumps).upper()}\n"
        new_message_content += f"Your current hand is: {str(hand)}\n"
        new_message_content += f"The cards played so far this trick (in order) are: {str(played)}\n\n"
        
        # Strategy rules reminder to optimize AI decision boundaries
        new_message_content += (
            "Rules Reminders:\n"
            "- You must follow the lead suit if you are able to.\n"
            "- If you can follow the lead suit, you must beat the highest card of that suit on the table if possible.\n"
            "- If you are void of the lead suit, you must play a trump card and beat any trumps already played if possible.\n\n"
            "CRITICAL: Output EXACTLY ONE card tuple and nothing else."
        ) 
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        response = chat(model=self.model, messages=self.messages)['message']['content']
        while not self._valid_trick_format(response):
            response = chat(model=self.model, messages=self.messages)['message']['content']
        return self._message_and_response(new_message_content)

