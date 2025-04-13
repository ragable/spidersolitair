import datetime as dt
SUITS = 'SHDC'
RANKS = "A23456789TJQK"
STANDARD_DECK = [rank + suit for rank in RANKS for suit in SUITS]
CARD_WIDTH = 80
CARD_HEIGHT = 120
CARD_SPACING_Y = 30
PILE_SPACING_X = 100
MARGIN = 20
HEXNUM = '0123456789ABCDEF'
FORWARD = 0      # used to indicate normal play
BACKTRACKING = 1 # used to indicate backtracking
NORMAL = 0 # used to indicate no empty columns
SINGLE = 1 # used to indicate single empty column
MULTI  = 2 # used to indicate > 1 empty columns
# NOTE: For COLNUM (column number)
# 0..J are legitimate column numbers
# (0..19) for moves.
# All actual moves are
# comprised of 3 characters - a
# souce column, a destination
# column and the number of cards
# go be moved. Deals and undo deals
# are one character,'L'.
# In the case of a backtrack a move
# is intepreted as the second character
# is the origin column and the first
# character is the destination, the
# third character is still the number
# of cards to be moved.
# When backtracking an 'L' becomes
# an undo deal.
COLNUM = '0123456789ABCDEFGHIJKL'
BASE_DATE = dt.datetime(2000,1,1)
# SPIDER_LEVEL is the maximum amount of levels
# allowed in a Spider move tree.
SPIDER_LEVEL = 3