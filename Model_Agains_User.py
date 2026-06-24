
from Constants import *
from Opponent import Opponent
from Multi_Agent_Opponent import Multi_Agent_Opponent


class Model_Against_User(Multi_Agent_Opponent):
    def __init__(self) -> None:
        super().__init__()
        self.bot_opponent = Opponent()
        self.bid_model = GRANITE4_350M
        self.trumps_model = GRANITE4_350M
        self.trick_model = NEMOTRON_NANO_4B

        self.attempts = 0

    def get_meld(self, hand, trumps, additional_message="") -> str:
        return self.bot_opponent.get_meld(hand, trumps, additional_message="")
    
    def get_tricks(self, hand, trumps, played, additional_message=""):
        if additional_message == "":
            self.attempts = 1
        else:
            self.attempts += 1
        if self.attempts >= 9:
            return self.get_trick_backup(hand, trumps, played)
        return super().get_tricks(hand, trumps, played, additional_message)
    
    def get_trick_backup(self, hand, trumps, played,  additional_message="") -> str:
        return self.bot_opponent.get_tricks(hand, trumps, played)




