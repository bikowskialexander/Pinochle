

import ast 
import re
from typing import Tuple
import copy 

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
        return (response_value >= lowest+10)
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

def parse_passed_cards(response_str: str) -> list:
    """
    Takes a raw string containing a list of card tuples from the LLM,
    cleans it up, parses it, and returns a valid Python list of tuples.
    
    Example Input: "[('SPADES', 'A'), ('SPADES', '10'), ('HEARTS', 'K'), ('DIAMONDS', 'Q')]"
    Example Output: [('SPADES', 'A'), ('SPADES', '10'), ('HEARTS', 'K'), ('DIAMONDS', 'Q')]
    """
    try:
        # 1. Clean up potential markdown code fences (```python ... ```) if the LLM leaked them
        cleaned_str = response_str.strip()
        cleaned_str = re.sub(r'^```[a-zA-Z]*\s*', '', cleaned_str)
        cleaned_str = re.sub(r'\s*```$', '', cleaned_str)
        cleaned_str = cleaned_str.strip()
        
        # 2. Extract just the list part [...] if there happens to be trailing text
        list_match = re.search(r'\[.*\]', cleaned_str, re.DOTALL)
        if list_match:
            cleaned_str = list_match.group(0)
            
        # 3. Safely parse the string representation into a real Python object
        parsed_data = ast.literal_eval(cleaned_str)
        
        # 4. Final verification that we received a list of tuples
        if isinstance(parsed_data, list):
            # Ensure every item inside is a tuple (or force it to be one)
            return [tuple(card) for card in parsed_data]
            
        print(f"[ERROR] Parsed data was a {type(parsed_data)}, expected a list.")
        return []
        
    except (ValueError, SyntaxError) as e:
        print(f"[ERROR] Failed to parse card string structure: {e}")
        return []


def check_passed(hand, response : str):
    try:
        cards = parse_passed_cards(response)

        if len(cards) != 4:
            return False 
        
        hand_copy = copy.deepcopy(hand)
        for card in cards:
            if is_a_card(card) == False or has_card(hand_copy, card) == False:
                return False
            hand_copy[card[0].upper()].remove(card[1])
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
    try:
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
    except:
        return False
    
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
    """
    Validates the first card led in a trick.
    Card must be a valid structure and must exist in the player's hand.
    """
    try:
        # card format: (SUIT, value)
        suit = card[0].upper() # Enforce uppercase for hand key lookups
        rank = card[1]
        
        if suit in hand and rank in hand[suit]:
            return True
        return False
    except (IndexError, AttributeError, TypeError):
        return False


def check_tricks_after_first(card, hand, played, trumps):
    """
    Validates a card played subsequent to the trick lead.
    Ensures correct rules for following suit or trumping are adhered to.
    """
    try:
        # 1. Base check: Does the player even have the card?
        if not check_trick_first(hand, card):
            return False
        
        # Keep string comparisons normalized to lowercase, 
        # but map dictionary keys strictly to uppercase.
        card_suit_lower = card[0].lower()
        card_val = card[1]
        trumps_lower = trumps.lower()
        
        # 2. Extract Lead Suit data from the first played card
        lead_suit_lower = played[0][0].lower()
        max_value_of_suit = CARDS.index(played[0][1])
        
        # Find highest matching lead-suit card on the table
        for p in played[1:]:
            if p[0].lower() == lead_suit_lower:
                index = CARDS.index(p[1])
                if index > max_value_of_suit:
                    max_value_of_suit = index

        # --- CASE A: Player is following the Lead Suit ---
        if card_suit_lower == lead_suit_lower:
            card_index = CARDS.index(card_val)
            if card_index > max_value_of_suit:
                return True
            else:
                # Fixed: Access hand using uppercase key
                for c in hand.get(lead_suit_lower.upper(), []):
                    if CARDS.index(c) > max_value_of_suit:
                        return False  # Forced to win if capable
                return True

        # --- CASE B: Player is shedding or trumping (Different Suit) ---
        else:
            # Fixed: Access hand using uppercase key to check if truly void
            if len(hand.get(lead_suit_lower.upper(), [])) == 0:
                
                # Subcase B1: Player plays a Trump Card
                if card_suit_lower == trumps_lower:
                    max_trump_index = None
                    for p in played:
                        if p[0].lower() == trumps_lower:
                            index = CARDS.index(p[1])
                            if max_trump_index is None or index > max_trump_index:
                                max_trump_index = index
                    
                    # If no trumps have been played yet, any played trump is legal
                    if max_trump_index is None:
                        return True
                        
                    card_index = CARDS.index(card_val)
                    if card_index > max_trump_index:
                        return True
                    else:
                        # Fixed: Access hand using uppercase key
                        for c in hand.get(trumps_lower.upper(), []):
                            if CARDS.index(c) > max_trump_index:
                                return False
                        return True  
                
                # Subcase B2: Player sluffs a regular off-suit card
                else:
                    # Fixed: Access hand using uppercase key
                    if len(hand.get(trumps_lower.upper(), [])) == 0:
                        return True
                    else:
                        return False
            else:
                return False
    except (IndexError, ValueError, KeyError, TypeError):
        return False

def parse_card(card_str: str) -> Tuple[str, str]:
    """
    Extract the suit and rank from a string in the form
    "('SUIT','rank')" (with optional spaces).

    Parameters
    ----------
    card_str : str
        The string to parse.  It may contain leading/trailing whitespace.

    Returns
    -------
    tuple[str, str]
        A tuple ``(suit, rank)``.

    Raises
    ------
    ValueError
        If *card_str* does not match the expected format.
    """
    # Strip outer whitespace first – makes the pattern a bit cleaner.
    card_str = card_str.strip()

    # Regex:
    #   \(            – literal '('
    #   \s*           – optional whitespace
    #   '([^']+)'     – a single‑quoted non‑empty string (captured)
    #   \s*,\s*       – a comma surrounded by optional whitespace
    #   '([^']+)'     – second single‑quoted string (captured)
    #   \s*\)         – optional whitespace and a closing ')'
    pattern = r"\(\s*'([^']+)'\s*,\s*'([^']+)'\s*\)"

    match = re.fullmatch(pattern, card_str)
    if not match:                     # pragma: no cover
        raise ValueError(
            f"'{card_str}' is not a valid card representation "
            f"– expected format \"('SUIT','rank')\""
        )
    suit, rank = match.group(1), match.group(2)
    return suit, rank

def valid_trick_format(trick):
    try:
        parse_card(trick)
        return True
    except ValueError:
        return False

def check_trick(played, hand, card : str, trumps):
    """
    Main entry point for verifying if playing 'card' is legal.
    """
    try:
        card = str(card)
        if valid_trick_format(card):
            card = parse_card(card)
            if len(played) == 0:
                return check_trick_first(hand, card)
            else:
                # Fixed parameter pass sequence to match check_tricks_after_first
                return check_tricks_after_first(card, hand, played, trumps)
    except:
        return False



