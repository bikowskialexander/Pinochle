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

# Premium Casino Color Palette
BG_COLOR = (24, 105, 48)         # Rich classic felt green
SHADOW_COLOR = (14, 56, 28)       # Deep table shading color for dropshadow depth
LABEL_BG = (16, 66, 32)          # Dark velvet tone for player HUD banners
CARD_COLOR = (255, 255, 255)
TEXT_BLACK = (25, 25, 25)       # High-contrast premium off-black
TEXT_RED = (200, 30, 35)         # Deeper card-stock crimson
MELD_COLOR = (212, 175, 55)      # Metallic gold leaf border
SELECTION_COLOR = (46, 204, 113)  # Vibrant emerald choice green
LEGAL_PLAY_COLOR = (241, 196, 15) # Warm amber play yellow
HOVER_COLOR = (220, 245, 220) 
BUTTON_BG = (245, 242, 235)      # Soft linen cream paper tone

# Bidding Highlight Profiles
BID_COLOR_PRIMARY = (241, 196, 15)   # Color Index 1: Active Gold Ring
BID_COLOR_SECONDARY = (52, 152, 219) # Color Index 2: Electric Blue Ring

# Sorting / Display Order
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
        self.team_scores = {'N/S': 0, 'E/W': 0}
        
        # State Management Repositories
        self.bidder_highlight = {}       
        self.translucent_players = set()  
        self.displayed_trump = None       
        
        self.player_names = {
            'North': 'Bot North', 'South': 'Bot South', 
            'East': 'Bot East', 'West': 'Bot West'
        }

        self.clickable_rects = [] 
        self._pending_user_click = None
        
        # Phase Variable Tracking
        self.latest_bid_action = None
        self.latest_trump_action = None
        self.passing_confirmed = False
        self.is_passing_phase = False
        self.is_trick_phase = False
        self.legal_trick_cards = set()
        self.chosen_trick_card = None

        # For user
        self.is_user = {'North':False, 'South':False, 'East':False, 'West':False}
        self.user_direction = None

    def _is_player_user(self, player_key) -> bool:
        if self.user_direction == player_key:
            return True
        if isinstance(self.user_direction, int):
            if index_to_Direction_name(self.user_direction) == player_key:
                return True
        if self.is_user.get(player_key) == True:
            return True
        if self.player_names.get(player_key) == 'user':
            return True
        return False

    def _get_active_user_key(self) -> str:
        for k in ['South', 'North', 'East', 'West']:
            if self._is_player_user(k):
                return k
        return 'South'

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
        self.latest_bid_action = None
        self._pending_user_click = None 
        
        while self.latest_bid_action is None:
            self.render(current_bid=current_bid)
        
        action = self.latest_bid_action
        self.latest_bid_action = None
        return action

    def get_user_trump_choice(self) -> str:
        self.latest_trump_action = None
        self._pending_user_click = None 
        
        while self.latest_trump_action is None:
            self.render(show_trump_panel=True)
            
        action = self.latest_trump_action
        self.latest_trump_action = None
        return action

    def get_user_passing_choice(self) -> list:
        self.green_highlights[self.user_direction] = set()
        self.passing_confirmed = False
        self.is_passing_phase = True
        self._pending_user_click = None

        while not self.passing_confirmed:
            self.render(show_passing_panel=True)

        self.is_passing_phase = False
        chosen_cards = [self.hands[self.user_direction][idx] for idx in self.green_highlights[self.user_direction]]
        self.green_highlights[self.user_direction] = set()
        return chosen_cards

    def get_user_trick_choice(self, legal_cards) -> tuple:
        if self.user_direction is None:
            return legal_cards[0] if legal_cards else None

        self.legal_trick_cards = {(str(suit).upper(), str(rank).upper()) for suit, rank in legal_cards}
        self.chosen_trick_card = None
        self.is_trick_phase = True
        self._pending_user_click = None

        while self.chosen_trick_card is None:
            self.render()

        self.is_trick_phase = False
        self.legal_trick_cards = set()
        return self.chosen_trick_card

    def display_winner(self, winner_text):
        """
        FORCE FREEZE LOOP: Freezes execution and locks down the table layout to blit
        a premium central victory panel until dismissed by any user click or keypress.
        """
        dismissed = False
        while not dismissed:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type in (pygame.MOUSEBUTTONDOWN, pygame.KEYDOWN):
                    dismissed = True
            
            self.screen.fill(BG_COLOR)
            self.draw_labels()
            self._draw_team_scoreboard()
            self._draw_hand_horizontal('North', self.pad_large)
            self._draw_hand_horizontal('South', self.screen_h - self.card_h - self.pad_large)
            self._draw_hand_grid('West', is_left_side=True)
            self._draw_hand_grid('East', is_left_side=False)
            if self.displayed_trump:
                self._draw_trump_indicator()
            else:
                self._draw_center_trick()
            
            cx, cy = self.screen_w // 2, self.screen_h // 2
            
            # FIX: Emojis and 'WINNER:' text prefix completely removed
            main_surf = self.font_main.render(str(winner_text).upper(), True, TEXT_BLACK)
            main_rect = main_surf.get_rect(center=(cx, cy))
            
            w = main_surf.get_width() + int(64 * self.scale)
            h = int(80 * self.scale)
            
            box_rect = pygame.Rect(cx - w // 2, cy - h // 2, w, h)
            shadow_rect = box_rect.move(int(5 * self.scale), int(5 * self.scale))
            
            pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=15)
            pygame.draw.rect(self.screen, BUTTON_BG, box_rect, border_radius=15)
            pygame.draw.rect(self.screen, MELD_COLOR, box_rect, int(3 * self.scale), border_radius=15)
            
            self.screen.blit(main_surf, main_rect)
            
            pygame.display.flip()
            self.clock.tick(30)

    def set_player_names(self, names_dict):
        for pos, name in names_dict.items():
            if pos in self.player_names:
                self.player_names[pos] = name

    def set_score(self, player, points):
        if player in self.scores:
            self.scores[player] = points

    def set_team_scores(self, ns_score, ew_score):
        self.team_scores['N/S'] = ns_score
        self.team_scores['E/W'] = ew_score

    def highlight_bidder(self, player, color_index=1):
        if player in self.hands:
            self.bidder_highlight[player] = color_index

    def remove_bidder_highlight(self, player):
        if player in self.bidder_highlight:
            del self.bidder_highlight[player]

    def set_score_translucent(self, player, translucent=True):
        if player in self.hands:
            if translucent:
                self.translucent_players.add(player)
            else:
                self.translucent_players.discard(player)

    def reset_score_transparency(self, player):
        self.translucent_players.discard(player)

    def set_displayed_trump(self, suit_name):
        if suit_name:
            self.displayed_trump = suit_name.upper()

    def clear_displayed_trump(self):
        self.displayed_trump = None

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

        if player in self.hands:
            for item in list(self.hands[player]):
                if str(item[0]).upper() == suit and str(item[1]).upper() == rank:
                    self.hands[player].remove(item)
                    break
            
            self.center_cards[player] = (suit, rank)
            
            check_lower = (suit.lower(), rank)
            if player in self.meld_highlights:
                self.meld_highlights[player].discard(check_lower)
            self.green_highlights[player] = set()
            
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
        suit = str(card_tuple[0]).upper()
        rank = str(card_tuple[1]).upper()
        if player in self.hands:
            for i, card in enumerate(self.hands[player]):
                if str(card[0]).upper() == suit and str(card[1]).upper() == rank:
                    if i not in self.green_highlights[player]:
                        self.green_highlights[player].add(i)
                        break

    def unhighlight_card(self, player, card_tuple):
        suit = str(card_tuple[0]).upper()
        rank = str(card_tuple[1]).upper()
        if player in self.hands:
            for i, card in enumerate(self.hands[player]):
                if str(card[0]).upper() == suit and str(card[1]).upper() == rank:
                    if i in self.green_highlights[player]:
                        self.green_highlights[player].remove(i)
                        break

    def clear_table(self):
        self.center_cards = {}

    def display_bidding_panel(self, current_bid):
        try:
            bid_int = int(current_bid)
            next_legal_bid = str(bid_int + 10) if bid_int >= 250 else "250"
        except (ValueError, TypeError):
            next_legal_bid = "250"

        cx, cy = self.screen_w // 2, self.screen_h // 2
        btn_w = int(180 * self.scale)
        btn_h = int(60 * self.scale)
        gap = int(20 * self.scale)
        
        pass_rect = pygame.Rect(cx - btn_w - gap // 2, cy - btn_h // 2, btn_w, btn_h)
        bid_rect = pygame.Rect(cx + gap // 2, cy - btn_h // 2, btn_w, btn_h)
        mouse_pos = pygame.mouse.get_pos()

        pass_shadow = pass_rect.move(int(4 * self.scale), int(4 * self.scale))
        pygame.draw.rect(self.screen, SHADOW_COLOR, pass_shadow, border_radius=10)
        pass_bg = HOVER_COLOR if pass_rect.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(self.screen, pass_bg, pass_rect, border_radius=10)
        pygame.draw.rect(self.screen, TEXT_BLACK, pass_rect, 2, border_radius=10)
        pass_surf = self.font_main.render("PASS", True, TEXT_RED)
        self.screen.blit(pass_surf, pass_surf.get_rect(center=pass_rect.center))
        self.clickable_rects.append((pass_rect, "BID_ACTION:PASS"))

        bid_shadow = bid_rect.move(int(4 * self.scale), int(4 * self.scale))
        pygame.draw.rect(self.screen, SHADOW_COLOR, bid_shadow, border_radius=10)
        bid_bg = HOVER_COLOR if bid_rect.collidepoint(mouse_pos) else BUTTON_BG
        pygame.draw.rect(self.screen, bid_bg, bid_rect, border_radius=10)
        pygame.draw.rect(self.screen, TEXT_BLACK, bid_rect, 2, border_radius=10)
        bid_surf = self.font_main.render(f"BID: {next_legal_bid}", True, TEXT_BLACK)
        self.screen.blit(bid_surf, bid_surf.get_rect(center=bid_rect.center))
        self.clickable_rects.append((bid_rect, f"BID_ACTION:{next_legal_bid}"))

    def display_trump_panel(self):
        cx, cy = self.screen_w // 2, self.screen_h // 2
        
        btn_w = int(110 * self.scale)
        btn_h = int(65 * self.scale)
        gap = int(15 * self.scale)
        
        total_w = (4 * btn_w) + (3 * gap)
        start_x = cx - total_w // 2
        y_pos = cy - btn_h // 2
        
        mouse_pos = pygame.mouse.get_pos()
        suits_ordered = ['SPADES', 'HEARTS', 'CLUBS', 'DIAMONDS']

        for i, suit_name in enumerate(suits_ordered):
            x_pos = start_x + i * (btn_w + gap)
            rect = pygame.Rect(x_pos, y_pos, btn_w, btn_h)
            
            shadow_rect = rect.move(int(4 * self.scale), int(4 * self.scale))
            pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=10)
            
            bg_color = HOVER_COLOR if rect.collidepoint(mouse_pos) else BUTTON_BG
            pygame.draw.rect(self.screen, bg_color, rect, border_radius=10)
            pygame.draw.rect(self.screen, TEXT_BLACK, rect, 2, border_radius=10)
            
            suit_lower = suit_name.lower()
            symbol = SUIT_SYMBOLS.get(suit_lower, '')
            color = SUIT_COLORS.get(suit_lower, TEXT_BLACK)
            
            label_surf = self.font_main.render(f"{symbol} {suit_name[:3]}", True, color)
            self.screen.blit(label_surf, label_surf.get_rect(center=rect.center))
            
            self.clickable_rects.append((rect, f"TRUMP_ACTION:{suit_name}"))

    def display_passing_panel(self):
        cx, cy = self.screen_w // 2, self.screen_h // 2
        selected_count = len(self.green_highlights[self.user_direction])
        
        guide_text = f"Select 4 Cards to Pass ({selected_count}/4)"
        guide_surf = self.font_main.render(guide_text, True, CARD_COLOR)
        guide_rect = guide_surf.get_rect(center=(cx, cy - int(50 * self.scale)))
        self.screen.blit(guide_surf, guide_rect)
        
        if selected_count == 4:
            btn_w = int(220 * self.scale)
            btn_h = int(60 * self.scale)
            button_rect = pygame.Rect(cx - btn_w // 2, cy - btn_h // 2 + int(20 * self.scale), btn_w, h=int(60 * self.scale))
            
            shadow_rect = button_rect.move(int(4 * self.scale), int(4 * self.scale))
            pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=10)
            
            mouse_pos = pygame.mouse.get_pos()
            bg_color = HOVER_COLOR if button_rect.collidepoint(mouse_pos) else BUTTON_BG
            pygame.draw.rect(self.screen, bg_color, button_rect, border_radius=10)
            pygame.draw.rect(self.screen, TEXT_BLACK, button_rect, 2, border_radius=10)
            
            label_surf = self.font_main.render("CONFIRM PASS", True, TEXT_BLACK)
            self.screen.blit(label_surf, label_surf.get_rect(center=button_rect.center))
            
            self.clickable_rects.append((button_rect, "PASS_ACTION:CONFIRM"))

    # --- DRAWING LOGIC ---

    def _draw_card(self, x, y, rank, suit, border_color=(0, 0, 0), border_thickness=2, hidden=False):
        suit = suit.lower()
        card_rect = pygame.Rect(x, y, self.card_w, self.card_h)
        
        shadow_rect = card_rect.move(int(3 * self.scale), int(3 * self.scale))
        pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=5)
        
        pygame.draw.rect(self.screen, CARD_COLOR, card_rect, border_radius=5)
        
        if border_thickness > 2:
            outline_rect = card_rect.inflate(border_thickness - 2, border_thickness - 2)
            pygame.draw.rect(self.screen, border_color, outline_rect, border_thickness, border_radius=5)
        else:
            pygame.draw.rect(self.screen, border_color, card_rect, border_thickness, border_radius=5)

        if hidden:
            back_color = (220, 75, 80) 
            inner_rect = card_rect.inflate(-int(8 * self.scale), -int(8 * self.scale))
            pygame.draw.rect(self.screen, back_color, inner_rect, border_radius=3)
            
            line_rect = inner_rect.inflate(-int(6 * self.scale), -int(6 * self.scale))
            pygame.draw.rect(self.screen, (255, 255, 240), line_rect, 1, border_radius=2)
            return card_rect

        color = SUIT_COLORS.get(suit, (0,0,0))
        symbol = SUIT_SYMBOLS.get(suit, '?')
        
        rank_surf = self.font_main.render(str(rank), True, color)
        offset_x = int(5 * self.scale)
        offset_y_rank = int(2 * self.scale)
        self.screen.blit(rank_surf, (x + offset_x, y + offset_y_rank))

        suit_surf = self.font_suit.render(symbol, True, color)
        offset_y_suit = int(28 * self.scale)
        self.screen.blit(suit_surf, (x + offset_x, y + offset_y_suit))
        
        return card_rect

    def _get_border_style(self, player, idx, card_tuple):
        if idx in self.green_highlights[player]: 
            return SELECTION_COLOR, 5
            
        suit = str(card_tuple[0]).upper()
        rank = str(card_tuple[1]).upper()
        check_tuple = (suit, rank)
        check_tuple_lower = (suit.lower(), rank)

        if self.is_trick_phase and player == self.user_direction:
            if check_tuple in self.legal_trick_cards or check_tuple_lower in self.legal_trick_cards:
                return LEGAL_PLAY_COLOR, 5

        if check_tuple in self.meld_highlights[player] or check_tuple_lower in self.meld_highlights[player]: 
            return MELD_COLOR, 5
        return (0, 0, 0), 2

    def _draw_hand_horizontal(self, player_key, start_y):
        cards = self.hands[player_key]
        if not cards: return
        
        total_width = (len(cards) * (self.card_w + self.margin)) - self.margin
        start_x = (self.screen_w - total_width) // 2

        is_user = (self.user_direction is not None and player_key == self.user_direction)
        hidden = not is_user

        for i, (suit, rank) in enumerate(cards):
            x = start_x + i * (self.card_w + self.margin)
            color, thick = self._get_border_style(player_key, i, (suit, rank))
            
            card_y = start_y
            if color == SELECTION_COLOR:
                card_y -= int(15 * self.scale)

            mouse_pos = pygame.mouse.get_pos()
            rect = pygame.Rect(x, card_y, self.card_w, self.card_h)
            
            if is_user and rect.collidepoint(mouse_pos):
                if color != SELECTION_COLOR and color != LEGAL_PLAY_COLOR:
                    color = HOVER_COLOR
                    thick = 4

            card_rect = self._draw_card(x, card_y, rank, suit, color, thick, hidden=hidden)
            
            if is_user:
                self.clickable_rects.append((card_rect, (player_key, i)))

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

        is_user = (self.user_direction is not None and player_key == self.user_direction)
        hidden = not is_user

        for i, (suit, rank) in enumerate(cards):
            row = i // cols
            col = i % cols
            x = start_x + col * (self.card_w + self.margin)
            y = start_y + row * (self.card_h + self.margin)
            color, thick = self._get_border_style(player_key, i, (suit, rank))
            
            card_x = x
            if color == SELECTION_COLOR:
                card_x += int(15 * self.scale) if not is_left_side else -int(15 * self.scale)

            mouse_pos = pygame.mouse.get_pos()
            rect = pygame.Rect(card_x, y, self.card_w, self.card_h)
            
            # FIX: Extraneous comments and stray code lines scrubbed completely
            if is_user and rect.collidepoint(mouse_pos):
                if color != SELECTION_COLOR and color != LEGAL_PLAY_COLOR:
                    color = HOVER_COLOR
                    thick = 4

            card_rect = self._draw_card(card_x, y, rank, suit, color, thick, hidden=hidden)
            
            if is_user:
                self.clickable_rects.append((card_rect, (player_key, i)))

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

    def _draw_trump_indicator(self):
        cx, cy = self.screen_w // 2, self.screen_h // 2
        suit_lower = self.displayed_trump.lower()
        symbol = SUIT_SYMBOLS.get(suit_lower, '')
        color = SUIT_COLORS.get(suit_lower, TEXT_BLACK)
        
        text_surf = self.font_main.render(f"{symbol} {self.displayed_trump}", True, color)
        text_rect = text_surf.get_rect(center=(cx, cy))
        
        badge_rect = text_rect.inflate(int(20 * self.scale), int(10 * self.scale))
        shadow_rect = badge_rect.move(int(3 * self.scale), int(3 * self.scale))
        
        pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=8)
        pygame.draw.rect(self.screen, BUTTON_BG, badge_rect, border_radius=8)
        pygame.draw.rect(self.screen, TEXT_BLACK, badge_rect, 1, border_radius=8)
        self.screen.blit(text_surf, text_rect)

    def _draw_team_scoreboard(self):
        ns_text = f"Team N/S: {self.team_scores['N/S']}"
        ew_text = f"Team E/W: {self.team_scores['E/W']}"
        
        ns_surf = self.font_main.render(ns_text, True, (255, 255, 255))
        ew_surf = self.font_main.render(ew_text, True, (255, 255, 255))
        
        max_w = max(ns_surf.get_width(), ew_surf.get_width()) + int(24 * self.scale)
        box_h = int(75 * self.scale)
        
        box_rect = pygame.Rect(self.pad_small, self.pad_small, max_w, box_h)
        shadow_rect = box_rect.move(int(3 * self.scale), int(3 * self.scale))
        
        pygame.draw.rect(self.screen, SHADOW_COLOR, shadow_rect, border_radius=8)
        pygame.draw.rect(self.screen, LABEL_BG, box_rect, border_radius=8)
        pygame.draw.rect(self.screen, MELD_COLOR, box_rect, 1, border_radius=8) 
        
        self.screen.blit(ns_surf, (box_rect.x + int(12 * self.scale), box_rect.y + int(10 * self.scale)))
        self.screen.blit(ew_surf, (box_rect.x + int(12 * self.scale), box_rect.y + int(40 * self.scale)))

    def _render_hud_banner(self, text, base_center, rotation=0, player_key=None):
        text_surf = self.font_main.render(text, True, (255, 255, 255))
        text_rect = text_surf.get_rect()
        
        w = text_rect.width + int(24 * self.scale)
        h = text_rect.height + int(10 * self.scale)
        
        temp_surface = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(temp_surface, LABEL_BG, (0, 0, w, h), border_radius=8)
        
        if player_key in self.bidder_highlight:
            idx = self.bidder_highlight[player_key]
            ring_color = BID_COLOR_PRIMARY if idx == 1 else BID_COLOR_SECONDARY
            pygame.draw.rect(temp_surface, ring_color, (0, 0, w, h), int(3 * self.scale), border_radius=8)
            
        text_rect.center = (w // 2, h // 2)
        temp_surface.blit(text_surf, text_rect)
        
        if player_key in self.translucent_players:
            temp_surface.set_alpha(100) 
            
        if rotation != 0:
            temp_surface = pygame.transform.rotate(temp_surface, rotation)
            
        final_rect = temp_surface.get_rect(center=base_center)
        self.screen.blit(temp_surface, final_rect)

    def draw_labels(self):
        self._render_hud_banner(
            f"{self.player_names['North']}: {self.scores['North']}", 
            (self.screen_w // 2, self.pad_small), player_key='North'
        )
        self._render_hud_banner(
            f"{self.player_names['South']}: {self.scores['South']}", 
            (self.screen_w // 2, self.screen_h - self.pad_small), player_key='South'
        )

        side_margin_center = self.pad_large // 2 
        
        self._render_hud_banner(
            f"{self.player_names['West']}: {self.scores['West']}", 
            (side_margin_center, self.screen_h // 2), rotation=90, player_key='West'
        )
        self._render_hud_banner(
            f"{self.player_names['East']}: {self.scores['East']}", 
            (self.screen_w - side_margin_center, self.screen_h // 2), rotation=-90, player_key='East'
        )

    def _draw_scene(self, current_bid=None, show_trump_panel=False, show_passing_panel=False):
        self.screen.fill(BG_COLOR)
        self.clickable_rects = [] 
        self.draw_labels()
        self._draw_team_scoreboard()
        self._draw_hand_horizontal('North', self.pad_large)
        self._draw_hand_horizontal('South', self.screen_h - self.card_h - self.pad_large)
        self._draw_hand_grid('West', is_left_side=True)
        self._draw_hand_grid('East', is_left_side=False)
        
        if show_passing_panel:
            self.display_passing_panel()
        elif show_trump_panel:
            self.display_trump_panel()
        elif current_bid is not None:
            self.display_bidding_panel(current_bid)
        else:
            if self.displayed_trump:
                self._draw_trump_indicator()
            self._draw_center_trick()
            
        pygame.display.flip()

    def render(self, current_bid=None, show_trump_panel=False, show_passing_panel=False):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit(); sys.exit()
            
            if event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE:
                self.clear_table()
            
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                for rect, identity in self.clickable_rects:
                    if rect.collidepoint(mouse_pos):
                        if isinstance(identity, str):
                            if identity.startswith("BID_ACTION:"):
                                self.latest_bid_action = identity.split(":")[1]
                            elif identity.startswith("TRUMP_ACTION:"):
                                self.latest_trump_action = identity.split(":")[1]
                            elif identity.startswith("PASS_ACTION:"):
                                self.passing_confirmed = True
                        else:
                            seat_key, card_index = identity
                            suit_str, rank_str = self.hands[seat_key][card_index]
                            
                            normalized_card = (suit_str, rank_str)
                            match_key = (str(suit_str).upper(), str(rank_str).upper())

                            if self.is_passing_phase:
                                print("Passing")
                                if card_index in self.green_highlights[seat_key]:
                                    self.green_highlights[seat_key].remove(card_index)
                                else:
                                    if len(self.green_highlights[seat_key]) < 4:
                                        self.green_highlights[seat_key].add(card_index)
                            elif self.is_trick_phase:
                                if seat_key == self.user_direction and match_key in self.legal_trick_cards:
                                    self.chosen_trick_card = normalized_card
                            else:
                                self._pending_user_click = normalized_card
                        break

        self._draw_scene(current_bid, show_trump_panel, show_passing_panel)
        self.clock.tick(30)