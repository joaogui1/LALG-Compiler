import tokenizer
from helper import *
from constants import *
from loader.lalg_error import LalgError
import loader.symbol_tables as symbol_tables

class Parser(object):
    ''' Parser Class - parses tokens '''
    SIZE = 5000

    def __init__(self, tokens) -> None:
        ''' Initializes artibutes '''
        self.tokens = iter(tokens)
        self.curr_token = None
        self.ip = 0
        self.dp = 0
        self.symbol_table = []
        self.bytes = bytearray(self.SIZE)

    def find_name_in_symbol_table(self, name) -> object:
        ''' Checks if symbol is in symbols table
        
        Parameters
        ----------
        name : str
            symbol name to search
        
        Returns
        -------
        symbol or None
            if symbol is found returns it, and None otherwise
        '''
        for symbol in self.symbol_table:
            if symbol.name == name:
                return symbol
        
        return None

    def match(self, token_type) -> None:
        ''' Matches current and expected symbols
        
        Parameters
        ----------
        token_type : str
            expected token type
        
        Raises
        ------
        LalgError
            if tokens don't match
        '''
        if self.curr_token.type_of == token_type:
            try:
                self.curr_token = next(self.tokens)
            except StopIteration:
                return
        else:
            raise LalgError(f'Token mismatch at {self.curr_token.row} {self.curr_token.column}. Expected {str(self.curr_token)} and got {str(token_type)}')

    def generate_op_code(self, op_code) -> None:
        ''' Stores op code in the bytes array, which will be used by the Emulator to
        execute the code.
        
        Parameters
        ----------
        op_code : OPCODE element
            op code to store
        '''
        self.bytes[self.ip] = op_code
        self.ip += 1

    def generate_address(self, target) -> None:
        ''' Stores address (variables, for example) in the bytes array, which will be used 
        by the Emulator to execute the code.
        
        Parameters
        ----------
        target : object
            value to store
        '''
        for byte in byte_packer(target):
            self.bytes[self.ip] = byte
            self.ip += 1

    def parse(self) -> object:
        ''' Parses tokens 
        
        Raises
        ------
        LalgError
            if token type is invalid

        Returns
        -------
        list
            list of bytes to be executed by the Emulator
        '''
        # matches begin of the file
        self.curr_token = next(self.tokens)
        self.match('TK_PROGRAM')
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_SEMICOLON)
        
        # consumes comments
        while self.curr_token.type_of == 'TK_COMMENT':
            self.match(tokenizer.TOKEN_COMMENT)

        # matches watch comes next - variable declarations, procedures or begin
        if self.curr_token.type_of == 'TK_VAR':
            self.variable_declaration()
        elif self.curr_token.type_of == 'TK_PROCEDURE':
            while self.curr_token.type_of == 'TK_PROCEDURE':
                self.procedure_declaration()
            self.begin()
        elif self.curr_token.type_of == 'TK_BEGIN':
            self.begin()
        else:
            raise LalgError(f'Invalid token when parsing')

        return self.bytes

    def var_already_declared(self, declarations) -> bool:
        ''' Checks if a variable was already declared '''
        return self.curr_token.value_of in declarations

    def variable_declaration(self, procedure=False) -> None:
        ''' Deals with variable declarations 
        
        Parameters
        ----------
        procedure : bool
            whether this comes or not from a procedure

        Raises
        ------
        LalgError
            if variable was already declared
            if variable type is invalid
        '''
        if not procedure:
            self.match('TK_VAR')
        declarations = []

        # gets all variables declared in the same line
        while self.curr_token.type_of == tokenizer.TOKEN_ID:
            if self.var_already_declared(declarations):
                raise LalgError(f'Variable already declared: {self.curr_token.value_of}')

            declarations.append(self.curr_token.value_of)
            self.match(tokenizer.TOKEN_ID)
            
            if self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_COMMA:
                self.match(tokenizer.TOKEN_OPERATOR_COMMA)

        self.match(tokenizer.TOKEN_OPERATOR_COLON)
        
        # gets variables type
        if self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT:
            self.match(tokenizer.TOKEN_DATA_TYPE_INT)
            data_type = tokenizer.TOKEN_DATA_TYPE_INT
        elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_REAL:
            self.match(tokenizer.TOKEN_DATA_TYPE_REAL)
            data_type = tokenizer.TOKEN_DATA_TYPE_REAL
        else:
            raise LalgError(f'{self.curr_token.type_of} data type is invalid at {self.curr_token.row} {self.curr_token.column}')

        if procedure:
            self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
        
        self.match(tokenizer.TOKEN_SEMICOLON)
        
        # adds all variables to the symbols table
        for variable in declarations:
            new_symbol = symbol_tables.SymbolObject(name=variable,
                                                    object_type=symbol_tables.TYPE_VARIABLE,
                                                    data_type=data_type,
                                                    dp=self.dp)
            self.symbol_table.append(new_symbol)
            self.dp += 1
        
        # Checks what to do next
        if self.curr_token.type_of == 'TK_VAR':
            self.variable_declaration()
        elif self.curr_token.type_of == 'TK_PROCEDURE':
            self.procedure_declaration()
        elif self.curr_token.type_of == 'TK_BEGIN':
            self.begin()
        else:
            raise LalgError(f'Invalid token when parsing')

    def begin(self) -> None:
        ''' Matches the format of a lalg code '''
        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_DOT)
        self.match(tokenizer.TOKEN_EOF)
        self.generate_op_code(OPCODE['HALT'])

    def statements(self) -> None:
        ''' Deals with all the possible statements in the code '''
        while self.curr_token.type_of != 'TK_END':
            type_of = self.curr_token.type_of

            if type_of == 'TK_WRITE':
                self.write_statement()
            elif type_of == 'TK_READ':
                self.read_statement()
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

    def find_name_or_error(self) -> object:
        ''' Checks if a symbol (variable) exists 
        
        Returns
        -------
        symbol
            symbol for the current token value
        
        Raises
        ------
        LalgError
            if variable is not declared
        '''
        symbol = self.find_name_in_symbol_table(self.curr_token.value_of)

        if symbol is None:
            raise LalgError(f'Variable {self.curr_token.value_of} is not declared')
        else:
            return symbol

    def assignment_statement(self) -> None:
        ''' Deals with assignment statements 
        
        Raises
        ------
        LalgError
            if variable and value type mismatch
        '''
        
        # gets symbol and value to be attributed
        symbol = self.find_name_or_error()
        lhs_type = symbol.data_type
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_OPERATOR_ASSIGNMENT)
        rhs_type = self.e()

        # check if variable type and value type match
        if rhs_type == tokenizer.TOKEN_CHARACTER:
            self.generate_op_code(OPCODE['POP_CHAR'])
            self.generate_address(symbol.dp)
        elif lhs_type == tokenizer.TOKEN_DATA_TYPE_REAL and rhs_type == tokenizer.TOKEN_REAL_LIT:
            self.generate_op_code(OPCODE['POP_REAL_LIT'])
            self.generate_address(symbol.dp)
        elif lhs_type == rhs_type:
            self.generate_op_code(OPCODE['POP'])
            self.generate_address(symbol.dp)
        else:
            raise LalgError(f'Type mismatch expected {lhs_type} and got {rhs_type}')

    def read_statement(self) -> None:
        ''' Deals with read statements 
        
        Raises
        ------
        LalgError
            if type is invalid
            if statement doesn't end with )
        '''
        self.match('TK_READ')
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)

        while True:
            # gets symbol
            symbol = self.find_name_or_error()
            lhs_type = symbol.data_type
            self.match(tokenizer.TOKEN_ID)

            # adds read opcodes
            if lhs_type == tokenizer.TOKEN_DATA_TYPE_INT:
                self.generate_op_code(OPCODE['READ_INT'])
                self.generate_address(symbol.dp)
            elif lhs_type == tokenizer.TOKEN_DATA_TYPE_REAL:
                self.generate_op_code(OPCODE['READ_REAL'])
                self.generate_address(symbol.dp)
            else:
                raise LalgError(f'Invalid type {lhs_type}')

            # checks if there are more variables to read
            type_of = self.curr_token.type_of
            if type_of == tokenizer.TOKEN_OPERATOR_COMMA:
                self.match(tokenizer.TOKEN_OPERATOR_COMMA)
            elif type_of == tokenizer.TOKEN_OPERATOR_RIGHT_PAREN:
                self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
                return
            else:
                raise LalgError(f'Expected comma or right paren, found: {self.curr_token.type_of}')

    def e(self) -> object:
        ''' Deals with expressions with less priority such as + and -
        
        Returns
        -------
        object
            operation result
        '''
        # gets one operator
        t1 = self.t()

        # does the operation with the respective operators
        while self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_PLUS or \
                self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_MINUS:

            op = self.curr_token.type_of
            self.match(op)
            t2 = self.t()
            t1 = self.emit(op, t1, t2)

        return t1

    def t(self) -> object:
        ''' Deals with expressions with medium priority such as * and /
        
        Returns
        -------
        object
            operation result
        '''
        # gets one operator
        t1 = self.f()

        # does the operation with the respective operators
        while self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_MULTIPLICATION or \
                self.curr_token.type_of == tokenizer.TOKEN_OPERATOR_DIVISION or \
                self.curr_token.type_of == 'TK_DIV':

            op = self.curr_token.type_of
            self.match(op)
            t2 = self.f()
            t1 = self.emit(op, t1, t2)

        return t1

    def generate_pushi_and_address(self, to_match):
        ''' Adds value and operator to the operations codes to be executed '''
        self.generate_op_code(OPCODE['PUSHI'])
        self.generate_address(self.curr_token.value_of)
        self.match(to_match)
        return to_match

    def f(self) -> object:
        ''' Deals with expressions
        
        Raises
        ------
        LalgError
            if operation is not supported

        Returns
        -------
        object
            operation result
        '''
        token_type = self.curr_token.type_of

        if token_type == tokenizer.TOKEN_ID: # varibles
            symbol = self.find_name_or_error()

            if symbol.object_type == symbol_tables.TYPE_VARIABLE:
                self.generate_op_code(OPCODE['PUSH'])
                self.generate_address(symbol.dp)
                self.match(tokenizer.TOKEN_ID)
                return symbol.data_type
        elif token_type == 'TK_NOT': # not 
            self.generate_op_code(OPCODE['NOT'])
            self.match('TK_NOT')
            return self.f()
        elif token_type == tokenizer.TOKEN_OPERATOR_LEFT_PAREN: # (
            self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)
            t1 = self.e()
            self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
            return t1
        elif token_type == tokenizer.TOKEN_DATA_TYPE_INT: # integer value
            return self.generate_pushi_and_address(tokenizer.TOKEN_DATA_TYPE_INT)
        elif token_type == tokenizer.TOKEN_DATA_TYPE_REAL: # float value
            self.generate_op_code(OPCODE['PUSHI'])
            self.generate_address(self.curr_token.value_of)
            self.match(tokenizer.TOKEN_DATA_TYPE_REAL)
            return tokenizer.TOKEN_DATA_TYPE_REAL
        elif token_type == tokenizer.TOKEN_REAL_LIT: # float literal value
            self.generate_op_code(OPCODE['PUSHI'])
            self.generate_address(self.curr_token.value_of)
            self.match(tokenizer.TOKEN_REAL_LIT)
            return tokenizer.TOKEN_REAL_LIT
        else:
            raise LalgError(f'f() does not support {self.curr_token.value_of} {token_type}')

    def condition(self) -> object:
        ''' Deals with conditions 
        
        Raises
        ------
        LalgError
            if condition is invalid

        Returns
        -------
        object
            condition result
        '''
        t1 = self.e()
        value_of = self.curr_token.value_of

        if CONDITIONALS.get(value_of) is None:
            raise LalgError(f"Expected conditional, got: {value_of}")
        
        type_of = self.curr_token.type_of
        self.match(type_of)
        t2 = self.e()
        t1 = self.emit(type_of, t1, t2)

        return t1

    def boolean(self, op, t1, t2) -> object:
        ''' Deals with booleans (in conditionals, for example) 
        
        Parameters
        ----------
        op : object
            operation
        t1 : object
            left operator
        t2 : object
            right operator

        Returns
        -------
        Bool Token or None       
        '''
        if t1 == t2:
            self.generate_op_code(op)
        elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
            self.generate_op_code(OPCODE['XCHG'])
            self.generate_op_code(OPCODE['CVR'])
            self.generate_op_code(OPCODE['XCHG'])
            self.generate_op_code(op)
        elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT:
            self.generate_op_code(OPCODE['CVR'])
            self.generate_op_code(op)
        elif t1 == 'TK_CHAR' and t2 == tokenizer.TOKEN_CHARACTER:
            self.generate_op_code(op)
        else:
            return None

        return tokenizer.TOKEN_DATA_TYPE_BOOL

    def emit(self, op, t1, t2) -> object:
        ''' Executes operations
        
        Parameters
        ----------
        op : object
            operation
        t1 : object
            left operator
        t2 : object
            right operator
        
        Raises
        ------
        LalgError
            if operators types don't match
            if operation is not supported

        Returns
        -------
        token
            operation result token type
        '''
        if op == tokenizer.TOKEN_OPERATOR_PLUS: # sum
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # between integers
                self.generate_op_code(OPCODE['ADD'])
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # integer and float
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['FADD'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # float and int
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['FADD'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # float and float
                self.generate_op_code(OPCODE['FADD'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise LalgError(f'Unable to match operation + with types {t1} and {t2}')

        elif op == tokenizer.TOKEN_OPERATOR_MINUS: # subtraction
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # between integers
                self.generate_op_code(OPCODE['SUB'])
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # int and float
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['FSUB'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # float and int
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['FSUB'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # between floats
                self.generate_op_code(OPCODE['FSUB'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise LalgError(f'Unable to match operation - with types {t1} and {t2}')

        elif op == tokenizer.TOKEN_OPERATOR_DIVISION: # division
            if t1 == t2: # same operator
                if t1 == tokenizer.TOKEN_DATA_TYPE_INT:
                    self.generate_op_code(OPCODE['DIVIDE'])
                elif t2 == tokenizer.TOKEN_DATA_TYPE_REAL:
                    self.generate_op_code(OPCODE['FDIVIDE'])
                return t1
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # int and float
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['DIVIDE'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # float and int
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['DIVIDE'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_REAL_LIT: # float and literal float
                self.generate_op_code(OPCODE['FDIVIDE'])
                return t1
            else:
                raise LalgError(f'Unable to match operation / with types {t1} and {t2}')

        elif op == 'TK_DIV': # div
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # between ints
                self.generate_op_code(OPCODE['DIV'])
                return tokenizer.TOKEN_DATA_TYPE_INT
            else:
                raise LalgError('Unable to match operation div with types {t1} and {t2}')
        
        elif op == tokenizer.TOKEN_OPERATOR_MULTIPLICATION: # multiplication
            if t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # between ints
                self.generate_op_code(OPCODE['MULTIPLY'])
                return tokenizer.TOKEN_DATA_TYPE_INT
            elif t1 == tokenizer.TOKEN_DATA_TYPE_INT and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # int and float
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['XCHG'])
                self.generate_op_code(OPCODE['FMULTIPLY'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_INT: # float and int
                self.generate_op_code(OPCODE['CVR'])
                self.generate_op_code(OPCODE['FMULTIPLY'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            elif t1 == tokenizer.TOKEN_DATA_TYPE_REAL and t2 == tokenizer.TOKEN_DATA_TYPE_REAL: # between floats
                self.generate_op_code(OPCODE['FMULTIPLY'])
                return tokenizer.TOKEN_DATA_TYPE_REAL
            else:
                raise LalgError('Unable to match operation * with with types {t1} and {t2}')
        
        elif op == 'TK_OR': # or
            if t1 == tokenizer.TOKEN_DATA_TYPE_BOOL and t2 == tokenizer.TOKEN_DATA_TYPE_BOOL:
                self.generate_op_code(OPCODE['OR'])
                return tokenizer.TOKEN_DATA_TYPE_BOOL
            else:
                raise LalgError('Unable to match operation or with types: with types {t1} and {t2}')
        
        elif op == tokenizer.TOKEN_OPERATOR_GTE: # >=
            return self.boolean(OPCODE['GTE'], t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_LTE: # <=
            return self.boolean(OPCODE['LTE'], t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_EQUALITY: # ==
            return self.boolean(OPCODE['EQL'], t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_NOT_EQUAL:
            return self.boolean(OPCODE['NEQ'], t1, t2) # <>
        elif op == tokenizer.TOKEN_OPERATOR_LEFT_CHEVRON: # <
            return self.boolean(OPCODE['GTR'], t1, t2)
        elif op == tokenizer.TOKEN_OPERATOR_RIGHT_CHEVRON: # >
            return self.boolean(OPCODE['LES'], t1, t2)
        else:
            raise LalgError(f'Failed to match operation {op}')

    def write_statement(self) -> object:
        ''' Deals with write statements 
        
        Raises
        ------
        LalgError
            if statement doesn't end with )
        '''
        self.match('TK_WRITE')
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)

        while True:
            if self.curr_token.type_of == tokenizer.TOKEN_ID: # prints variable
                symbol = self.find_name_or_error()
                expression = self.e()

                if expression == tokenizer.TOKEN_DATA_TYPE_INT:
                    self.generate_op_code(OPCODE['PRINT_I'])
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_CHAR:
                    self.generate_op_code(OPCODE['PRINT_C'])
                    self.generate_address(symbol.dp)
                elif expression == tokenizer.TOKEN_DATA_TYPE_REAL:
                    self.generate_op_code(OPCODE['PRINT_R'])
                    self.generate_address(symbol.dp)
                else:
                    raise LalgError(f'write does not support symbol {str(symbol)}')

            if self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT: # literal int
                self.generate_op_code(OPCODE['PRINT_ILIT'])
                self.generate_address(int(self.curr_token.value_of))
                self.match(tokenizer.TOKEN_DATA_TYPE_INT)
            elif self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR: # literal char
                self.generate_op_code(OPCODE['PRINT_C'])
                self.generate_address(self.curr_token.value_of)
                self.match(tokenizer.TOKEN_CHARACTER)
            elif self.curr_token.type_of == tokenizer.TOKEN_STRING_LIT: # literal string
                self.generate_op_code(OPCODE['PUSHI'])
                s = self.curr_token.value_of[1:-1]
                self.generate_address(len(s))
                self.generate_op_code(OPCODE['PRINT_STR_LIT'])

                for byte in bytearray(s, encoding='utf8'):
                    self.bytes[self.ip] = byte
                    self.ip += 1

                self.match(tokenizer.TOKEN_STRING_LIT)

            # checks if there are more variables to read
            type_of = self.curr_token.type_of
            if type_of == tokenizer.TOKEN_OPERATOR_COMMA:
                self.match(tokenizer.TOKEN_OPERATOR_COMMA)
            elif type_of == tokenizer.TOKEN_OPERATOR_RIGHT_PAREN:
                self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
                return
            else:
                raise LalgError(f'Expected comma or right paren, found: {self.curr_token.type_of}')

    def repeat_statement(self) -> None:
        ''' Deals with repetition statements '''
        self.match('TK_REPEAT')
        target = self.ip
        self.statements()
        self.match('TK_UNTIL')
        self.condition()
        self.generate_op_code(OPCODE['JFALSE'])
        self.generate_address(target)

    def while_statement(self) -> None:
        ''' Deals with while statements '''
        self.match('TK_WHILE')
        target = self.ip
        self.condition()
        self.match('TK_DO')
        self.generate_op_code(OPCODE['JFALSE'])
        hole = self.ip
        self.generate_address(0)
        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)
        self.generate_op_code(OPCODE['JMP'])
        self.generate_address(target)
        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save

    def if_statement(self) -> None:
        ''' Deals with if statements '''

        self.match('TK_IF')
        self.condition()
        self.match('TK_THEN')
        self.generate_op_code(OPCODE['JFALSE'])
        hole = self.ip
        self.generate_address(0)

        # nested begins
        if self.curr_token.type_of == 'TK_BEGIN':
            self.match('TK_BEGIN')
            self.statements()
            self.match('TK_END')
        else:
            self.statements()

        # checks for an else
        if self.curr_token.type_of == 'TK_ELSE':
            self.generate_op_code(OPCODE['JMP'])
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
        ''' Deals with for statements '''
        self.match('TK_FOR')
        value_of = self.curr_token.value_of
        self.assignment_statement()
        target = self.ip
        symbol = self.find_name_in_symbol_table(value_of)

        self.match('TK_TO')
        self.generate_op_code(OPCODE['PUSH'])
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE['PUSHI'])
        self.generate_address(self.curr_token.value_of)
        self.generate_op_code(OPCODE['LTE'])
        self.match(tokenizer.TOKEN_DATA_TYPE_INT)

        self.match('TK_DO')
        self.generate_op_code(OPCODE['JFALSE'])
        hole = self.ip
        self.generate_address(0)

        self.match('TK_BEGIN')
        self.statements()

        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)
        self.generate_op_code(OPCODE['PUSH'])
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE['PUSHI'])
        self.generate_address(1)
        self.generate_op_code(OPCODE['ADD'])
        self.generate_op_code(OPCODE['POP'])
        self.generate_address(symbol.dp)
        self.generate_op_code(OPCODE['JMP'])
        self.generate_address(target)
        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save

    def case_statement(self):
        ''' Deals with case statements '''
        self.match('TK_CASE')
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)
        checker = self.curr_token
        e1 = self.e()

        if e1 == tokenizer.TOKEN_DATA_TYPE_REAL:
            raise LalgError('Real type not allowed for case: {e1}')
        
        self.match(tokenizer.TOKEN_OPERATOR_RIGHT_PAREN)
        self.match('TK_OF')
        hole_list = []
        while self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_INT or \
                self.curr_token.type_of == tokenizer.TOKEN_DATA_TYPE_CHAR:
            e2 = self.e()
            self.emit(tokenizer.TOKEN_OPERATOR_EQUALITY, e1, e2)
            self.match(tokenizer.TOKEN_OPERATOR_COLON)

            self.generate_op_code(OPCODE['JFALSE'])
            hole = self.ip
            self.generate_address(0)
            self.statements()

            self.generate_op_code(OPCODE['JMP'])
            hole_list.append(self.ip)
            self.generate_address(0)

            save = self.ip
            self.ip = hole
            self.generate_address(save)
            self.ip = save

            if self.curr_token.type_of != 'TK_END':
                symbol = self.find_name_in_symbol_table(checker.value_of)

                if symbol is not None:
                    self.generate_op_code(OPCODE['PUSH'])
                    self.generate_address(symbol.dp)

        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)
        save = self.ip
        
        for hole in hole_list:
            self.ip = hole
            self.generate_address(save)
        
        self.ip = save

    def procedure_declaration(self) -> None:
        ''' Deals with procedure declarations '''
        # matches procedure format
        self.match('TK_PROCEDURE')
        procedure = self.curr_token
        self.match(tokenizer.TOKEN_ID)
        self.match(tokenizer.TOKEN_OPERATOR_LEFT_PAREN)
        self.variable_declaration(procedure=True)
        self.match(tokenizer.TOKEN_SEMICOLON)

        self.generate_op_code(OPCODE['JMP'])
        hole = self.ip
        self.generate_address(0)

        # adds symbol for the procedure
        symbol = symbol_tables.SymbolObject(name=procedure.value_of,
                                            object_type='TK_PROCEDURE',
                                            data_type=symbol_tables.TYPE_PROCEDURE,
                                            dp=self.dp,
                                            attribute={
                                                'ip': self.ip,
                                                'ret': -1
                                            })

        # matches the procedure itself
        self.match('TK_BEGIN')
        self.statements()
        self.match('TK_END')
        self.match(tokenizer.TOKEN_SEMICOLON)

        self.generate_op_code(OPCODE['JMP'])
        symbol.ret = self.ip
        self.generate_address(0)

        self.symbol_table.append(symbol)
        self.dp += 1

        save = self.ip
        self.ip = hole
        self.generate_address(save)
        self.ip = save