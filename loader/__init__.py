''' Creates and stores symbols '''
import os

RESERVED = 0
LETTER = 1
DIGIT = 2
SPACE = 3
EOL = 4
QUOTE = 5
DOT = 6
COMMENT = 7
SEMICOLON = 8
NEGATIVE = 9
OPERATOR = 10
UNDERLINE = 11

ALPHABET = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
OPERATORS = '+-/,()<>:=*[]'
DIGITS = '0123456789'

symbol_map = {' ': SPACE,
              '\t': SPACE,
              '\r': SPACE,
              '\n': EOL,
              '\'': QUOTE,
              '.': DOT,
              '{': COMMENT,
              ';': SEMICOLON,
              '-': NEGATIVE,
              '_': UNDERLINE}

# stores alphabet characters
for character in ALPHABET:
    symbol_map[character] = LETTER
    symbol_map[character.lower()] = LETTER

# stores operators
for operator in OPERATORS:
    symbol_map[operator] = OPERATOR

# stores digits
for digit in DIGITS:
    symbol_map[digit] = DIGIT
    symbol_map[int(digit)] = DIGIT

# stores keywords from the keywords file
with open(os.path.join(__name__, 'keywords.txt')) as keyword_file:
    for line in keyword_file.readlines():
        symbol = line.strip()
        symbol_map[symbol] = RESERVED