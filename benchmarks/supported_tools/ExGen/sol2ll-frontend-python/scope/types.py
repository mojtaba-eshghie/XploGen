import llvmlite.ir as ir
from scope.simbol_table import Symbol

BOOL = ir.IntType(1)
BYTE = ir.IntType(8)
i256 = ir.IntType(256)
address = ir.IntType(160)
str256 = ir.IntType(256)
SYSTEM_TYPES = (BOOL, BYTE, i256, address, str256, ir.LiteralStructType)

class MappingType(object):
    def __init__(self, KT, VT):
        self.keyType = KT
        self.valueType = VT
    
    def getLLVMType(self):
        if self.valueType in SYSTEM_TYPES:
            return self.valueType
        elif type(self.valueType) is Symbol:
            return self.valueType.pyType.getLLVMType()
        elif type(self.valueType) in (MappingType, ArrayType, StructType):
            return self.valueType.getLLVMType()
        elif type(self.valueType) is ContractType:
            return address
        else:
            return
    
    def getPyType(self):
        if type(self.valueType) is Symbol:
            return self.valueType.pyType
        else:
            return self.valueType

class ArrayType(object):
    def __init__(self, ET):
        self.length = 0
        self.elementType = ET
    
    def extractValue(self, index):
        # todo
        pass

    def getLLVMType(self):
        if self.elementType in SYSTEM_TYPES:
            return self.elementType
        elif type(self.elementType) is Symbol:
            return self.elementType.pyType.getLLVMType()
        elif type(self.elementType) in (MappingType, ArrayType, StructType):
            return self.elementType.getLLVMType()
        elif type(self.elementType) is ContractType:
            return address
        else:
            return
    
    def getPyType(self):
        if type(self.elementType) is Symbol:
            return self.elementType.pyType
        else:
            return self.elementType

class StructType(object):
    def __init__(self, EN, ET):
        self.elementNames = EN
        self.elementTypes = ET
    
    def iterList(self, t):
        if t in SYSTEM_TYPES:
            return t
        elif type(t) is Symbol:
            return self.iterList(t.pyType)
        elif type(t) is MappingType:
            return self.iterList(t.valueType)
        elif type(t) is ArrayType:
            return self.iterList(t.elementType)
        elif type(t) is StructType:
            return t.getLLVMType()
        elif type(t) is ContractType:
            return address
        else:
            return
    
    def getLLVMType(self):
        llType = []
        for eType in self.elementTypes:
            llType.append(self.iterList(eType))
        return ir.LiteralStructType(llType)
    
    def getPyType(self):
        self.elementTypes

class EnumType(object):
    def __init__(self, EN):
        self.elementNames = EN
    
    def getLLVMType(self):
        # todo
        pass

class ContractType(object):
    def __init__(self, name, addr):
        self.contract_name = name
        self.address = addr
        
    def getLLVMType(self):
        return address
