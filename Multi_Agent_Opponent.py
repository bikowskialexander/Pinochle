
from Constants import *

from Ollama_opponent import Ollama_Opponent


class Multi_Agent_Opponent(Ollama_Opponent):

    def __init__(self) -> None:
        super().__init__()
        self.bid_model = DEFAULT_MODEL
        self.trumps_model = DEFAULT_MODEL
        self.pass_model = DEFAULT_MODEL
        self.meld_model = DEFAULT_MODEL
        self.trick_model = DEFAULT_MODEL

    def get_bid(self, current: int, hand: dict, additional_message="") -> str:
        self.model = self.bid_model
        return super().get_bid(current, hand, additional_message)

    def get_trumps(self, hand: dict, additional_message="") -> str:
        self.model = self.trumps_model
        return super().get_trumps(hand, additional_message)

    def get_pass(self, hand: dict, trumps: str, additional_message="") -> str:
        self.model= self.pass_model
        return super().get_pass(hand, trumps, additional_message)

    def get_meld(self, hand, trumps, additional_message="") -> str:
        self.model = self.meld_model
        return super().get_meld(hand, trumps, additional_message) 

    def get_tricks(self, hand, trumps, played, additional_message="") -> str:
        self.model = self.trick_model
        return super().get_tricks(hand, trumps, played, additional_message)