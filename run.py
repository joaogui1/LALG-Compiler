import argparse

from parse import Parser
from emulator import Emulator
from tokenizer import get_token
from pascal_loader.main_io import PascalFile

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=True)
    parser.add_argument('--output', '-o', type=str)
    args = parser.parse_args()
    
    print('Reading file...')
    tokens = get_token(PascalFile(input_file=args.input))

    print('Parsing...')
    parser = Parser(tokens=tokens)
    byte_array = parser.parse()
    print('Emulating...')
    emulator = Emulator(byte_array)
    emulator.start()