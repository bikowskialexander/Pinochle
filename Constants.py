

# ========================================
#              Constants
#   Contains constants used by all files
# ========================================


# ========================================
#              Gameplay
# ========================================

SUITS = ['HEARTS', 'SPADES', 'DIAMONDS', 'CLUBS']
CARDS = ['9', 'J', 'Q', 'K', '10', 'A']

# How many times a model is given to give the correct answer before game over
ATTEMPTS_TILL_FAILURE = 10


# ========================================
#              Meld
# ========================================

MELD_OPTIONS = ["nine of trumps", "marriage", "royal marriage", "run", "pinochle", "double pinochle", "aces", "kings", "queens", "jacks"]

NINES_POINTS = 10
MARRIAGE_POINTS = 20
ROYAL_MARRIAGE_POINTS = 40
PINOCHLE_POINTS = 40
DOUBLE_PINOCHLE_POINTS = 300
RUN_POINTS = 150
ACES_POINTS = 100
KINGS_POINTS = 80
QUEENS_POINTS = 60
JACKS_POINTS = 40

MELD_POINTS = {"nine of trumps": NINES_POINTS, 
               "marriage": MARRIAGE_POINTS,
               "royal marriage": ROYAL_MARRIAGE_POINTS,
               "run": RUN_POINTS,
               "aces": ACES_POINTS,
               "kings": KINGS_POINTS,
               "queens": QUEENS_POINTS,
               "jacks": JACKS_POINTS,
               "pinochle": PINOCHLE_POINTS,
               "double pinochle": DOUBLE_PINOCHLE_POINTS} 

# ========================================
#              Tricks
# ========================================

ACE_TRICK = 11
TEN_TRICK = 10
KING_TRICK = 4
QUEEN_TRICK = 3
JACK_TRICK = 2
NINE_TRICK = 0
LAST_TRICK = 10

TRICK_VALUE_DICT = {
    'A':ACE_TRICK,
    '10':TEN_TRICK,
    'K':KING_TRICK,
    'Q':QUEEN_TRICK,
    'J':JACK_TRICK,
    '9':NINE_TRICK
}


# ========================================
#              Tested Models
# ========================================

GRANITE4_1_8B = "granite4.1:8b"
GRANITE4_1_3B = "granite4.1:3b"
GRANITE4_1B = "granite4:1b"
GRANITE4_350M = "granite4:350M"
QWEN_3_5_0_8B = "qwen3.5:0.8b"
QWEN_3_5_9B = "qwen3.5:9b"
QWEN_3_5_4B = "qwen3.5:4b"
QWEN_3_5_37B = "qwen3.5:27b"
GPTOSS = "gpt-oss:latest"
NEMOTRON_MINI_4B = "nemotron-mini:4b"
NEMOTRON_NANO_4B = "nemotron-3-nano:4b"
COGITO = "cogito:latest"
LLAMA_3_2 = "llama3.2:latest"
GEMMA4_E2B = "gemma4:e2b"

# Used model 
DEFAULT_MODEL = NEMOTRON_NANO_4B


# ========================================
#              Messages
# ========================================

PASS_FAILURE_MESSAGE = "The last output given was not accepted. Please Try Again."
TRICK_FAILURE_MESSAGE = PASS_FAILURE_MESSAGE + " \nCRITICAL: Do **NOT** give the same output. Here is the last output: " 


