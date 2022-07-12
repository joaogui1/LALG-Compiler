from loader.lalg_error import LalgError

LALG_FILE_EXT = '.lalg'

class LalgFile(object):
    ''' File Class - wrapper to deal with input file '''

    def __init__(self, input_file, output_file=None) -> None:
        ''' Initializes artibutes 
        
        Raises
        ------
        LalgError
            if file extension is wrong
        Other
            if there's any error opening the file
        '''
        
        self.FILE = None
        self.input_file = input_file
        self.output_file = output_file

        if not self.input_file.endswith(LALG_FILE_EXT):
            raise LalgError(f'Invalid file extension. Expected {LALG_FILE_EXT} and got .{input_file.split(".")[-1]}')

        try:
            self.FILE = open(self.input_file)
        except Exception as e:
            print(f'Could not open file - {e.args}')

        self.contents = self.FILE.read()
    
    def get_input_file(self) -> str:
        ''' Gets input file name '''
        return self.input_file

    def get_output_file(self) -> str:
        ''' Gets output file name '''
        return self.output_file

    def io_object(self) -> object:
        ''' Gets file as object '''
        return self.FILE
    
    def __repr__(self) -> str:
        ''' Creates a string representation of the class '''
        return self.input_file

    def __del__(self) -> None:
        ''' Class destructor to close file '''
        if self.FILE is not None:
            self.FILE.close()