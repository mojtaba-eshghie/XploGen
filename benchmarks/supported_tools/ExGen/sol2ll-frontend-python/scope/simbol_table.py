class Symbol(object):
    def __init__(self, name, pyType ,llType, addr):
        assert pyType is not None
        self.name = name
        self.pyType = pyType
        self.llType = llType
        self.addr = addr
            
class SymbolTable(object):
    def __init__(self):
        self.symbols = {}

    def append(self, sym):
        assert isinstance(sym, Symbol)
        self.symbols[sym.name] = sym

    def delete(self, name):
        del self.symbols[name]
    
    def update(self, name, sym):
        self.symbols[name] = sym
    
    def lookup(self, name):
        if name in self.symbols:
            return self.symbols[name]
        return None
