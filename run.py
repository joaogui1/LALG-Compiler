from __future__ import absolute_import

import pprint

from tokenizer import get_token
from pascal_loader.main_io import PascalFile
from parse import Parser
from emulator import Emulator

if __name__ == '__main__':
    pp = pprint.PrettyPrinter()
    tokens = get_token(PascalFile(input_file='samples/arrays.pos'))
    parser = Parser(tokens=tokens)
    bytes = parser.parse()
    emulator = Emulates(bytes)
    emulator.start()