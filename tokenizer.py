from loader import *
from loader.lalg_error import LalgError

TOKEN_NAME_PREFIX = 'TK_'

TOKEN_CHARACTER = TOKEN_NAME_PREFIX + 'CHARACTER'
TOKEN_COMMENT = TOKEN_NAME_PREFIX + 'COMMENT'
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
TOKEN_DATA_TYPE_BOOL = TOKEN_NAME_PREFIX + 'BOOLEAN'
TOKEN_DATA_TYPE_CHAR = TOKEN_NAME_PREFIX + 'CHAR'

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
                   'real': TOKEN_DATA_TYPE_REAL}

class Token(object):
    def __init__(self, value_of, type_of, row, column) -> None:
        self.value_of = value_of
        self.type_of = type_of
        self.row = row
        self.column = column

    def __unicode__(self) -> str:
        return f"<{self.value_of}, {self.type_of}, {self.row}, {self.column}>"

    def __repr__(self):
        return f"<{self.value_of}, {self.type_of}, {self.row}, {self.column}>"

def token_name(suffix):
    return TOKEN_NAME_PREFIX + suffix.upper()

def case_letter(text):
    suffix = ''
    for char in text:
        char_val = symbol_map.get(char, None)

        if char_val == LETTER or char_val == DIGIT or char_val == UNDERLINE:
            suffix += char
        else:
            break
    
    return suffix


def case_comment(text):
    index = 0
    word = ''

    while index < len(text):
        char = text[index]

        if char == '}':
            return word + char
        else:
            word += char
            index += 1

def case_digit(text):
    suffix = ''
    digit_seen = False
    index = 0

    while index < len(text):
        char = text[index]
        char_val = symbol_map.get(char, None)

        if char_val == DIGIT:
            suffix += char
            digit_seen = True
            index += 1
        elif char_val == '-':
            suffix += char
            index += 1
        elif char_val == DOT:
            if digit_seen:
                if suffix.__contains__('.') and symbol_map.get(text[index + 1]) is DOT:
                    suffix += char
                    suffix += text[index + 1]
                    index += 2
                else:
                    suffix += char
                    index += 1
            else:
                raise LalgError('Invalid literal.')
        elif char.lower() == 'e':
            if text[index + 1] == '-' or text[index + 1] == '+':
                suffix += char
                suffix += text[index + 1]
                index += 2
            elif symbol_map.get(text[index + 1]) is DIGIT:
                suffix += char
                index += 1
            else:
                raise LalgError('Invalid literal.')
        else:
            return suffix


def case_operator(text):
    index = 0

    if text[index] == ':' and text[index + 1] == '=':
        return text[index] + text[index + 1]
    elif text[index] == '<' and (text[index + 1] == '=' or text[index + 1] == '>'):
        return text[index] + text[index + 1]
    elif text[index] == '>' and text[index + 1] == '=':
        return text[index] + text[index + 1]
    else:
        return text[index]

def get_token(code):
    row, column, index = 1, 1, 0
    token_list = []

    while index < len(code.contents):
        symbol = symbol_map.get(code.contents[index])
        
        if symbol == LETTER:
            word = case_letter(code.contents[index:])
            index += len(word)
            if reserved_tokens.get(word) is None:
                token_list.append(Token(word, TOKEN_ID, row, column))
            else:
                token_list.append(Token(word, token_name(word), row, column))
            column += len(word)
        elif symbol == DIGIT:
            word = case_digit(code.contents[index:])
            index += len(word)
            #TODO tem que lidar com erro aqui, não?
            if word.count('.') == 1:
                token_list.append(Token(word, TOKEN_REAL_LIT, row, column))
            else:
                token_list.append(Token(word, TOKEN_DATA_TYPE_INT, row, column))
            column += len(word)
        elif symbol == SPACE:
            column += 1
            index += 1
        elif symbol == OPERATOR:
            word = case_operator(code.contents[index:])
            index += len(word)
            token_list.append(Token(word, operators_classifications[word], row, column))
            column += len(word)
        elif symbol == EOL:
            index += 1
            row += 1
            column = 1
        elif symbol == DOT:
            index += 1
            token_list.append(Token('.', TOKEN_DOT, row, column))
            column += 1
        elif symbol == SEMICOLON:
            index += 1
            token_list.append(Token(';', TOKEN_SEMICOLON, row, column))
            column += 1
        elif symbol == COMMENT:
            word = case_comment(code.contents[index:])
            index += len(word)
            token_list.append(Token(word, TOKEN_COMMENT, row, column))
            column += len(word)
        else:
            raise LalgError('Unknown symbol: %s (ln %i, col %i)' % (code.contents[index], row, column))
    token_list.append(Token('EOF', TOKEN_EOF, row, column))
    return token_list

for keyword, value in symbol_map.items():
    if value == RESERVED:
        reserved_tokens[keyword.lower()] = TOKEN_RESERVED
        reserved_tokens[keyword.upper()] = TOKEN_RESERVED