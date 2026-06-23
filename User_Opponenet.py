
from Opponent import Opponent

class User_Opponent(Opponent):
    def __init__(self):
        self.ui=None
        super().__init__()

    def get_bid(self, current, hand, additional_message=""):
        return self.ui.get_user_bidding_choice(current)





