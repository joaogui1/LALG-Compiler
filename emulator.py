from helper import *
from constants import *
from loader.lalg_error import LalgError

class Emulator(object):
    ''' Emulator Class - uses bytes generated from tokens to execute code '''

    def __init__(self, bytes) -> None:
        ''' Initializes artibutes '''
        self.data_array = {}
        self.stack = []
        self.bytes = bytes
        self.out = []
        self.ip = 0
        self.pointer = 0

    def flush(self) -> None:
        ''' Prints generated output '''
        print('Flushing...')

        for item in self.out:
            print(item, end='')
        
        print()

    def start(self):
        ''' For each operation code, executes its respective function 
        
        Raises
        ------
        LalgError
            if operation is not defined
        '''
        operations = {
            OPCODE['ADD']: self.add,
            OPCODE['CVR']: self.cvr,
            OPCODE['DIV']: self.div,
            OPCODE['DIVIDE']: self.divide,
            OPCODE['DUMP']: self.dump,
            OPCODE['EQL']: self.eql,
            OPCODE['FADD']: self.f_add,
            OPCODE['FDIVIDE']: self.f_divide,
            OPCODE['FMULTIPLY']: self.f_multiply,
            OPCODE['FSUB']: self.f_sub,
            OPCODE['GTE']: self.gte,
            OPCODE['GTR']: self.gtr,
            OPCODE['HALT']: self.halt,
            OPCODE['JFALSE']: self.jfalse,
            OPCODE['JMP']: self.jmp,
            OPCODE['LES']: self.les,
            OPCODE['LTE']: self.lte,
            OPCODE['MULTIPLY']: self.multiply,
            OPCODE['NEQ']: self.neq,
            OPCODE['NEW_LINE']: self.print_new_line,
            OPCODE['POP_CHAR']: self.pop_char,
            OPCODE['POP_REAL_LIT']: self.pop_real_lit,
            OPCODE['POP']: self.pop,
            OPCODE['PRINT_C']: self.print_c,
            OPCODE['PRINT_I']: self.print_i,
            OPCODE['PRINT_ILIT']: self.print_ilit,
            OPCODE['PRINT_R']: self.print_r,
            OPCODE['PRINT_STR_LIT']: self.print_str_lit, 
            OPCODE['PUSH_CHAR']: self.push_char,
            OPCODE['PUSH']: self.push,
            OPCODE['PUSHI']: self.pushi,
            OPCODE['RET_AND_PRINT']: self.ret_and_print,
            OPCODE['RETRIEVE']: self.retrieve,
            OPCODE['SUB']: self.sub,
            OPCODE['XCHG']: self.xchg,
            OPCODE['READ_INT']: self.read_int,
            OPCODE['READ_REAL']: self.read_real,
        }

        op = self.bytes[self.ip]
        
        if op in operations:
            operations[op]()

            # if operation is not the last one, recursive call start function
            if op != OPCODE['HALT']:
                self.start()
        else:
            raise LalgError(f'Operation {op} is not supported')

    def pushi(self) -> None:
        ''' Pushes integer to stack '''
        self.ip += 1
        self.stack.append(self.immediate_value())

    def immediate_value(self) -> object:
        ''' Generates value from bytes
        
        Returns 
        -------
        number
            number (int or float) generated from the bytes or variable position
        '''
        
        immediate = bytearray()

        for i in range(4):
            immediate.append(self.bytes[self.ip])
            self.ip += 1
        
        return byte_unpacker(immediate)

    def immediate_data(self) -> object:
        ''' Generates value from variable
        
        Returns 
        -------
        object
            value of a given variable
        '''
        imm = self.immediate_value()
        if imm not in self.data_array:
            self.halt()

        return self.data_array[imm]

    def pop(self) -> object:
        ''' Pops value from stack and adds it to the variables array
        
        Returns
        -------
        object
            value from the top of the stack
        '''
        self.ip += 1
        popped_value = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = popped_value
        self.pointer += 1
        return popped_value

    def push(self) -> None:
        ''' Pushes value to stack '''
        self.ip += 1
        imm = self.immediate_data()
        self.stack.append(imm)

    def print_i(self) -> None:
        ''' Adds integer to the output array '''
        self.ip += 1
        self.out.append(self.immediate_data())

    def print_new_line(self) -> None:
        ''' Adds \n to the output array '''
        self.ip += 1
        self.out.append('\n')

    def sub(self) -> None:
        ''' Subtracts two top values from stack '''
        self.ip += 1
        top = self.stack.pop()
        new_top = self.stack.pop() - top
        self.stack.append(new_top)

    def add(self) -> None:
        ''' Adds two top values from stack '''
        self.ip += 1
        new_top = self.stack.pop() + self.stack.pop()
        self.stack.append(new_top)

    def multiply(self) -> None:
        ''' Multiply two top values from stack '''
        self.ip += 1
        new_top = self.stack.pop() * self.stack.pop()
        self.stack.append(new_top)

    def divide(self) -> None:
        ''' Divides two top values from stack '''
        self.ip += 1
        denom = self.stack.pop()
        new_top = self.stack.pop() / float(denom)
        self.stack.append(new_top)
    
    def div(self):
        ''' Integer division between two top values from stack '''
        self.ip += 1
        denom = int(self.stack.pop())
        new_top = int(self.stack.pop()) / denom
        self.stack.append(new_top)

    def jfalse(self) -> None:
        ''' Jumps if false '''
        self.ip += 1

        if self.stack.pop():
            self.immediate_value()
        else:
            imm = self.immediate_value()
            self.ip = imm

    def gte(self) -> None:
        ''' Adds greater or equal than bool result to stack '''
        self.ip += 1
        new_top = self.stack.pop() <= self.stack.pop()
        self.stack.append(new_top)

    def gtr(self) -> None:
        ''' Adds greater than bool result to stack '''
        self.ip += 1
        new_top = self.stack.pop() > self.stack.pop()
        self.stack.append(new_top)

    def lte(self) -> None:
        ''' Adds less or equal than operator to stack '''
        self.ip += 1
        new_top = self.stack.pop() >= self.stack.pop()
        self.stack.append(new_top)

    def les(self) -> None:
        ''' Adds less than bool result to stack '''
        self.ip += 1
        new_top = self.stack.pop() < self.stack.pop()
        self.stack.append(new_top)

    def eql(self) -> None:
        ''' Adds equal bool result to stack '''
        self.ip += 1
        new_top = self.stack.pop() == self.stack.pop()
        self.stack.append(new_top)

    def neq(self) -> None:
        ''' Adds not equal bool result to stack '''
        self.ip += 1
        new_top = self.stack.pop() != self.stack.pop()
        self.stack.append(new_top)

    def xchg(self) -> None:
        ''' Swaps two top values from stack '''
        self.ip += 1
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def cvr(self) -> None:
        ''' Converts top value to float '''
        self.ip += 1
        new_top = float(self.stack.pop())
        self.stack.append(new_top)

    def jmp(self) -> None:
        ''' Jumps to position '''
        self.ip += 1
        self.ip = self.immediate_value()

    def pop_char(self) -> object:
        ''' Pops char from stack and adds it to the variables array '''
        self.ip += 1
        top = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = top
        self.pointer += 1
        return top

    def read_int(self) -> object:
        ''' Reads integer from user
        
        Raises
        ------
        LalgError
            if input value is not int

        Returns
        -------
        int
            user input
        '''
        self.ip += 1
        user_input = input()
        try:
            user_input = int(user_input)
        except:
            raise LalgError("Value entered is not valid")
        
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = user_input
        self.pointer += 1
        return user_input

    def read_real(self) -> object:
        ''' Reads from from user
        
        Raises
        ------
        LalgError
            if input value is not float

        Returns
        -------
        float
            user input
        '''
        self.ip += 1
        user_input = input()
        try:
            user_input = float(user_input)
        except:
            raise LalgError("Value entered is not valid")
        
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = user_input
        self.pointer += 1
        return user_input

    def push_char(self) -> None:
        ''' Pushes char stack '''
        self.ip += 1
        new_top = chr(self.immediate_value())
        self.stack.append(new_top)

    def f_divide(self) -> None:
        ''' Divides two floats '''
        self.ip += 1
        denom = bits_to_float(self.stack.pop())
        new_top = self.stack.pop() / float(denom)
        self.stack.append(new_top)

    def f_multiply(self) -> None:
        ''' Multiply two floats '''
        self.ip += 1
        new_top = float(self.stack.pop()) * float(self.stack.pop())
        self.stack.append(new_top)

    def f_add(self) -> None:
        ''' Adds two floats '''
        self.ip += 1
        new_top = float(self.stack.pop()) + float(self.stack.pop())
        self.stack.append(new_top)

    def f_sub(self) -> None:
        ''' Subtracts two floats '''
        self.ip += 1
        top = float(self.stack.pop())
        new_top = float(self.stack.pop()) - top
        self.stack.append(new_top)

    def dump(self) -> None:
        ''' Attributes value to variable '''
        self.ip += 1
        assignment = self.stack.pop()
        self.pointer = self.stack.pop()
        self.data_array[self.pointer] = assignment
        self.pointer += 1

    def retrieve(self) -> None:
        ''' Gets value from variable '''
        self.ip += 1
        self.pointer = self.stack.pop()
        self.stack.append(self.data_array[self.pointer])
    
    def print_c(self) -> None:
        ''' Adds char to output array '''
        self.ip += 1
        out_val = self.data_array[self.immediate_value()]
        self.out.append(out_val)

    def print_r(self) -> None:
        ''' Adds float to output array '''
        self.ip += 1
        self.out.append(self.immediate_data())

    def print_ilit(self) -> None:
        ''' Adds literal integer to output array '''
        self.ip += 1
        val = self.immediate_value()
        self.out.append(val)

    def ret_and_print(self) -> None:
        ''' Attributes value and adds it to output array '''
        self.ip += 1
        self.pointer = self.stack.pop()
        out_val = self.data_array[self.pointer]
        self.out.append(out_val)

    def print_str_lit(self) -> None:
        ''' Adds literal string to output array '''
        self.ip += 1
        text_len = self.stack.pop()
        text = ''

        for _ in range(text_len):
            text += chr(self.bytes[self.ip])
            self.ip += 1
        
        self.out.append(text)
    
    def pop_real_lit(self) -> None:
        ''' Adds literal float to output array '''
        self.ip += 1
        top = self.stack.pop()
        new_val = float('{0:.2f}'.format(bits_to_float(top)))
        self.data_array[self.immediate_value()] = new_val
        self.pointer += 1
    
    def halt(self) -> None:
        ''' Finishes execution '''
        print('Done!')
        self.flush()
        exit(0)