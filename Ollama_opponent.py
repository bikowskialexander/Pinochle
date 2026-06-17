
import random
import ast 
import re
from typing import Tuple

from ollama import chat 

from Constants import *
from Opponent import Opponent
import checks

class Ollama_Opponent(Opponent):

    def __init__(self) -> None:
        super().__init__()
        self.model = DEFAULT_MODEL

    def _parse_card(self, card_str: str) -> Tuple[str, str]:
        return checks.parse_card(card_str)
        
    def _message_and_response(self, new_message_content):
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        response = chat(model=self.model, messages=self.messages, think=False)['message']['content']
        structured_response = {'role':'assistant', 'content':response}
        self.messages.append(structured_response)
        return response.strip()
        
    def get_bid(self, current: int, hand: dict, additional_message="") -> str:

        # Get the prompt from the file
        file = open("Prompts/Bid.txt")
        new_message_content = file.read()
        file.close()
        
        # Inject additional context and hand data
        if additional_message:
            new_message_content += f"Notice: {additional_message}\n"
        new_message_content += f"Your current hand data: {str(hand)}\n\n"
        new_message_content += "Evaluate your hand strength. Output your decision (either PASS or the number) now:"
        
        return self._message_and_response(new_message_content)

    def get_trumps(self, hand: dict, additional_message="") -> str:
        new_message_content = (
            "You are playing Pinochle and have won the bid. You must now declare the trump suit.\n\n"
            "CRITICAL RULES AND FORMATTING CONSTRAINTS:\n"
            "- You must ONLY output a single suit string name.\n"
            "- The suit name must be written in ALL CAPS (e.g., SPADES, HEARTS, CLUBS, or DIAMONDS).\n"
            "- Do not wrap your response in markdown code blocks (do not use ```text or ```).\n"
            "- Do not include any punctuation, quotes, filler words, or explanatory sentences.\n"
            "- Your output must contain the single word for the suit and absolutely nothing else.\n\n"
        )
        
        # Inject the feedback/error message if a previous attempt failed validation
        if additional_message:
            new_message_content += f"ATTENTION (PREVIOUS ATTEMPT FAILED):\n{additional_message}\n\n"
        
        # Inject the raw hand data for the test evaluation
        new_message_content += f"Your Hand Data: {str(hand)}\n\n"
        new_message_content += "Evaluate your hand strength and declare the trump suit now:"
        
        return self._message_and_response(new_message_content)
    
    def get_pass(self, hand: dict, trumps: str, additional_message="") -> str:
        
        file = open("Prompts/Passing.txt")
        new_message_content = file.read()
        file.close()
        
        # Inject the error/feedback message if a previous attempt failed validation
        if additional_message:
            new_message_content += f"ATTENTION (PREVIOUS ATTEMPT FAILED):\n{additional_message}\n\n"
        
        # Inject the raw game state variables for the test
        new_message_content += f"Trump Suit: {str(trumps).upper()}\n"
        new_message_content += f"Your Hand Data: {str(hand)}\n\n"
        new_message_content += "Process your hand data and output your list of four card tuples now:"
        
        return self._message_and_response(new_message_content)
    
    def get_meld(self, hand, trumps, additional_message="") -> str:
        import Deck
        Deck.print_deck(hand)
        print(trumps)
        print()
        # Read in file for meld prompt
        meld_file = open("Prompts/Meld.txt", 'r')
        new_message_content = meld_file.read()
        
        # Inject current game state
        if additional_message != "":
            new_message_content += f"ATTENTION (PREVIOUS ATTEMPT FAILED):\n{additional_message}\n\n"
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
        file = open("Prompts/Tricks.txt")
        new_message_content = file.read()
        file.close()

        # Inject game state context
        if additional_message != "":
            new_message_content += f"ATTENTION (PREVIOUS ATTEMPT FAILED):\n{additional_message}\n\n"
        new_message_content += f"\n\nThe trump suit for this hand is: {str(trumps).upper()}\n"
        new_message_content += f"Your current hand is: {str(hand)}\n"
        new_message_content += f"The cards played so far this trick (in order) are: {str(played)}\n\n"
        
        new_message = {'role':'user', 'content':new_message_content}
        self.messages.append(new_message)
        return self._message_and_response(new_message_content)

