import os

FILE_EXT = 'pas'

class PascalFile(object):
    def __init__(self, input_file, output_file='') -> None:
        self.input_file = input_file
        self.output_file = output_file
        self.FILE = open(input_file)
        self.content = self.FILE.read()
    
    def get_input_file(self) -> str:
        return self.input_file

    def get_output_file(self) -> str:
        return self.output_file

    def io_object(self):
        return self.FILE
    
    def __unicode__(self):
        return self.input_file
    
    def __del__(self) -> None:
        self.FILE.close()
