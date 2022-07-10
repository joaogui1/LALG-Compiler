TYPE_ARRAY = 'arr'
TYPE_VARIABLE = 'var' 
TYPE_FUNCTION = 'func'
TYPE_PARAMETER = 'par'
TYPE_PROCEDURE = 'pro'
TYPE_STATEMENTS = 'stat'
TYPE_EXPRESSIONS = 'expr'

class SymbolObject(object):
    def __init__(self, name, object_type, data_type, dp=None, attribute=None, others=None) -> None:
        self.dp = dp
        self.name = name
        self.data_type = data_type
        self.object_type = object_type
        
        if attribute is not None:
            for attr, value in attribute.items():
                self.__setattr__(attr, value)
        
        if others is None:
            self.others = others
        else:
            self.others = []

    def __unicode__(self) -> str:
        return '<%s, %s, %i, %s>' % (self.name, self.object_type, self.dp, self.data_type)

    def __repr__(self) -> str:
        return '<%s, %s, %i, %s>' % (self.name, self.object_type, self.dp, self.data_type)
