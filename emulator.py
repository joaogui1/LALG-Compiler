import sys
from helper import *
from constants import *
from pascal_loader import PascalError

class Emulator(object):
    def __init__(self, bytes) -> None:
        self.data_array = {}
        self.stack = []
        self.bytes = bytes
        self.out = []
        self.ip = 0
        self.pointer = 0

    def flush(self) -> None:
        print('Flushing...')
        for item in self.out:
            print(item, end='')

    def start(self):
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
            OPCODE['PRINT_B']: self.print_b,
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
        }

        op = self.bytes[self.ip]

        if op in operations:
            operations[op]()

            if op != OPCODE['HALT']:
                self.start()
        else:
            print(f'Stack {self.stack}')
            raise PascalError(f'Operation {op} is not supported')

    def pushi(self) -> None:
        self.ip += 1
        self.stack.append(self.immediate_value())

    def immediate_value(self) -> object:
        immediate = bytearray()

        for i in range(4):
            immediate.append(self.bytes[self.ip])
            self.ip += 1
        
        return byte_unpacker(immediate)

    def immediate_data(self) -> object:
        return self.data_array[self.immediate_value()]

    def pop(self) -> object:
        self.ip += 1
        popped_value = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = popped_value
        self.pointer += 1
        return popped_value

    def print_i(self) -> None:
        self.ip += 1
        self.out.append(self.immediate_data())

    def push(self) -> None:
        self.ip += 1
        imm = self.immediate_data()
        self.stack.append(imm)

    def print_new_line(self) -> None:
        self.ip += 1
        self.out.append('\n')

    def sub(self) -> None:
        self.ip += 1
        top = self.stack.pop()
        new_top = self.stack.pop() - top
        self.stack.append(new_top)

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
        denom = self.stack.pop()
        new_top = self.stack.pop() / float(denom)
        self.stack.append(new_top)
    
    def div(self):
        self.ip += 1
        denom = int(self.stack.pop())
        new_top = int(self.stack.pop()) / denom
        self.stack.append(new_top)

    def jfalse(self) -> None:
        self.ip += 1

        if self.stack.pop():
            self.immediate_value()
        else:
            imm = self.immediate_value()
            self.ip = imm

    def gte(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() <= self.stack.pop()
        self.stack.append(new_top)

    def gtr(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() > self.stack.pop()
        self.stack.append(new_top)

    def lte(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() >= self.stack.pop()
        self.stack.append(new_top)

    def les(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() < self.stack.pop()
        self.stack.append(new_top)

    def eql(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() == self.stack.pop()
        self.stack.append(new_top)

    def neq(self) -> None:
        self.ip += 1
        new_top = self.stack.pop() != self.stack.pop()
        self.stack.append(new_top)

    def xchg(self) -> None:
        self.ip += 1
        self.stack[-1], self.stack[-2] = self.stack[-2], self.stack[-1]

    def cvr(self) -> None:
        self.ip += 1
        new_top = float(self.stack.pop())
        self.stack.append(new_top)

    def jmp(self) -> None:
        self.ip += 1
        self.ip = self.immediate_value()

    def pop_char(self) -> object:
        self.ip += 1
        top = self.stack.pop()
        self.pointer = self.immediate_value()
        self.data_array[self.pointer] = top
        self.pointer += 1
        return top

    def push_char(self) -> None:
        self.ip += 1
        new_top = chr(self.immediate_value())
        self.stack.append(new_top)

    def f_divide(self) -> None:
        self.ip += 1
        denom = bits_to_float(self.stack.pop())
        new_top = self.stack.pop() / float(denom)
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
        new_top = float(self.stack.pop()) - top
        self.stack.append(new_top)

    def dump(self) -> None:
        self.ip += 1
        assignment = self.stack.pop()
        self.pointer = self.stack.pop()
        self.data_array[self.pointer] = assignment
        self.pointer += 1

    def retrieve(self) -> None:
        self.ip += 1
        self.pointer = self.stack.pop()
        self.stack.append(self.data_array[self.pointer])
    
    def print_c(self) -> None:
        self.ip += 1
        out_val = self.data_array[self.immediate_value()]
        self.out.append(out_val)

    def print_b(self) -> None:
        self.ip += 1
        boolean = self.immediate_data()
        out_val = 'true' if boolean == 1 else 'false'
        self.out.append(out_val)

    def print_r(self) -> None:
        self.ip += 1
        self.out.append(self.immediate_data())

    def print_ilit(self) -> None:
        self.ip += 1
        val = self.immediate_value()
        self.out.append(val)

    def ret_and_print(self) -> None:
        self.ip += 1
        self.pointer = self.stack.pop()
        out_val = self.data_array[self.pointer]
        self.out.append(out_val)

    def print_str_lit(self) -> None:
        self.ip += 1
        text_len = self.stack.pop()
        text = ''

        for _ in range(text_len):
            text += chr(self.bytes[self.ip])
            self.ip += 1
        
        self.out.append(text)
    
    def pop_real_lit(self) -> None:
        self.ip += 1
        top = self.stack.pop()
        new_val = float('{0:.2f}'.format(bits_to_float(top)))
        self.data_array[self.immediate_value()] = new_val
        self.pointer += 1
    
    def halt(self) -> None:
        print('Done!')
        self.flush()
        sys.exit()