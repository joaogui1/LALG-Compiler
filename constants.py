import ctypes

class OPCODE(object):
    ADD = 0
    CVR = 1
    DIV = 2
    DIVIDE = 3
    DUMP = 4
    DUP = 5
    EQL = 6
    FADD = 7
    FDIVIDE = 8
    FMULTIPLY = 9
    FSUB = 10
    GTE = 11
    GTR = 12
    HALT = 13
    JFALSE = 14
    JMP = 15
    JTRUE = 16
    LES = 17
    LTE = 18
    MULTIPLY = 19
    NEQ = 20
    NEW_LINE = 21
    NOT = 22
    OR = 23
    POP = 24
    POP_CHAR = 25
    POP_REAL_LIT = 26
    PRINT_B = 27
    PRINT_C = 28
    PRINT_I = 29
    PRINT_ILIT = 30
    PRINT_R = 31
    PRINT_STR_LIT = 32
    PUSH = 33
    PUSH_CHAR = 34
    PUSHI = 34
    RET_AND_PRINT = 36
    RETRIEVE = 37
    SUB = 38
    XCHG = 39

class TYPE(object):
    I, R, B, C, S = range(5)

CONDITIONALS = {
    '<': True,
    '<>': True,
    '<=': True,
    '>': True,
    '>=': True,
    '=': True,
}

INSTRUCTION_LENGTH = 5

def float_to_bits(val):
    return ctypes.c_int.from_address(ctypes.addressof(val)).value

def bits_to_float(val):
    return ctypes.c_int.from_buffer(ctypes.c_float(val)).value

def byte_unpacker(bytes):
    return (bytes[0] << 24) | (bytes[1] << 16) | (bytes[2] << 8) | (bytes[3])

def byte_packer(val):
    if not isinstance(val, int):
        val = float_to_bits((float(val)))

    return (val >> 24) & 0xFF, (val >> 16) & 0xFF, (
        val >> 8) & 0xFF, val & 0xFF