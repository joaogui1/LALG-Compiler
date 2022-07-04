TYPE_VARIABLE = 'var' 
TYPE_FUNCTION = 'func'
TYPE_PROCEDURE = 'pro'
TYPE_EXPRESSIONS = 'expr'
TYPE_STATEMENTS = 'stat'
TYPE_PARAMETER = 'par'
TYPE_ARRAY = 'arr'

class SymbolObject(object):
    def __init__(self, name, object_type, data_type, dp=None, attribute=None, others=None) -> None:
        self.name = name
        self.object_type = object_type
        self.data_type = data_type
        self.dp = dp

        self.others = others if others is None else []

        if attribute is not None:
            for attr, value in attribute.iteritems():
                self.__setattr__(attr, value)

    
    def __unicode__(self) -> str:
        return f'{self.name}, {self.object_type}, {self.data_type}'
