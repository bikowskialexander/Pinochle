

# ================================================================
#           This file is used to run a playable version
# ================================================================


from Pinochle import Pinochle
from User_Opponenet import User_Opponent
from Opponent import Opponent 
from Model_Agains_User import Model_Against_User


def main():
    p = Pinochle()
    p.players = [User_Opponent(), Opponent(), Opponent(), Opponent()]
    p.run()
    while True:
        if p.game_over() == 0:
            p.ui.display_winner("You Won")
        else:
            p.ui.display_winner("You Lost")


if __name__ == "__main__":
    main()
