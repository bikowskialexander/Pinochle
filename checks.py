

import ast 
import re

from Constants import *

def is_a_card_value(n : str):
    try:
        CARDS.index(n)
        return True
    except ValueError:
        return False
    
def is_a_card(card : tuple):
    if len(card) != 2:
        return False 
    if is_a_suit(card[0]):
        return is_a_card_value(card[1])
    return False 
            
    
def has_card(hand, card : tuple):
    try:
        hand[card[0].upper()].index(card[1])
    except:
        return False 
    return True

def parse_game_string(raw_str):
    """
    Bypasses ast.literal_eval to completely avoid ValueErrors.
    Extracts quoted words directly and structures them into a list and tuples.
    """
    # 1. Find all quoted segments in the string
    # This grabs 'marriage', 'SPADES', 'K', etc., completely ignoring commas/brackets
    tokens = re.findall(r"['\"]([^'\"]+)['\"]", raw_str)
    
    if not tokens:
        return []
        
    # The first token is always your action/status ('marriage', 'nine of trumps')
    action = tokens[0]
    
    # The remaining tokens are your cards (Suit, Rank, Suit, Rank...)
    # We group them into pairs of tuples
    card_tokens = tokens[1:]
    cards = [(card_tokens[i], card_tokens[i+1]) for i in range(0, len(card_tokens), 2)]
    
    # Combine them back into your expected structure
    return [action] + cards

# ---------------------------------------------------
#                   For Bids
# ---------------------------------------------------


# Checks if a bid is possible
def is_a_bid(response, lowest):
    if response == 'PASS':
        return True
    try:
        response_value = int(response) 
        return (response_value > lowest)
    except:
        return False    


# ---------------------------------------------------
#                   For Trumps
# ---------------------------------------------------

def is_a_suit(response : str):
    response = response.upper()
    try:
        SUITS.index(response)
        return True
    except ValueError:
        return False 
    
    
# ---------------------------------------------------
#                   For Passing
# ---------------------------------------------------


# This needs to be adjusted for multiple of the same card
def check_passed(hand, response : str):
    try:
        cards = ast.literal_eval(response)

        if len(cards) != 4:
            return False 
        
        for card in cards:
            if is_a_card(card) == False or has_card(hand, card) == False:
                return False

        return True 
    
    except:
        return False 


# ---------------------------------------------------
#                   For Meld
# ---------------------------------------------------



def is_meld(name):
    try:
        MELD_OPTIONS.index(name.lower())
        return True
    except:
        return False
    
def check_meld_valid(hand, response : str, trumps):
    melds = response.split('\n')
    if response == "":
            return True
    for meld in melds:
        if meld == "" or meld == " " or meld == "\n":
            return True
        meld = parse_game_string(meld)
        meld_type = meld[0].lower() 
        cards = meld[1::]
        for card in cards:
            if has_card(hand, card) == False:
                return False
        if is_meld(meld_type) == False:
            return False 
        if meld_type == 'aces':
            if check_four_of_a_kind_meld(cards, 'aces') == False:
                return False
        elif meld_type == 'kings':
            if check_four_of_a_kind_meld(cards, 'kings') == False:
                return False
        elif meld_type == 'queens':
            if check_four_of_a_kind_meld(cards, 'queens') == False:
                return False
        elif meld_type == 'jacks':
            if check_four_of_a_kind_meld(cards, 'jacks') == False:
                return False
        elif meld_type == 'marriage':
            if check_for_marriage(cards) == False:
                return False 
        elif meld_type == 'royal marriage':
            if check_royal_marriage(cards, trumps) == False:
                return False 
        elif meld_type == "nine of trumps":
            if check_nines(cards, trumps) == False:
                return False 
        elif meld_type == "pinochle":
            if check_pinochle(cards) == False:
                return False
        elif meld_type == "double pinochle":
            if check_double_pinochle(cards) == False:
                return False 
        elif meld_type == "run":
            if check_run(cards, trumps) == False:
                return False
        else:
            return False
    return True
    
def check_run(cards, suit):
    needed = ['A', '10', 'K', 'Q', 'J']
    for card in cards:
        try:
            needed.remove(card[1])
        except ValueError:
            return False 
        if card[0] != suit:
            return False 
    return True

def check_double_pinochle(cards : list):
    if len(cards) != 4:
        return False 
    for i in range(4):
        for j in range(4):
            if check_pinochle([cards[i], cards[j]]):
                cards.pop(i)
                cards.pop(j)
                break
    if len(cards) == 2:
        return check_pinochle(cards)
    return False 

def check_pinochle(cards):
    if cards[1][0] == 'J' and cards[0][1] == 'diamonds':
        if cards[1][0] == 'Q' and cards[0][0] == 'spades':
            return True
    if cards[1][0] == 'Q' and cards[0][0] == 'spades':
        if cards[1][0] == 'J' and cards[0][1] == 'diamonds':
            return True
    return False 

def check_nines(cards, suit):
    if cards[0][1] == '9':
        if cards[0][0].upper() == suit.upper():
            return True
    return False 

def check_royal_marriage(cards, suit):
    if cards[0][0] == suit:
        return check_for_marriage(cards)
    return False 

def check_for_marriage(cards):
    if cards[0][0] == cards[1][0]:
        if cards[0][1] == 'K':
            if cards[1][1] == 'Q':
                return True
        if cards[0][1] == 'Q':
            if cards[1][1] == 'K':
                return True
    return False  

def check_four_of_a_kind_meld(cards : list, kind):
    card_check = cards[0][1]
    suits = {'hearts':0, 'spades':0, 'clubs':0, 'diamonds':0}
    for card in cards[1::]:
        suits[card[0]] += 1
        if suits[card[0]] > 1:
            return False 
        if card[0] != card_check:
            return False
    if kind == "aces":
        return card[0][1] == 'A'
    if kind == 'kings':
        return card[0][1] == 'K'
    if kind == 'queens':
        return card[0][1] == 'Q'
    if kind == 'jacks':
        return card[0][1] == 'J'
    

# ---------------------------------------------------
#                   For Tricks
# ---------------------------------------------------

def check_trick_first(hand, card):
    try:
        card = str(card)
        card = ast.literal_eval(card)
        if is_a_card(card):
            if has_card(hand, card):
                return True
        return False
    except:
        return False
    
def check_tricks_after_first(card, hand, played, trumps):
    try:
        if check_trick_first(hand, card)== False:
            return False
        
        card = str(card)
        card = ast.literal_eval(card)

        suit = played[0][0].lower()
        max_value_of_suit = CARDS.index(played[0][1])
        for p in played[1::]:
            if p[0] == suit:
                index = CARDS.index(p[1])
                if index > max_value_of_suit:
                    max_value_of_suit = index

        if card[0].lower() == suit.lower(): # if the same suit
            index = CARDS.index(card[1])
            if index > max_value_of_suit:
                return True
            else:
                for c in hand[suit]:
                    if CARDS.index(c) > max_value_of_suit:
                        return False  
                if CARDS.index(card[0]) == max_value_of_suit:
                    return True
        else: # if a different suit
            if len(hand[suit]) == 0: # if none of suit
                
                if card[1].lower() == trumps:
                    # Check for highest trump
                    max_trump_index = None
                    for p in played[1::]:
                        index = CARDS.index(p[1])
                        if p[0] == trumps:
                            if max_trump_index == None or index > max_trump_index:
                                max_trump_index = index
                    if max_trump_index == None:
                        return True
                    if len(hand[trumps]) == 1:
                        return True
                    if len(hand[trumps]) == 2:
                        if hand[trumps][0] == hand[trumps][1]:
                            return True
                    if CARDS.index(card[1]) > max_trump_index: # if it is highest yet
                        return True
                    else:
                        if CARDS.index(card[1]) == max_trump_index: # if played the same
                            # check for higher trumps
                            for c in hand[trumps]: 
                                if CARDS.index(c) > max_trump_index: # if a higher exists
                                    return False
                            return True  
                        else:
                            # Check for other higher
                            for c in hand[trumps]:
                                if CARDS.index(c) > max_trump_index:
                                    return False
                            return True # there are no trumps higher
                else: # if did not play trumps
                    if len(hand[trumps]) == 0:
                        return True
                    else:
                        return False
            else:
                return False
    except:
        return False

def check_trick(played, hand, card, trumps):
    if len(played) == 0:
        return check_trick_first(hand, card)
    else:
        return check_tricks_after_first(card, hand, played, trumps)






