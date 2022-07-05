import os
import sys

PASCAL_FILE_EXT = '.pas'

class PascalFile(object):
    def __init__(self, input_file, output_file=None) -> None:
        self.input_file = input_file
        self.output_file = output_file

        try:
            self.FILE = open(self.input_file)
        except Exception as e:
            print(f'Could not open file - {e.args}')

        self.contents = self.FILE.read()
    
    def get_input_file(self) -> str:
        return self.input_file

    def get_output_file(self) -> str:
        return self.output_file

    def io_object(self) -> object:
        return self.FILE

    def __unicode__(self) -> str:
        return self.input_file
    
    def __repr__(self) -> str:
        return self.input_file

    def __del__(self) -> None:
        self.FILE.close()