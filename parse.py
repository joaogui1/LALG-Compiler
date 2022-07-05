from loader import PascalError
import loader.symbol_tables as symbol_tables
import tokenizer
from constants import *
import sys, threading
sys.setrecursionlimit(10**7) # max depth of recursion
threading.stack_size(2**27)  # new thread will get stack of such size

class Parser(object):
    def __init__(self, tokens, verbose=False) -> None:
        self.tokens = tokens
        self.curr_token = None
        self.ip = 0
        self.dp = 0
        self.symbols = []
        self.bytes = bytearray(5000)
        self.verbose = verbose
    
    def find_name_in_symbol_table(self, name):
        for symbol in self.symbols:
            if symbol.name == name:
                return symbol
        
        return None
    
    def match(self, type_of):
        # print(type_of, self.curr_token.type_of)
        if self.curr_token.type_of == type_of:
            if self.verbose:
                print(f'Matched: {type_of}')
            
            if len(self.tokens) > 0:
                self.curr_token = self.tokens.pop(0)
            else:
                print('retornou')
                return
        else:
            raise PascalError(f'Token mismatch at {self.curr_token.row} {self.curr_token.col}, expected {str(type)} got {str(self.curr_token)}')
    
    def generate_op_code(self, op_code) -> None:
        self.bytes[self.ip] = op_code
        self.ip += 1
    
    def generate_address(self, target) -> None:
        for byte in byte_packer(target):
            self.bytes[self.ip] = byte
            self.ip += 1
        
    def parse(self):
        self.curr_token = self.tokens.pop(0)
        self.match('TK_PROGRAM')
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_SEMICOLON)

        if self.curr_token.type_of == 'TK_VAR':
            self.variable_declaration()
        elif self.curr_token.type_of == 'TK_PROCEDURE':
            while self.curr_token.type_of == 'TK_PROCEDURE':
                self.procedure_declaration()
            self.begin()
        else:
            self.begin()
        
        return self.bytes
    
    def begin(self):
        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_DOT)
        self.match(tokenizer.TOKEN_EOF)
        self.generate_op_code(OPCODE.HALT)
    
    def statementes(self):
        while self.curr_token.type_of != 'TK_END':
            type = self.curr_token.type_of
            
            if type == 'TK_WRITELN':
                self.write_line_statement()
            elif type == tokenizer.TOKEN_ID:
                self.assignment_statement()
            elif type == 'TK_WHILE':
                self.while_statement()
            elif type == 'TK_REPEAT':
                self.repeat_statement()
            elif type == 'TK_IF':
                self.if_statement()
            elif type == 'TK_FOR':
                self.for_statement()
            elif type == 'TK_CASE':
                self.case_statement()
            elif type == tokenizer.TOKEN_SEMICOLON:
                self.match(tokenizer.TOKEN_SEMICOLON)
            elif type == tokenizer.TOKEN_COMMENT:
                self.match(tokenizer.TOKEN_COMMENT)
            else:
                if self.verbose:
                    print(f'Parser: statements() can\'t match {self.curr_token}')
                return

    def find_name_or_error(self):
        symbol = self.find_name_in_symbol_table(self.curr_token.value)
        if symbol is None:
            raise PascalError(f'Var {self.curr_token.value} is not declared at {self.curr_token.row} {self.curr_token.col}')
        else:
            return symbol

    def assignment_statement(self):
        symbol = self.find_name_or_error()
        lhs_type = symbol.data_type
        self.match(tokenizer.TOKEN_ID)

        if self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_LEFT_BRACKET:
            self.array_assignment(symbol)
            return
        
        self.match(tokenizer.TOKEN_OPERATOR_ASSIGNMENT)
        rhs_type = self.e()

        if rhs_type == tokenizer.TOKEN_CHARACTER:
            self.generate_op_code(OPCODE.POP_CHAR)
            self.generate_address(symbol.dp)
        elif lhs_type == tokenizer.TOKEN_DATA_TYPE_REAL and rhs_type == tokenizer.TOKEN_REAL_LIT:
            self.generate_op_code(OPCODE.POP_REAL_LIT)
            self.generate_address(symbol.dp)
        elif lhs_type == rhs_type:
            self.generate_op_code(OPCODE.POP)
            self.generate_address(symbol.dp)
        else:
            raise PascalError(f'Type mismatch {lhs_type} != {rhs_type}')
    
    def e(self):
        t1 = self.t()

        while self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_PLUS or \
                self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_MINUS:
            
            op = self.curr_token.type_of
            self.match(op)
            t2 = self.t()
            t1 = self.emit(op, t1, t2)
        
        return t1

    def t(self):
        t1 = self.f()

        while self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_MULTIPLICATION or \
                       self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_DIVISION or \
                       self.curr_token.type_of == 'TK_DIV':

            op = self.curr_token.type_of
            self.match(op)
            t2 = self.f()
            t1 = self.emit(op, t1, t2)
        
        return t1

    def f(self):
        type = self.curr_token.type_of

        if type == tokenizer.TOKEN_ID:
            symbol = self.find_name_or_error()

            if symbol.object_type == symbol_tables.TYPE_VARIABLE:
                self.generate_op_code(OPCODE.PUSH)
                self.generate_address(symbol.dp)
                self.match(tokenizer.TOKEN_ID)
                return symbol.data_type
            
            elif symbol.object_type == symbol_tables.TYPE_ARRAY:
                self.match(tokenizer.TOKEN_ID)
                self.access_array(symbol)
                self.generate_op_code(OPCODE.RETRIEVE)
                return symbol.assignment_type
        
        elif type == 'TK_NOT':
            self.generate_op_code(OPCODE.NOT)
            self.match('TK_NOT')
            return self.f()
        
        elif type == tokenizer.TOKEN_OPERATOR_LEFT_PAREN:
            self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)
            t1 = self.e()
            self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
            return t1
        
        elif type == tokenizer.TOKEN_DATA_TYPE_INT:
            return self.generate_pushi_and_address(tokenizer.TOKEN_DATA_TYPE_INT)
        
        elif type == tokenizer.TOKEN_DATA_TYPE_REAL:
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(self.curr_token.value)
            self.match(tokenizer.TOKEN_DATA_TYPE_REAL)
            return tokenizer.TOKEN_DATA_TYPE_REAL
        
        elif type == tokenizer.TOKEN_REAL_LIT:
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(self.curr_token.value)
            self.match(tokenizer.TOKEN_REAL_LIT)
            return tokenizer.TOKEN_REAL_LIT
        
        elif type == tokenizer.TOKEN_DATA_TYPE_BOOL:
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(self.curr_token.value)
            self.match(tokenizer.TOKEN_DATA_TYPE_BOOL)
            return tokenizer.TOKEN_DATA_TYPE_BOOL
        
        elif type == tokenizer.TOKEN_DATA_TYPE_CHAR:
            return self.generate_pushi_and_address(tokenizer.TOKEN_DATA_TYPE_CHAR)
        
        elif type == tokenizer.TOKEN_CHARACTER:
            self.generate_op_code(OPCODE.PUSH_CHAR)
            self.generate_address(ord(self.curr_token.value))
            self.match(tokenizer.TOKEN_CHARACTER)
            return tokenizer.TOKEN_CHARACTER
        
        elif type == 'TK_TRUE':
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(1)
            self.match('TK_TRUE')
            return tokenizer.TOKEN_DATA_TYPE_BOOL
        
        elif type == 'TK_FALSE':
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(0)
            self.match('TK_FALSE')
            return tokenizer.TOKEN_DATA_TYPE_BOOL
        
        else:
            raise PascalError(f'f() does not support {self.curr_token.value}, {type}')

    def generate_pushi_and_address(self, to_match):
        self.generate_op_code(OPCODE.PUSHI)
        self.generate_address(self.curr_token.value)
        self.match(to_match)
        return to_match

    def condition(self):
        t1 = self.e()
        value = self.curr.value
        
        if CONDITIONALS.get(value) is None:
            raise PascalError(f"Expected conditional, got: {value}")
        else:
            type = self.curr.type
            self.match(type)
            t2 = self.t()
            t1 = self.emit(type, t1, t2)
        
        return t1

    def repeat_statement(self):
        self.match('TK_REPEAT')
        target = self.ip
        self.statements()
        self.match('TK_UNTIL')
        self.condition()
        self.generate_op_code(OPCODE.JFALSE)
        self.generate_address(target)

    def while_statement(self):
        self.match('TK_WHILE')
        target = self.ip
        self.condition()
        self.match('TK_DO')
        self.generate_op_code(OPCODE.JFALSE)
        hole = self.ip
        self.generate_address(0)
        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)
        self.generate_op_code(OPCODE.JMP)
        self.generate_address(target)
        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save

    def if_statement(self):
        self.match('TK_IF')
        self.condition()
        self.match('TK_THEN')
        self.generate_op_code(OPCODE.JFALSE)
        hole = self.ip
        self.generate_address(0)
        self.statements()

        if self.curr_token.type_of == 'TK_ELSE':
            self.generate_op_code(OPCODE.JMP)
            hole_2 = self.ip
            self.generate_address(0)
            save = self.ip
            self.ip = hole
            self.generate_address(save)
            self.ip = save
            hole = hole_2
            self.match('TK_ELSE')
            self.statements()

        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save

    def for_statement(self):
        self.match('TK_FOR')
        value = self.curr_token.value
        self.assignment_statement()
        target = self.ip
        symbol = self.find_name_in_symbol_table(value)

        self.match('TK_TO')
        self.generate_op_code(OPCODE.PUSH)
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE.PUSHI)
        self.generate_address(self.curr_token.value)
        self.generate_op_code(OPCODE.LTE)
        self.match(tokenizer.TOKEN_DATA_TYPE_INT)
        self.match('TK_DO')
        self.generate_op_code(OPCODE.JFALSE)
        hole = self.ip
        self.generate_address(0)

        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)

        self.generate_op_code(OPCODE.PUSH)
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE.PUSHI)
        self.generate_address(1)
        self.generate_op_code(OPCODE.ADD)
        self.generate_op_code(OPCODE.POP)
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE.JMP)
        self.generate_address(target)
        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save

    def array_assignment(self, symbol):
        self.access_array(symbol)
        self.match(tokenizer.TOKEN_OPERATOR_ASSIGNMENT)
        e1 = self.e()
        
        if e1 == symbol.assignment_type:
            self.generate_op_code(OPCODE.DUMP)
        else:
            raise PascalError(f'Array assignment type mismatch with {e1} and {symbol.assignment_type}')
    
    def procedure_declaration(self):
        self.match('TK_PROCEDURE')
        procedure = self.curr_token
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_SEMICOLON)

        self.generate_op_code(OPCODE.JMP)
        hole = self.ip
        self.generate_address(0)

        symbol = symbol_tables.SymbolObject(name=procedure.value,
                                            type_object='TK_PROCEDURE',
                                            data_type=symbol_tables.TYPE_PROCEDURE,
                                            dp = self.dp,
                                            attribute={
                                                'ip': self.ip,
                                                'ret': -1
                                            })

        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)

        self.generate_op_code(OPCODE.JMP)
        symbol.ret = self.ip
        self.generate_address(0)

        self.symbols.append(symbol)
        self.dp += 1

        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save    

    def access_array(self, symbol):
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_BRACKET)
        curr_symbol = self.find_name_or_error()
        self.generate_op_code(OPCODE.PUSH)
        self.generate_address(curr_symbol.dp)
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_OPERATOR_RIGHT_BRACKET)

        self.generate_op_code(OPCODE.PUSHI)

        if curr_symbol.data_type == tokenizer.TOKEN_DATA_TYPE_INT:
            self.generate_address(symbol.left)
            self.generate_op_code(OPCODE.XCHG)
            self.generate_op_code(OPCODE.SUB)
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(4)
            self.generate_op_code(OPCODE.MULTIPLY)
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(symbol.dp)
            self.generate_op_code(OPCODE.ADD)
        elif curr_symbol.data_type == tokenizer.TOKEN_DATA_TYPE_CHAR:
            self.generate_address(symbol.left)
            self.generate_op_code(OPCODE.XCHG)
            self.generate_op_code(OPCODE.SUB)
            self.generate_op_code(OPCODE.PUSHI)
            self.generate_address(symbol.dp)
            self.generate_op_code(OPCODE.ADD)
        else:
            raise Parser(f'Array access with type {curr_symbol.data_type} not supported.')

    def extract_ranges(self, token):
        payload = {}
        split = token.value.split('..')

        if len(split) != 2:
            raise PascalError(f'Unexpected range for array, expected in form of 0..2, got {self.curr_token}')
        
        left, right = split[0], split[1]
        
        if left.isalpha():
            if right.isalpha():
                payload['access_type'] = tokenizer.TOKEN_DATA_TYPE_CHAR
            else:
                raise PascalError(f'Array range mismatch, {left} {right}')
        else:
            if left.__contains__('.'):
                if right.__contains__('.'):
                    left, right = float(left), float(right)
                    payload['data_type'] = tokenizer.TOKEN_DATA_TYPE_REAL
                else:
                    raise PascalError('Array range mismatch, %s %s' % (left, right))
            else:
                left, right = int(left), int(right)
                payload['access_type'] = tokenizer.TOKEN_DATA_TYPE_INT
        
        payload['left'], payload['right'], payload['token'] = left, right, token
        return payload

    def case_statement(self):
        self.match('TK_CASE')
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)
        checker = self.curr_token
        e1 = self.e()

        if e1 == tokenizer.TOKEN_DATA_TYPE_REAL:
            raise PascalError(f'Real type not allowed for case: {e1}')
        
        self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
        self.match('TK_OF')
        hole_list = []

        while self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT or \
                self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR or \
                self.curr_token.type_of == tokenizer.TOKEN_CHARACTER or \
                self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_BOOL:
            
            e2 = self.e()
            self.emit(tokenizer.TOKEN_OPERATOR_EQUALITY, e1, e2)
            self.match(tokenizer.TOKEN_OPERATOR_COLON)

            self.generate_op_code(OPCODE.JFALSE)
            hole = self.ip
            self.generate_address(0)
            self.statements()

            self.generate_op_code(OPCODE.JMP)
            hole_list.append(self.ip)
            self.generate_address(0)

            save = self.ip
            self.ip = hole
            self.generate_address(save)
            self.ip = save

            if self.curr_token.type_of != 'TK_END':
                symbol = self.find_name_in_symbol_table(checker.value)
                if symbol is not None:
                    self.generate_op_code(OPCODE.PUSH)
                    self.generate_address(symbol.dp)

        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)
        save = self.ip

        for hole in hole_list:
            self.ip = hole
            self.generate_address(save)
        
        self.ip = save

    def write_line_statement(self):
        self.match('TK_WRITELN')
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)

        while True:
            if self.curr_token.type_of == tokenizer.TOKEN_ID:
                symbol = self.find_name_or_error()
                if hasattr(symbol, 'assignment_type'):
                    self.match(tokenizer.TOKEN_ID)
                    self.access_array(symbol)
                    self.generate_op_code(OPCODE.RET_AND_PRINT)
                    continue
                else:
                    expression = self.e()

                if expression == tokenizer.TOKEN_DATA_TYPE_INT:
                    self.generate_op_code(OPCODE.PRINT_I)
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_CHAR:
                    self.generate_op_code(OPCODE.PRINT_C)
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_REAL:
                    self.generate_op_code(OPCODE.PRINT_R)
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_BOOL:
                    self.generate_op_code(OPCODE.PRINT_B)
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_ARRAY:
                    self.generate_op_code(OPCODE.RETRIEVE)
                else:
                    raise PascalError(f'writeln does not support {str(symbol)}')
            
            if self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.PRINT_ILIT)
                self.generate_address(int(self.curr_token.value))
                self.match(tokenizer.TOKEN_DATA_TYPE_INT)
            elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR:
                self.generate_op_code(OPCODE.PRINT_C)
                self.generate_address(self.curr_token.value)
                self.match(tokenizer.TOKEN_CHARACTER)
            elif self.curr_token.type_of == tokenizer.TOKEN_STRING_LIT:
                self.generate_op_code(OPCODE.PUSHI)
                s = self.curr_token.value
                s = s[1:-1]
                self.generate_address(len(s))
                self.generate_op_code(OPCODE.PRINT_STR_LIT)
                for byte in bytearray(s):
                    self.byte_array[self.ip] = byte
                    self.ip += 1
                self.match(tokenizer.TOKEN_STRING_LIT)

            type = self.curr_token.type_of
            if type == tokenizer.TOKEN_OPERATOR_COMMA:
                self.match(tokenizer.TOKEN_OPERATOR_COMMA)
            elif type == tokenizer.TOKEN_OPERATOR_RIGHT_PAREN:
                self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
                self.generate_op_code(OPCODE.NEW_LINE)
                return
            else:
                raise PascalError(f'Expected comma or right paren, found: {self.curr_token.type_of}')
    
    def boolean(self, op, t1, t2):
        if t1 == t2:
            self.generate_op_code(op)
        elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
            self.generate_op_code(OPCODE.XCHG)
            self.generate_op_code(OPCODE.CVR)
            self.generate_op_code(OPCODE.XCHG)
            self.generate_op_code(op)
        elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
            self.generate_op_code(OPCODE.CVR)
            self.generate_op_code(op)
        elif t1 == 'TK_CHAR' and t2 == tokenizer.TOKEN_CHARACTER:
            self.generate_op_code(op)
        else:
            return None
        
        return tokenizer.TOKEN_DATA_TYPE_BOOL


    def emit(self, op, t1, t2):
        if op == tokenizer.TOKEN_OPERATOR_PLUS:
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.ADD)
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.FADD)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.FADD)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.FADD)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise PascalError(f'Unable to match operation + with types: {t1} and {t2}')
        
        elif op == tokenizer.TOKEN_OPERATOR_MINUS:
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.SUB)
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.FSUB)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.FSUB)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.FSUB)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise PascalError(f'Unable to match operation - with types: {t1} and {t2}')

        elif op == tokenizer.TOKEN_OPERATOR_DIVISION:
            if t1 == t2:
                if t1 == tokenizer.TOKEN_DATA_TYPE_INT:
                    self.generate_op_code(OPCODE.DIVIDE)
                elif t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                    self.generate_op_code(OPCODE.FDIVIDE)
                return t1
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.DIVIDE)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.DIVIDE)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_REAL_LIT:
                self.generate_op_code(OPCODE.FDIVIDE)
                return t1
            else:
                raise PascalError(f'Unable to match operation / with types: {t1} and {t2}')

        elif op == 'TK_DIV':
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.DIV)
                return tokenizer.TOKEN_DATA_TYPE_INT
            else:
                raise PascalError(f'Unable to match operation div with types: {t1} and {t2}')

        elif op == tokenizer.TOKEN_OPERATOR_MULTIPLICATION:
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.MULTIPLY)
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.XCHG)
                self.generate_op_code(OPCODE.FMULTIPLY)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE.CVR)
                self.generate_op_code(OPCODE.FMULTIPLY)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE.FMULTIPLY)
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise PascalError(f'Unable to match operation * with types: {t1} and {t2}')

        elif op == 'TK_OR':
            if t1 == tokenizer.TOKEN_DATA_TYPE_BOOL and t2 == tokenizer.TOKEN_DATA_TYPE_BOOL:
                self.generate_op_code(OPCODE.OR)
                return tokenizer.TOKEN_DATA_TYPE_BOOL
            else:
                raise PascalError(f'Unable to match operation or with types: {t1} and {t2}')

        elif op == tokenizer.TOKEN_OPERATOR_GTE:
            return self.boolean(OPCODE.GTE, t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_LTE:
            return self.boolean(OPCODE.LTE, t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_EQUALITY:
            return self.boolean(OPCODE.EQL, t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_NOT_EQUAL:
            return self.boolean(OPCODE.NEQ, t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_LEFT_CHEVRON:
            return self.boolean(OPCODE.GTR, t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_RIGHT_CHEVRON:
            return self.boolean(OPCODE.LES, t1, t2)
        else:
            raise PascalError(f'Emit failed to match {op}')

    def variable_declaration(self):
        self.match('TK_VAR')
        declarations = []

        while self.curr_token.type_of == tokenizer.TOKEN_ID:
            if self.curr_token.value in declarations:
                raise PascalError(f'Variable already declared at {self.curr_token.row} {self.curr_token.col}: {self.curr_token.value}')

            declarations.append(self.curr_token.value)
            self.match(tokenizer.TOKEN_ID)

            if self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_COMMA:
                self.match(tokenizer.TOKEN_OPERATOR_COMMA)

        self.match(tokenizer.TOKEN_OPERATOR_COLON)
        
        if self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT:
            self.match(tokenizer.TOKEN_DATA_TYPE_INT)
            data_type = tokenizer.TOKEN_DATA_TYPE_INT
        elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_REAL:
            self.match(tokenizer.TOKEN_DATA_TYPE_REAL)
            data_type = tokenizer.TOKEN_DATA_TYPE_REAL
        elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR:
            self.match(tokenizer.TOKEN_DATA_TYPE_CHAR)
            data_type = tokenizer.TOKEN_DATA_TYPE_CHAR
        elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_BOOL:
            self.match(tokenizer.TOKEN_DATA_TYPE_BOOL)
            data_type = tokenizer.TOKEN_DATA_TYPE_BOOL
        elif self.curr_token.type_of == 'TK_ARRAY':
            self.match('TK_ARRAY')
            data_type = tokenizer.TOKEN_DATA_TYPE_ARRAY
        else:
            raise PascalError(f'{self.curr_token.type_of} data type is invalid {self.curr_token.row} {self.curr_token.col}')

        if data_type == tokenizer.TOKEN_DATA_TYPE_ARRAY:
            self.match(tokenizer.TOKEN_OPERATOR_LEFT_BRACKET)
            extractor = self.extract_ranges(self.curr_token)
            self.match(tokenizer.TOKEN_DATA_TYPE_RANGE)
            self.match(tokenizer.TOKEN_OPERATOR_RIGHT_BRACKET)
            self.match('TK_OF')

            if self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT:
                self.match(tokenizer.TOKEN_DATA_TYPE_INT)
                assignment_type = tokenizer.TOKEN_DATA_TYPE_INT
            elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.match(tokenizer.TOKEN_DATA_TYPE_REAL)
                assignment_type = tokenizer.TOKEN_DATA_TYPE_REAL
            elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR:
                self.match(tokenizer.TOKEN_DATA_TYPE_CHAR)
                assignment_type = tokenizer.TOKEN_DATA_TYPE_CHAR
            elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_BOOL:
                self.match(tokenizer.TOKEN_DATA_TYPE_BOOL)
                assignment_type = tokenizer.TOKEN_DATA_TYPE_BOOL
            else:
                raise PascalError(f'Array of type <{self.curr_token.type_of}> is not valid.')

            self.match(tokenizer.TOKEN_SEMICOLON)
            attributes = {
                'left': extractor['left'],
                'right': extractor['right'],
                'access_type': extractor['access_type'],
                'assignment_type': assignment_type
            }

            if extractor['access_type'] == tokenizer.TOKEN_DATA_TYPE_INT:
                for variable in declarations:
                    self.symbols.append(symbol_tables.SymbolObject(name=variable,
                                                                        object_type=symbol_tables.TYPE_ARRAY,
                                                                        data_type=tokenizer.TOKEN_DATA_TYPE_ARRAY,
                                                                        dp=self.dp,
                                                                        attribute=attributes))
                    self.dp += 4 * int(extractor['right']) - int(extractor['left'])
            
            elif extractor['access_type'] == tokenizer.TOKEN_DATA_TYPE_CHAR:
                pass
            else:
                raise PascalError('Array access type of %s is not allowed.' % extractor['access_type'])

        else:
            self.match(tokenizer.TOKEN_SEMICOLON)
            for variable in declarations:
                self.symbols.append(symbol_tables.SymbolObject(name=variable,
                                                                    object_type=symbol_tables.TYPE_VARIABLE,
                                                                    data_type=data_type,
                                                                    dp=self.dp))
                self.dp += 1
        
        if self.curr_token.type_of == 'TK_VAR':
            self.variable_declaration()
        elif self.curr_token.type_of == 'TK_PROCEDURE':
            self.procedure_declaration()
        else:
            self.begin()

    def statements(self):
        while self.curr_token.type_of != 'TK_END':
            type_of = self.curr_token.type_of
            if type_of == 'TK_WRITELN':
                self.write_line_statement()
            elif type_of == tokenizer.TOKEN_ID:
                self.assignment_statement()
            elif type_of == 'TK_WHILE':
                self.while_statement()
            elif type_of == 'TK_REPEAT':
                self.repeat_statement()
            elif type_of == 'TK_IF':
                self.if_statement()
            elif type_of == 'TK_FOR':
                self.for_statement()
            elif type_of == 'TK_CASE':
                self.case_statement()
            elif type_of == tokenizer.TOKEN_SEMICOLON:
                self.match(tokenizer.TOKEN_SEMICOLON)
            elif type_of == tokenizer.TOKEN_COMMENT:
                self.match(tokenizer.TOKEN_COMMENT)
            else:
                return
