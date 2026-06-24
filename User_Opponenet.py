
from UI import index_to_Direction_name
from Opponent import Opponent

class User_Opponent(Opponent):
    def __init__(self):
        super().__init__()
        self.ui = 1

    def get_bid(self, current, hand, additional_message=""):
        return self.ui.get_user_bidding_choice(current)
    
    def get_trumps(self, hand, additional_message=""):
        return self.ui.get_user_trump_choice()
    
    def get_pass(self, hand, trumps, additional_message=""):
        print(self.ui.get_user_passing_choice())
        return super().get_pass(hand, trumps, additional_message)

    def get_tricks(self, hand, trumps, played, additional_message=""):
        return super().get_tricks(hand, trumps, played, additional_message)



