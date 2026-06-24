
from UI import index_to_Direction_name
from Opponent import Opponent

from checks import check_trick

class User_Opponent(Opponent):
    def __init__(self):
        super().__init__()
        self.ui = 1

    def get_bid(self, current, hand, additional_message=""):
        return self.ui.get_user_bidding_choice(current)
    
    def get_trumps(self, hand, additional_message=""):
        return self.ui.get_user_trump_choice()
    
    def get_pass(self, hand, trumps, additional_message=""):
        results = self.ui.get_user_passing_choice()
        return str(results)

    def get_tricks(self, hand, trumps, played, additional_message=""):
        available = []
        for suit in hand.keys():
            if suit != 'len':
                for rank in hand[suit]:
                    card = (suit, rank)
                    if check_trick(played, hand, card, trumps):
                        available.append(card)
        result = self.ui.get_user_trick_choice(available)
        return str(result)



