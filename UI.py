import pygame
import sys

import Deck

from Constants import *

# --- Base Design Constants ---
BASE_WIDTH = 1300
BASE_HEIGHT = 900
BASE_CARD_W = 60
BASE_CARD_H = 90
BASE_MARGIN = 10
BASE_FONT_SIZE = 24
BASE_SUIT_SIZE = 30 

# Colors
BG_COLOR = (34, 139, 34)
CARD_COLOR = (255, 255, 255)
TEXT_BLACK = (0, 0, 0)
TEXT_RED = (210, 0, 0)
MELD_COLOR = (255, 215, 0)
SELECTION_COLOR = (0, 255, 0)
HOVER_COLOR = (144, 238, 144)

# Sorting / Display Order - Internally lowercase for UI processing mapping
RANK_ORDER = {'A': 5, '10': 4, 'K': 3, 'Q': 2, 'J': 1, '9': 0}
DISPLAY_SUIT_ORDER = ['spades', 'hearts', 'clubs', 'diamonds']

SUIT_SYMBOLS = {'spades': '♠', 'hearts': '♥', 'clubs': '♣', 'diamonds': '♦'}
SUIT_COLORS = {'spades': TEXT_BLACK, 'hearts': TEXT_RED, 'clubs': TEXT_BLACK, 'diamonds': TEXT_RED}

def index_to_Direction_name(index : int) -> str:
    return ['North', 'East', 'South', 'West'][index]

class PinochleUI:
    def __init__(self):
        pygame.init()
        
        # 1. Determine Scale
        info = pygame.display.Info()
        monitor_w = info.current_w
        monitor_h = info.current_h

        scale_w = (monitor_w * 0.9) / BASE_WIDTH
        scale_h = (monitor_h * 0.9) / BASE_HEIGHT
        self.scale = min(scale_w, scale_h)
        
        # 2. Apply Scale
        self.screen_w = int(BASE_WIDTH * self.scale)
        self.screen_h = int(BASE_HEIGHT * self.scale)
        self.card_w = int(BASE_CARD_W * self.scale)
        self.card_h = int(BASE_CARD_H * self.scale)
        self.margin = int(BASE_MARGIN * self.scale)
        self.pad_large = int(80 * self.scale)
        self.pad_small = int(40 * self.scale)

        # 3. Init Screen & Fonts
        self.screen = pygame.display.set_mode((self.screen_w, self.screen_h))
        pygame.display.set_caption(f"Pinochle (Scale: {self.scale:.2f})")
        self.clock = pygame.time.Clock()
        
        scaled_font_main = int(BASE_FONT_SIZE * self.scale)
        scaled_font_suit = int(BASE_SUIT_SIZE * self.scale)
        
        self.font_main = pygame.font.SysFont('arial', scaled_font_main, bold=True)
        self.font_suit = pygame.font.SysFont('arial', scaled_font_suit) 

        # Data Stores (Suits completely lowercase internally)
        self.hands = {'North': [], 'South': [], 'East': [], 'West': []}
        self.center_cards = {}
        self.meld_highlights = {'North': set(), 'South': set(), 'East': set(), 'West': set()}
        self.green_highlights = {'North': set(), 'South': set(), 'East': set(), 'West': set()}
        self.scores = {'North': 0, 'South': 0, 'East': 0, 'West': 0}
        
        self.player_names = {
            'North': 'Bot North', 'South': 'Bot South', 
            'East': 'Bot East', 'West': 'Bot West'
        }

        self.clickable_rects = [] 
        self._pending_user_click = None

    def sleep(self, seconds):
        """Pauses execution for 'seconds' while keeping the window responsive."""
        start_ticks = pygame.time.get_ticks()
        target_ticks = seconds * 1000
        while pygame.time.get_ticks() - start_ticks < target_ticks:
            self.render()

    def get_latest_from_user(self):
        if self._pending_user_click:
            card = self._pending_user_click
            self._pending_user_click = None
            return card
        return None

    def set_player_names(self, names_dict):
        for pos, name in names_dict.items():
            if pos in self.player_names:
                self.player_names[pos] = name

    def set_score(self, player, points):
        if player in self.scores:
            self.scores[player] = points

    def update_hands(self, player_hands):
        for p in ['North', 'East', 'South', 'West']:
            self.hands[p] = []
        for player in range(4):
            player_name = ['North', 'East', 'South', 'West'][player]
            for suit in SUITS:
                # Accepts uppercase SUITS global, converts to map lowercase input dict keys
                suit_lower = suit.upper()
                if suit_lower in player_hands[player]:
                    for card in player_hands[player][suit_lower]:
                        self.hands[player_name].append((suit_lower, card))

    def play_card(self, player, card_tuple):
        # Force string extraction and enforce uppercase to match the flat tuple list
        suit = str(card_tuple[0]).upper()
        rank = str(card_tuple[1]).upper()
        target_card = (suit, rank)

        if player in self.hands:
            # Direct removal bypasses validation rules entirely
            if target_card in self.hands[player]:
                self.hands[player].remove(target_card)
            
            # Advance game and UI state variables
            self.center_cards[player] = target_card
            
            if target_card in self.meld_highlights.get(player, []):
                self.meld_highlights[player].remove(target_card)
            if target_card in self.green_highlights.get(player, []):
                self.green_highlights[player].remove(target_card)
            
   
    def display_meld(self, player, card_list, points):
        if player not in self.meld_highlights: return
        self.scores[player] = points
        new_highlights = set()
        for (suit, rank) in card_list:
            new_highlights.add((suit.lower(), rank))
        self.meld_highlights[player] = new_highlights

    def clear_meld(self, player):
        if player in self.meld_highlights:
            self.meld_highlights[player] = set()
            self.scores[player] = 0

    def highlight_card(self, player, card_tuple):
        input_suit, input_rank = card_tuple
        target = (input_suit.lower(), input_rank)
        if player in self.green_highlights:
            self.green_highlights[player].add(target)

    def unhighlight_card(self, player, card_tuple):
        input_suit, input_rank = card_tuple
        target = (input_suit.lower(), input_rank)
        if player in self.green_highlights and target in self.green_highlights[player]:
            self.green_highlights[player].remove(target)

    def clear_table(self):
        self.center_cards = {}

    # --- DRAWING LOGIC ---

    def _draw_card(self, x, y, rank, suit, border_color=(0, 0, 0), border_thickness=2):
        suit = suit.lower()
        card_rect = pygame.Rect(x, y, self.card_w, self.card_h)
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=5)
        pygame.draw.rect(self.screen, border_color, card_rect, border_thickness, border_radius=5)

        color = SUIT_COLORS.get(suit, (0,0,0))
        symbol = SUIT_SYMBOLS.get(suit, '?')
        
        rank_surf = self.font_main.render(rank, True, color)
        offset_x = int(5 * self.scale)
        offset_y_rank = int(2 * self.scale)
        self.screen.blit(rank_surf, (x + offset_x, y + offset_y_rank))

        suit_surf = self.font_suit.render(symbol, True, color)
        offset_y_suit = int(28 * self.scale)
        self.screen.blit(suit_surf, (x + offset_x, y + offset_y_suit))
        
        return card_rect

    def _get_border_style(self, player, card_tuple):
        if card_tuple in self.green_highlights[player]: return SELECTION_COLOR, 5
        if card_tuple in self.meld_highlights[player]: return MELD_COLOR, 5
        return (0, 0, 0), 2

    def _draw_hand_horizontal(self, player_key, start_y):
        cards = self.hands[player_key]
        if not cards: return
        
        total_width = (len(cards) * (self.card_w + self.margin)) - self.margin
        start_x = (self.screen_w - total_width) // 2

        is_user = self.player_names[player_key] == 'user'

        for i, (suit, rank) in enumerate(cards):
            x = start_x + i * (self.card_w + self.margin)
            color, thick = self._get_border_style(player_key, (suit, rank))
            
            mouse_pos = pygame.mouse.get_pos()
            rect = pygame.Rect(x, start_y, self.card_w, self.card_h)
            
            if is_user and rect.collidepoint(mouse_pos):
                color = HOVER_COLOR
                thick = 4

            card_rect = self._draw_card(x, start_y, rank, suit, color, thick)
            
            if is_user:
                # Returns the suit parameter back upstream transformed as uppercase to match your game logic expectation
                self.clickable_rects.append((card_rect, (suit.upper(), rank)))

    def _draw_hand_grid(self, player_key, is_left_side):
        cards = self.hands[player_key]
        if not cards: return
        cols = 2
        rows = (len(cards) + cols - 1) // cols
        
        total_height = rows * (self.card_h + self.margin)
        start_y = (self.screen_h - total_height) // 2
        
        if is_left_side:
            start_x = self.pad_large
        else:
            start_x = self.screen_w - (self.card_w * 2 + self.margin) - self.pad_large

        for i, (suit, rank) in enumerate(cards):
            row = i // cols
            col = i % cols
            x = start_x + col * (self.card_w + self.margin)
            y = start_y + row * (self.card_h + self.margin)
            color, thick = self._get_border_style(player_key, (suit, rank))
            self._draw_card(x, y, rank, suit, color, thick)

    def _draw_center_trick(self):
        cx, cy = self.screen_w // 2, self.screen_h // 2
        offsets = {
            'North': (cx - self.card_w // 2, cy - self.card_h - self.margin),
            'South': (cx - self.card_w // 2, cy + self.margin),
            'West':  (cx - self.card_w - self.margin * 2, cy - self.card_h // 2),
            'East':  (cx + self.margin * 2,              cy - self.card_h // 2)
        }
        for player, (suit, rank) in self.center_cards.items():
            if player in offsets:
                x, y = offsets[player]
                self._draw_card(x, y, rank, suit)

    def draw_labels(self):
        h_labels = [
            (f"{self.player_names['North']}: {self.scores['North']}", self.screen_w//2, self.pad_small),
            (f"{self.player_names['South']}: {self.scores['South']}", self.screen_w//2, self.screen_h - self.pad_small),
        ]
        for text, x, y in h_labels:
            surf = self.font_main.render(text, True, (255, 255, 255))
            rect = surf.get_rect(center=(x, y))
            self.screen.blit(surf, rect)

        side_margin_center = self.pad_large // 2 
        
        west_text = f"{self.player_names['West']}: {self.scores['West']}"
        west_surf = self.font_main.render(west_text, True, (255, 255, 255))
        west_rotated = pygame.transform.rotate(west_surf, 90)
        west_rect = west_rotated.get_rect(center=(side_margin_center, self.screen_h // 2))
        self.screen.blit(west_rotated, west_rect)

        east_text = f"{self.player_names['East']}: {self.scores['East']}"
        east_surf = self.font_main.render(east_text, True, (255, 255, 255))
        east_rotated = pygame.transform.rotate(east_surf, -90)
        east_rect = east_rotated.get_rect(center=(self.screen_w - side_margin_center, self.screen_h // 2))
        self.screen.blit(east_rotated, east_rect)

    def _draw_scene(self):
        self.screen.fill(BG_COLOR)
        self.clickable_rects = [] 
        self.draw_labels()
        self._draw_hand_horizontal('North', self.pad_large)
        self._draw_hand_horizontal('South', self.screen_h - self.card_h - self.pad_large)
        self._draw_hand_grid('West', is_left_side=True)
        self._draw_hand_grid('East', is_left_side=False)
        self._draw_center_trick()
        pygame.display.flip()

    def render(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.clear_table()
            
            if event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1: 
                    mouse_pos = event.pos
                    for rect, (suit, rank) in self.clickable_rects:
                        if rect.collidepoint(mouse_pos):
                            self._pending_user_click = (suit, rank)
                            break

        self._draw_scene()
        self.clock.tick(30)

# --- TEST BLOCK ---
if __name__ == "__main__":
    game = PinochleUI()

    game.set_player_names({
        'North': 'AI_North',
        'South': 'user',
        'East':  'AI_East',
        'West':  'AI_West'
    })

    # Kept input deck initialization keys lowercase to reflect your game state storage format
    full_hands = [
        { 'spades': ['A', '10', 'K'], 'hearts': ['A', '10', 'K'], 'clubs': ['A', '10', 'K'], 'diamonds': ['A', '10', 'K'] },
        { 'spades': ['A', 'A', '10', '10', 'K', 'K', 'Q', 'Q', 'J', 'J'], 'diamonds': ['A', '10'], 'hearts': [], 'clubs': [] },
        { 'clubs': ['Q', 'Q', 'J', 'J', '9', '9'], 'hearts': ['Q', 'Q', 'J', 'J', '9', '9'], 'spades': [], 'diamonds': [] },
        { 'diamonds': ['Q', 'Q', 'J', 'J', '9', '9'], 'spades': ['9', '9'], 'clubs': ['A', '10'], 'hearts': ['A', '10'] }
    ]
    
    game.update_hands(full_hands)

    print("--- Testing Sleep Function ---")
    
    # 1. Accepts uppercase parameter format seamlessly 
    game.play_card('North', ('HEARTS', 'A'))
    game.sleep(2.0) 
    
    # 2. Handles alternate flipped-tuple parameters gracefully
    game.play_card('East', ('9', 'HEARTS'))
    game.sleep(2.0) 
    
    print("System Ready. Polling for user clicks...")
    
    while True:
        game.render()
        user_card = game.get_latest_from_user()
        if user_card:
            print(f"GAME LOGIC: Received input {user_card}")  # Will print out uppercase suit variant
            game.play_card('South', user_card)