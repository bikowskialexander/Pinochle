
from Opponent import Opponent

class User_Opponent(Opponent):
    def __init__(self):
        self.ui=None
        super().__init__()

    def get_bid(self, current, hand, additional_message=""):
        return self.ui.get_user_bidding_choice(current)
    
    def get_trumps(self, hand, additional_message=""):
        return self.ui.get_user_trump_choice()

    def get_tricks(self, hand, trumps, played, additional_message=""):
        return super().get_tricks(hand, trumps, played, additional_message)



