
import random 
from Constants import *

def generate_ordered_deck():
    deck = {'len':0}
    for suit in SUITS:
        deck[suit] = []
        for _ in range(2):
            for card in CARDS:
                deck[suit].append(card)
                deck["len"] += 1
    return deck 

def draw_random(deck):
    length = deck['len']
    selection = random.randint(0, length-1)
    current = 0
    for s in range(len(SUITS)):
        for c in range(len(deck[SUITS[s]])):
            if current == selection:
                deck['len'] -= 1
                return deck[SUITS[s]].pop(c), SUITS[s]
            current += 1

def draw_hand(deck, size):
    hand = {"len":size}
    for suit in SUITS:
        hand[suit] = []
    for _ in range(size):
        card = draw_random(deck)
        hand[card[1]].append(card[0])
    return hand


def print_deck(deck):
    for suit in SUITS:
        print(suit, ":", deck[suit])
