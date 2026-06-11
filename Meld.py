
from Constants import *

def get_melds(hand, trumps):
    melds = []
    for suit in SUITS:
        try:
            hand[suit].index('K')
            hand[suit].index('Q')
            if suit != trumps:
                melds.append(['marriage', (suit.upper(), 'K'), (suit.upper(), 'Q')])
            else:
                melds.append(['royal marriage', (suit.upper(), 'K'), (suit.upper(), 'Q')])
        except:
            pass 
        try:
            if suit == trumps:
                hand[suit].index('A')
                hand[suit].index('10')
                hand[suit].index('K')
                hand[suit].index('Q')
                hand[suit].index('J')
                melds.append(["run"])
                for c in ['A', '10', 'K', 'Q', 'J']:
                    melds[-1].append(suit.upper(), c)
        except:
            pass 
        # End of loop

    try:
        hand[trumps].index('9')
        melds.append(['nine of trumps', (trumps.upper(), '9')])
    except:
        pass 
    try:
        for suit in SUITS:
            hand[suit].index['A'] 
        melds.append(['aces'])
        for suit in SUITS:
            melds.append((suit.upper(), 'A'))
    except:
        pass 
    try:
        for suit in SUITS:
            hand[suit].index['K'] 
        melds.append(['kings'])
        for suit in SUITS:
            melds.append((suit.upper(), 'K'))
    except:
        pass 
    try:
        for suit in SUITS:
            hand[suit].index['Q'] 
        melds.append(['queens'])
        for suit in SUITS:
            melds.append((suit.upper(), 'Q'))
    except:
        pass 
    try:
        for suit in SUITS:
            hand[suit].index['J'] 
        melds.append(['jacks'])
        for suit in SUITS:
            melds.append((suit.upper(), 'J'))
    except:
        pass 
    try:
        hand['diamonds'].index('J')
        hand['spades'].index('Q')
        melds.append(['pinochle', ('SPADES', 'Q'), ('DIAMONDS', 'J')])
    except:
        pass 
    try:
        i1 = hand['diamonds'].index('J')
        i2 = hand['spades'].index('Q')
        hand['diamonds'].index('J', i1+1)
        i2 = hand['spades'].index('Q', i2+1)
        melds.append(['double pinochle', ('SPADES', 'Q'), ('DIAMONDS', 'J'), ('SPADES', 'Q'), ('DIAMONDS', 'J')])
    except:
        pass 
    m_string = ""
    for m in melds:
        m_string += str(m) + '\n'
    return m_string

