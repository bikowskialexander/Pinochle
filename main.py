

# ================================================================
#           This file is used to run a playable version
# ================================================================


from Pinochle import Pinochle


def main():
    p = Pinochle()
    p.run()
    while True:
        if p.game_over() == 0:
            p.ui.display_winner("You Won")
        else:
            p.ui.display_winner("You Lost")


if __name__ == "__main__":
    main()
