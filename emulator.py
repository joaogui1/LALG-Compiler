from loader import PascalError
from constants import *
import sys

class Emulator(object):
    def __init__(self, bytes) -> None:
        self.bytes = bytes
        self.data = {}
        self.stack = []
        self.out = []
        self.ip = 0
        self.pointer = 0
    
    def start(self) -> None:
        operations = {
            OPCODE.ADD: self.add,
            OPCODE.CVR: self.cvr,
            OPCODE.DIV: self.div,
            OPCODE.DIVIDE: self.divide,
            OPCODE.DUMP: self.dump,
            OPCODE.EQL: self.eql,
            OPCODE.FADD: self.f_add,
            OPCODE.FDIVIDE: self.f_divide,
            OPCODE.FSUB: self.f_sub,
            OPCODE.GTE: self.gte,
            OPCODE.HALT: self.halt,
            OPCODE.JFALSE: self.jfalse,
            OPCODE.JMP: self.jmp,
            OPCODE.LES: self.les,
            OPCODE.LTE: self.lte,
            OPCODE.MULTIPLY: self.multiply,
            OPCODE.NEQ: self.neq,
            OPCODE.NEW_LINE: self.new_line,
            OPCODE.POP_CHAR: self.pop_char,
            OPCODE.POP_REAL_LIT: self.pop_real_lit,
            OPCODE.POP: self.pop,
            OPCODE.PRINT_B: self.print_b,
            OPCODE.PRINT_C: self.print_c,
            OPCODE.PRINT_I: self.print_i,
            OPCODE.PRINT_ILIT: self.print_ilit,
            OPCODE.PRINT_R: self.print_r,
            OPCODE.PRINT_STR_LIT: self.print_str_lit, 
            OPCODE.PUSH_CHAR: self.push_char,
            OPCODE.PUSH: self.push,
            OPCODE.PUSHI: self.pushi,
            OPCODE.RET_AND_PRINT: self.ret_and_print,
            OPCODE.RETRIEVE: self.retrieve,
            OPCODE.SUB: self.sub,
            OPCODE.XCHG: self.xchg,
        }

        op = self.bytes[self.ip]
        if op in operations:
            operations[op]()
            self.start()
        else:
            print(f'Stack {self.stack}')
            raise PascalError(f'Operation {op} is not supported')
    
    def immediate_value(self):
        immediate = bytearray()
        for i in range(4):
            immediate.append(self.bytes[self.ip])
            self.ip += 1
        
        return byte_unpacker(immediate)
    
    def immediate_data(self):
        return self.data[self.immediate_value()]
    
    def pop(self) -> int:
        self.ip += 1
        top_value = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data[self.pointer] = top_value
        self.pointer += 1
        return top_value
    
    def push(self) -> None:
        self.ip += 1
        imm = self.immediate_data()
        self.stack.append(imm)

    def pushi(self) -> None:
        self.ip += 1
        self.stack.append(self.immediate_value())    
    
    def jfalse(self) -> None:
        self.ip += 1
        if self.stack.pop():
            self.immediate_value()
        else:
            self.ip = self.immediate_value()
        
    def gte(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() <= self.stack.pop()
        self.stack.appned(new_top)
    
    def gtr(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() > self.stack.pop()
        self.stack.appned(new_top)
    
    def lte(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() >= self.stack.pop()
        self.stack.appned(new_top)
    
    def les(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() < self.stack.pop()
        self.stack.appned(new_top)
    
    def eql(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() == self.stack.pop()
        self.stack.appned(new_top)
    
    def neq(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() != self.stack.pop()
        self.stack.appned(new_top)

    def xchg(self) -> None:
        self.ip += 1
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def cvr(self) -> None:
        self.ip += 1
        self.stack.append(float(self.stack.pop()))

    def jmp(self) -> None:
        self.ip += 1
        self.ip = self.immediate_value()
    
    def pop_char(self):
        self.ip += 1
        top = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data[self.pointer] = top
        self.pointer += 1
        return top
    
    def push_char(self) -> None:
        self.ip += 1
        self.stack.append(chr(self.immediate_value()))

    def sub(self) -> None:
        self.ip += 1
        top = self.stack.pop()
        self.stack.append(self.stack.pop() - top)
    
    def add(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() + self.stack.pop()
        self.stack.append(new_top)

    def multiply(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() * self.stack.pop()
        self.stack.append(new_top)
    
    def divide(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() / self.stack.pop()
        self.stack.append(new_top)
    
    def div(self) -> None:
        self.ip += 1
        d = int(self.stack.pop())
        self.stack.append(int(self.stack.pop()) / d)
    
    def f_divide(self) -> None:
        self.ip += 1
        d = bits_to_float(self.stack.pop())
        new_top = self.stack.pop() / float(d)
        self.stack.append(new_top)
    
    def f_multiply(self) -> None:
        self.ip += 1
        new_top = float(self.stack.pop()) * float(self.stack.pop())
        self.stack.append(new_top)

    def f_add(self) -> None:
        self.ip += 1
        new_top = float(self.stack.pop()) + float(self.stack.pop())
        self.stack.append(new_top)
    
    def f_sub(self) -> None:
        self.ip += 1
        top = float(self.stack.pop())
        self.stack.append(float(self.stack.pop()) - top)

    def dump(self) -> None:
        self.ip += 1
        top = self.stack.pop()
        self.pointer = self.stack.pop()
        self.data[self.pointer] = top
        self.pointer += 1

    def retrieve(self) -> None:
        self.ip += 1
        self.pointer = self.stack.pop()
        self.stack.append(self.data[self.pointer])
    
    def print_ilit(self) -> None:
        self.ip += 1
        val = self.immediate_value()
        self.out.append(val)

    def pop_real_lit(self) -> None:
        self.ip += 1
        top = self.stack.pop()
        self.data[self.immediate_value()] = float('{0:.2f}'.format(bits_to_float(top)))

    def print_b(self) -> None:
        self.ip += 1
        val = 'true ' if self.immediate_data() == 1 else 'false'
        self.out.append(val)

    def print_c(self) -> None:
        self.ip += 1
        new_top = self.data[self.immediate_value()]
        self.out.append(new_top)

    def print_r(self) -> None:
        self.ip += 1
        self.out.append(self.immediate_data())

    def print_i(self) -> None:
        self.ip += 1
        self.out.append(self.immediate_data())

    def ret_and_print(self) -> None:
        self.ip += 1
        self.pointer = self.stack.pop()
        self.out.append(self.data[self.pointer])
    
    def print_str_lit(self) -> None:
        self.ip += 1
        str_len = self.stack.pop()
        text = ''

        for i in range(str_len):
            text += chr(self.bytes[self.ip])
            self.ip += 1
        
        self.out.append(text)

    def new_line(self) -> None:
        self.ip += 1
        self.out.append('\n')

    def flush(self) -> None:
        print('-' * 50 + 'Flushing' + '-' * 50)

        for item in self.out:
            print(item)

    def halt(self) -> None:
        print('Finishing simulating')
        self.flush()
        sys.exit()