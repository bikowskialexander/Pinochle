
from Constants import *
from Opponent import Opponent
from Multi_Agent_Opponent import Multi_Agent_Opponent


class Model_Against_User(Multi_Agent_Opponent):
    def __init__(self) -> None:
        super().__init__()
        self.bot_opponent = Opponent()
        self.bid_model = GRANITE4_350M
        self.trumps_model = GRANITE4_350M
        self.trick_model = QWEN_3_5_9B

    def get_meld(self, hand, trumps, additional_message="") -> str:
        return self.bot_opponent.get_meld(hand, trumps, additional_message="")




