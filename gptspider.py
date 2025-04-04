import pygame
import sys
import os
import random
import zlib
RANKS = 'KQJT98765432A'
SUITS = 'SHDC'
STANDARD_DECK = [rank + suit for rank in RANKS for suit in SUITS]

# --- Card Logic ---
class Card:
    def __init__(self, rank, suit, face_up=False):
        self.rank = rank
        self.suit = suit
        self.face_up = face_up

    def flip(self):
        self.face_up = not self.face_up

    def get_id(self):
        return self.rank + self.suit

    def rank_value(self):
        return RANKS.index(self.rank)


class CardSprite(pygame.sprite.Sprite):
    def __init__(self, card, image_dir, pos=(0, 0), card_size=(80, 120)):
        super().__init__()
        self.card = card
        self.image_dir = image_dir
        self.card_size = card_size
        self.front_image = self.load_image(card.get_id())
        self.back_image = self.load_image("back-side")
        self.image = self.back_image if not self.card.face_up else self.front_image
        self.rect = self.image.get_rect(topleft=pos)
        self.dragging = False
        self.original_pos = pos

    def load_image(self, name):
        path = os.path.join(self.image_dir, f"{name}.png")
        img = pygame.image.load(path).convert_alpha()
        img = pygame.transform.smoothscale(img, self.card_size)
        return img

    def update(self):
        self.image = self.back_image if not self.card.face_up else self.front_image


# --- Create 2 Decks (Full 4-Suit Spider) ---
def create_double_deck(image_dir, card_size, name = None):

    if name == None:
        deck = []
        for suit in SUITS:
            for rank in RANKS:
                for _ in range(2):
                    card = Card(rank, suit)
                    sprite = CardSprite(card, image_dir, card_size=card_size)
                    deck.append(sprite)

        random.shuffle(deck)
        savedeck = []
        for crd in deck:
            savedeck.append(crd.card.get_id())
        ba = bytearray([STANDARD_DECK.index(card_) for card_ in savedeck])
        crc = zlib.crc32(ba)
        fn = 'decks/' + hex(crc)[2:] + '.txt'
        with open(fn, 'w') as f1:
            f1.write(str(savedeck))
    else:
        dfname = 'decks/' + name + '.txt'
        f = open(dfname,'r')
        deckfile = eval(f.read())
        deck = []
        for cardname in deckfile:
            for _ in range(2):
                card = Card(cardname[0],cardname[1])
                sprite = CardSprite(card, image_dir, card_size=card_size)
                deck.append(sprite)

    return deck


# --- Setup Initial Spider Layout ---
def setup_spider_tableau(deck):
    piles = [[] for _ in range(10)]
    index = 0
    for i in range(10):
        num_cards = 6 if i < 4 else 5
        for j in range(num_cards):
            card = deck[index]
            card.rect.topleft = (50 + i * 90, 50 + j * 30)
            card.original_pos = card.rect.topleft
            card.card.face_up = (j == num_cards - 1)
            card.update()
            piles[i].append(card)
            index += 1
    stock = deck[index:]
    return piles, stock


def draw_stock_and_buttons(screen, stock_pile, card_size):
    if stock_pile:
        stock_back = pygame.transform.smoothscale(pygame.image.load(os.path.join(image_dir, "back-side.png")).convert_alpha(), card_size)
        screen.blit(stock_back, (1000, 50))
        pygame.draw.rect(screen, (255, 255, 255), (1000, 50, card_size[0], card_size[1]), 2)

    pygame.draw.rect(screen, (200, 200, 200), (1000, 200, 100, 40))
    font = pygame.font.SysFont(None, 24)
    text = font.render("Redeal", True, (0, 0, 0))
    screen.blit(text, (1020, 210))

    for i in range(8):
        x = 800 + i * 35
        pygame.draw.rect(screen, (255, 255, 255), (x, 600, 30, 45), 2)


# --- Pygame Setup ---
pygame.init()
screen = pygame.display.set_mode((1200, 700))
pygame.display.set_caption("Spider Solitaire - Initial Deal")
clock = pygame.time.Clock()

image_dir = "img/cards/"
card_size = (80, 120)

full_deck = create_double_deck(image_dir, card_size)
tableau_piles, stock_pile = setup_spider_tableau(full_deck)
all_sprites = pygame.sprite.LayeredUpdates([card for pile in tableau_piles for card in pile])

selected_card = None
selected_pile = None
mouse_offset = (0, 0)

# --- Game Loop ---
running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

        elif event.type == pygame.MOUSEBUTTONDOWN:
            x, y = event.pos
            if 1000 <= x <= 1100 and 200 <= y <= 240:
                full_deck = create_double_deck(image_dir, card_size)
                tableau_piles, stock_pile = setup_spider_tableau(full_deck)
                all_sprites = pygame.sprite.LayeredUpdates([card for pile in tableau_piles for card in pile])

            elif 1000 <= x <= 1000 + card_size[0] and 50 <= y <= 50 + card_size[1]:
                print("Stock clicked - deal logic to be implemented")

            else:
                for pile in tableau_piles:
                    if pile:
                        top_card = pile[-1]
                        if top_card.rect.collidepoint(event.pos):
                            if not top_card.card.face_up:
                                top_card.card.flip()
                                top_card.update()
                            else:
                                selected_card = top_card
                                selected_pile = pile
                                mouse_offset = (event.pos[0] - top_card.rect.x, event.pos[1] - top_card.rect.y)
                                all_sprites.move_to_front(selected_card)
                                break

        elif event.type == pygame.MOUSEBUTTONUP:
            if selected_card:
                dropped = False
                for i, pile in enumerate(tableau_piles):
                    if pile:
                        last_card = pile[-1]
                        if last_card.rect.collidepoint(event.pos):
                            src_val = selected_card.card.rank_value()
                            dst_val = last_card.card.rank_value()
                            if src_val == dst_val + 1:
                                new_x = 50 + i * 90
                                new_y = 50 + len(pile) * 30
                                selected_card.rect.topleft = (new_x, new_y)
                                selected_card.original_pos = selected_card.rect.topleft
                                pile.append(selected_card)
                                if selected_pile and selected_card in selected_pile:
                                    selected_pile.remove(selected_card)
                                all_sprites.move_to_front(selected_card)
                                dropped = True
                                break
                if not dropped:
                    selected_card.rect.topleft = selected_card.original_pos
                selected_card.dragging = False
                selected_card = None
                selected_pile = None

        elif event.type == pygame.MOUSEMOTION:
            if selected_card:
                selected_card.rect.topleft = (event.pos[0] - mouse_offset[0], event.pos[1] - mouse_offset[1])
                selected_card.dragging = True

    screen.fill((34, 139, 34))
    all_sprites.draw(screen)
    draw_stock_and_buttons(screen, stock_pile, card_size)
    pygame.display.flip()
    clock.tick(60)

pygame.quit()
sys.exit()
