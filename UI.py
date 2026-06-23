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

HOVER_COLOR = (200, 245, 200) # Slightly deeper hover green for distinct contrast
BUTTON_BG = (230, 230, 230)    # Light gray baseline so it stands out from card

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

        # Data Stores
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
        
        # Bidding Phase Variable Tracking
        self.latest_bid_action = None

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

    def get_user_bidding_choice(self, current_bid) -> str:
        """
        Enters a blocking game loop that keeps rendering until the user clicks 
        either the Bid or Pass button. Returns the choice string.
        """
        self.latest_bid_action = None
        while self.latest_bid_action is None:
            self.render(current_bid=current_bid)
        
        action = self.latest_bid_action
        self.latest_bid_action = None
        return action

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
                suit_lower = suit.upper()
                if suit_lower in player_hands[player]:
                    for card in player_hands[player][suit_lower]:
                        self.hands[player_name].append((suit_lower, card))

    def play_card(self, player, card_tuple):
        suit = str(card_tuple[0]).upper()
        rank = str(card_tuple[1]).upper()
        target_card = (suit, rank)

        if player in self.hands:
            if target_card in self.hands[player]:
                self.hands[player].remove(target_card)
            
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

    def display_bidding_panel(self, current_bid):
        """Creates a dual-button interactive console panel in the center area."""
        try:
            bid_int = int(current_bid)
            next_legal_bid = str(bid_int + 10) if bid_int >= 250 else "250"
        except (ValueError, TypeError):
            next_legal_bid = "250"

        cx, cy = self.screen_w // 2, self.screen_h // 2
        
        # Dimensions
        btn_w = int(180 * self.scale)
        btn_h = int(60 * self.scale)
        gap = int(20 * self.scale)
        
        # Positions: Pass on left, Bid on right
        pass_rect = pygame.Rect(cx - btn_w - gap // 2, cy - btn_h // 2, btn_w, btn_h)
        bid_rect = pygame.Rect(cx + gap // 2, cy - btn_h // 2, btn_w, btn_h)
        
        mouse_pos = pygame.mouse.get_pos()

        # --- Draw Pass Button ---
        pass_bg = HOVER_COLOR if pass_rect.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(self.screen, pass_bg, pass_rect, border_radius=10)
        pygame.draw.rect(self.screen, TEXT_BLACK, pass_rect, 2 if pass_bg == BUTTON_BG else 4, border_radius=10)
        
        pass_surf = self.font_main.render("PASS", True, TEXT_RED)
        pass_rect_center = pass_surf.get_rect(center=pass_rect.center)
        self.screen.blit(pass_surf, pass_rect_center)
        self.clickable_rects.append((pass_rect, "BID_ACTION:PASS"))

        # --- Draw Bid Button ---
        bid_bg = HOVER_COLOR if bid_rect.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(self.screen, bid_bg, bid_rect, border_radius=10)
        pygame.draw.rect(self.screen, TEXT_BLACK, bid_rect, 2 if bid_bg == BUTTON_BG else 4, border_radius=10)
        
        bid_surf = self.font_main.render(f"BID: {next_legal_bid}", True, TEXT_BLACK)
        bid_rect_center = bid_surf.get_rect(center=bid_rect.center)
        self.screen.blit(bid_surf, bid_rect_center)
        self.clickable_rects.append((bid_rect, f"BID_ACTION:{next_legal_bid}"))

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

    def _draw_scene(self, current_bid=None):
        self.screen.fill(BG_COLOR)
        self.clickable_rects = [] 
        self.draw_labels()
        self._draw_hand_horizontal('North', self.pad_large)
        self._draw_hand_horizontal('South', self.screen_h - self.card_h - self.pad_large)
        self._draw_hand_grid('West', is_left_side=True)
        self._draw_hand_grid('East', is_left_side=False)
        
        if current_bid is not None:
            self.display_bidding_panel(current_bid)
        else:
            self._draw_center_trick()
            
        pygame.display.flip()

    def render(self, current_bid=None):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.clear_table()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for rect, identity in self.clickable_rects:
                    if rect.collidepoint(mouse_pos):
                        if isinstance(identity, str) and identity.startswith("BID_ACTION:"):
                            self.latest_bid_action = identity.split(":")[1]
                        else:
                            self._pending_user_click = identity
                        break

        self._draw_scene(current_bid)
        self.clock.tick(30)