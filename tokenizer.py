from lib2to3.pgen2 import token
from lib2to3.pgen2.token import SEMI
from token import PLUS
from loader import symbol_map, LETTER, RESERVED, SPACE, DIGIT, OPERATOR, EOL, \
                        QUOTE, DOT, SEMICOLON, COMMENT, COMMENT_TYPES, HYPHEN, PascalError

TOKEN_NAME_PREFIX = 'TK_'

TOKEN_CHARACTER = TOKEN_NAME_PREFIX + 'CHARACTER'
TOKEN_COMMENT = TOKEN_NAME_PREFIX + 'COMMENT'
TOKEN_DATA_TYPE_ARRAY = TOKEN_NAME_PREFIX + 'ARRAY'
TOKEN_DATA_TYPE_BOOL = TOKEN_NAME_PREFIX + 'BOOLEAN'
TOKEN_DATA_TYPE_CHAR = TOKEN_NAME_PREFIX + 'CHAR'
TOKEN_DATA_TYPE_INT = TOKEN_NAME_PREFIX + 'INTEGER'
TOKEN_DATA_TYPE_RANGE = TOKEN_NAME_PREFIX + 'RANGE'
TOKEN_DATA_TYPE_REAL = TOKEN_NAME_PREFIX + 'REAL'
TOKEN_DOT = TOKEN_NAME_PREFIX + 'DOT'
TOKEN_EOF = TOKEN_NAME_PREFIX + 'EOF'
TOKEN_ID = TOKEN_NAME_PREFIX + 'ID'
TOKEN_OPERATOR = TOKEN_NAME_PREFIX + 'OPERATOR'
TOKEN_OPERATOR_ASSIGNMENT = TOKEN_NAME_PREFIX + 'ASSIGNMENT'
TOKEN_OPERATOR_COLON = TOKEN_NAME_PREFIX + 'COLON'
TOKEN_OPERATOR_COMMA = TOKEN_NAME_PREFIX + 'COMMA'
TOKEN_OPERATOR_DIVISION = TOKEN_NAME_PREFIX + '/'
TOKEN_OPERATOR_EQUALITY = TOKEN_NAME_PREFIX + '='
TOKEN_OPERATOR_GTE = TOKEN_NAME_PREFIX + '>='
TOKEN_OPERATOR_LEFT_BRACKET = TOKEN_NAME_PREFIX + '['
TOKEN_OPERATOR_LEFT_CHEVRON = TOKEN_NAME_PREFIX + '<'
TOKEN_OPERATOR_LEFT_PAREN = TOKEN_NAME_PREFIX + 'LPAREN'
TOKEN_OPERATOR_LTE = TOKEN_NAME_PREFIX + '<='
TOKEN_OPERATOR_MINUS = TOKEN_NAME_PREFIX + '-'
TOKEN_OPERATOR_MULTIPLICATION = TOKEN_NAME_PREFIX + '*'
TOKEN_OPERATOR_NOT_EQUAL = TOKEN_NAME_PREFIX + '<>'
TOKEN_OPERATOR_PLUS = TOKEN_NAME_PREFIX + '+'
TOKEN_OPERATOR_RIGHT_BRACKET = TOKEN_NAME_PREFIX + ']'
TOKEN_OPERATOR_RIGHT_CHEVRON = TOKEN_NAME_PREFIX + '>'
TOKEN_OPERATOR_RIGHT_PAREN = TOKEN_NAME_PREFIX + 'RPAREN'
TOKEN_REAL_LIT = TOKEN_NAME_PREFIX + 'REAL_LIT'
TOKEN_RESERVED = TOKEN_NAME_PREFIX + 'RESERVED'
TOKEN_SEMICOLON = TOKEN_NAME_PREFIX + 'SEMICOLON'
TOKEN_STRING_LIT = TOKEN_NAME_PREFIX + 'STR_LIT'

operators_classifications = {
    ':=': TOKEN_OPERATOR_ASSIGNMENT,
    '(': TOKEN_OPERATOR_LEFT_PAREN,
    ')': TOKEN_OPERATOR_RIGHT_PAREN,
    '+': TOKEN_OPERATOR_PLUS,
    '-': TOKEN_OPERATOR_MINUS,
    '/': TOKEN_OPERATOR_DIVISION,
    '<': TOKEN_OPERATOR_LEFT_CHEVRON,
    '<=': TOKEN_OPERATOR_LTE,
    '>': TOKEN_OPERATOR_RIGHT_CHEVRON,
    '>=': TOKEN_OPERATOR_GTE,
    ',': TOKEN_OPERATOR_COMMA,
    ':': TOKEN_OPERATOR_COLON,
    '*': TOKEN_OPERATOR_MULTIPLICATION,
    '=': TOKEN_OPERATOR_EQUALITY,
    '<>': TOKEN_OPERATOR_NOT_EQUAL,
    '[': TOKEN_OPERATOR_LEFT_BRACKET,
    ']': TOKEN_OPERATOR_RIGHT_BRACKET
}

reserved_tokens = {'integer': TOKEN_DATA_TYPE_INT,
                   'real': TOKEN_DATA_TYPE_REAL,
                   'char': TOKEN_DATA_TYPE_CHAR,
                   'boolean': TOKEN_DATA_TYPE_BOOL}

strings = set()

class Token(object):
    def __init__(self, value, type_of, row, col) -> None:
        self.value = value
        self.type_of = type_of
        self.row = row
        self.col = col
    
    def __unicode__(self) -> str:
        return f'{self.value}, {self.type_of}, {self.row}, {self.col}'

def get_token_name(suffix):
    return TOKEN_NAME_PREFIX + suffix.upper()

def letter(text):
    suffix = ''
    for char in text:
        char_val = symbol_map.get(char, None)

        if char_val == LETTER or char == DIGIT:
            suffix += char
        else:
            break
    
    return suffix

def quote(text, row, col):
    suffix = ''
    first_quote = False
    for char in text:
        char_val = symbol_map.get(char, None)

        if char_val == QUOTE and first_quote:
            suffix += char
            strings.add(suffix.replace('\'', ''))
            break
        elif char_val == QUOTE and not first_quote:
            suffix += char
            first_quote = True
        elif char == '\n':
            suffix += char
            row += 1
        elif char_val == EOL:
            suffix += char
            col += len(suffix)
            raise PascalError(f'Invalid string at {row}, {col}')

    return suffix

def comment(text):
    idx = 0
    word = ''

    while idx < len(text):
        char = text[idx]
        if char == '}':
            return word + char
        elif char == '*' and text[idx+1] == ')':
            return word + char + text[idx+1]
        else:
            word += char
            idx += 1

def inline_comment(text):
    idx = 0
    word = ''
    
    while idx < len(text):
        char = text[idx]
        idx += 1

        if char == '\n':
            return word
        else:
            word += char

def digit(text):
    suffix = ''
    digit_seen = False
    idx = 0

    while idx < len(text):
        char = text[idx]
        char_val = symbol_map.get(char, None)

        if char_val == DIGIT:
            suffix += char
            digit_seen = True
            idx += 1
        elif char_val == HYPHEN:
            suffix += char
            idx += 1
        elif char_val == DOT and digit_seen:
            if suffix.__contains__('.') and symbol_map.get(text[idx+1]) == DOT:
                suffix += char + text[idx + 1]
                idx += 2
            else:
                suffix += char
                idx += 1
        elif char_val == DOT and not digit_seen:
            raise PascalError('Invalid number')
        elif char.lower() == 'e':
            if text[idx+1] == HYPHEN or text[idx+1] == PLUS:
                suffix += char + text[idx+1]
                idx += 2
            elif symbol_map.get(text[idx+1]) == DIGIT:
                suffix += char
                idx += 1
            else:
                raise PascalError('Invalid number')
        else:
            break
    
    return suffix

def operator(text):
    idx = 0

    if text[idx] == '(' and text[idx+1] == '*':
        return comment(text[idx:])
    elif text[idx] == ':' and text[idx+1] == '=':
        return text[idx] + text[idx+1]
    elif text[idx] == '<' and (text[idx+1] == '=' or text[idx+1] == '>'):
        return text[idx] + text[idx+1]
    elif text[idx] == '>' and text[idx+1] == '=':
        return text[idx] + text[idx+1]
    elif text[idx] == '/' and text[idx+1] == '/':
        return inline_comment(text[idx:])
    else:
        return text[idx]

def get_token(file):
    row, col, idx = 1, 1, 0
    tokens = []
    text = file.content

    while idx < len(text):
        char_val = symbol_map.get(text[idx])
        if char_val == LETTER:
            word = letter(text[idx:])
            idx += len(word)
            col += len(word)

            if word in reserved_tokens:
                tokens.append(Token(word, get_token_name(word), row, col))
            else:
                tokens.append(Token(word, TOKEN_ID, row, col))
        elif char_val == DIGIT:
            word = digit(text[idx:])
            idx += len(word)
            col += len(word)
            
            if word.count('.') == 2:
                tokens.append(Token(word, TOKEN_DATA_TYPE_RANGE, row, col))
            elif word.count('.') == 1:
                tokens.append(Token(word, TOKEN_REAL_LIT, row, col))
            else:
                tokens.append(Token(word, TOKEN_DATA_TYPE_INT, row, col))
        elif char_val == SPACE:
            col += 1
            idx += 1
        elif char_val == OPERATOR:
            word = operator(text[idx:])
            idx += len(word)
            col += len(word)

            if word[:2] in COMMENT_TYPES:
                tokens.append(Token(word, TOKEN_COMMENT, row, col))
            else:
                tokens.append(Token(word, operators_classifications[word], row, col))
        elif char_val == QUOTE:
            word = quote(text[idx:], row, col)
            idx += len(word)

            if len(word) == 3:
                tokens.append(Token(str(word.replace("'", '')), TOKEN_CHARACTER, row, col))
            else:
                tokens.append(Token(word, TOKEN_STRING_LIT, row, col))
        elif char_val == EOL:
            idx += 1
            row += 1
            col = 1
        elif char_val == DOT:
            idx += 1
            col += 1
            tokens.append(Token('.', TOKEN_DOT, row, col))
        elif char_val == SEMICOLON:
            idx += 1
            col += 1
            tokens.append(Token(';', TOKEN_SEMICOLON, row, col))
        elif char_val == COMMENT:
            word = comment(text[idx:])
            idx += len(word)
            tokens.append(Token(word, TOKEN_COMMENT, row, col))        
            col += len(word)
        else:
            raise PascalError(f'Unknown token at {row}, {col}: {text[idx]}')
    
    tokens.append(Token('EOF', TOKEN_EOF, row, col))
    return tokens


for key, value in symbol_map.items():
    if value == RESERVED:
        reserved_tokens[key.upper()] = TOKEN_RESERVED
        reserved_tokens[key.lower()] = TOKEN_RESERVED