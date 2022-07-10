import argparse

from parse import Parser
from emulator import Emulator
from tokenizer import get_token
from loader.main_io import LalgFile

if __name__ == '__main__':
    # add argument parser
    parser = argparse.ArgumentParser()
    parser.add_argument('--input', '-i', type=str, required=True)
    parser.add_argument('--output', '-o', type=str)
    args = parser.parse_args()
    
    # uses LalgFile to read code
    print('Reading file...')
    tokens = get_token(LalgFile(input_file=args.input))

    # uses parser to parse tokens
    print('Parsing...')
    parser = Parser(tokens=tokens)
    byte_array = parser.parse()
    
    # uses bytes to execute the code
    print('Emulating...')
    emulator = Emulator(byte_array)
    emulator.start()