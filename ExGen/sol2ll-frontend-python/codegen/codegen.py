# -*- coding:utf-8 -*-

import time
import llvmlite.ir as ir
from solidity_parser import parser
from solidity_parser.parser import AstVisitor
from scope.simbol_table import Symbol, SymbolTable
from scope.types import MappingType, ArrayType, StructType, EnumType, ContractType

# Solidity Types
BOOL = ir.IntType(1)
BYTE = ir.IntType(8)
i256 = ir.IntType(256)
address = ir.IntType(160)
str256 = ir.IntType(256)
BUILT_IN_TYPES = (BOOL, BYTE, i256, address, str256)
SYSTEM_TYPES = (BOOL, BYTE, i256, address, str256, ir.LiteralStructType)

class LLVMCodeGenerator(AstVisitor):
    def __init__(self, filepath):
        self.ast = parser.parse_file(filepath)
        self.obj = parser.objectify(self.ast)
        self.modules = {}
        self.module = None
        self.builder = None
        self.contract = None
        self.function = None
        self.loop_cur_blocks = []
        self.loop_end_blocks = []
        self.symbol_table = SymbolTable()
    
    def _alloca(self, name, type):
        with self.builder.goto_entry_block():
            alloca = self.builder.alloca(type, size=None, name=name)
        return alloca

    def generate_code(self):
        self._codegen(self.ast)
    
    def print_ir(self):
        for key in self.modules:
            print(self.modules[key])

    def _codegen(self, node):
        if node == ";" or node == None:
            return self._codegen_Throw(node)
        else:
            if node.type == "InLineAssemblyStatement":
                # TODO: Currently embedded assembly is not supported
                return
            method = '_codegen_' + node.type
            return getattr(self, method)(node)
    
    def _codegen_SourceUnit(self, node):
        for child in node.children:
            self._codegen(child)
    
    def _codegen_PragmaDirective(self, node):
        # TODO: Add assertion that given Solidity contracts can be compiled by solc-v0.4.24
        pass

    def _codegen_ImportDirective(self, node):
        # TODO: Currently inherited or library contract is not supported
        pass
    
    def _codegen_StateVariableDeclaration(self, node):
        pass
    
    def _codegen_StructDefinition(self, node):
        pass

    def _codegen_EnumDefinition(self, node):
        pass

    def _codegen_EventDefinition(self, node):
        pass

    def _codegen_ContractDefinition(self, root):
        self.contract = root.name
        self.module = ir.Module(name=self.contract)
        self.module.triple = "x86_64-unknown-linux-gnu"
        self.module.data_layout = "e-m:e-i64:64-f80:128-n8:16:32:64-S128"
        self.modules[self.contract] = self.module

        if not self.symbol_table.lookup("arithmetic_result"):
            # This variable is used for temporarily storing arithmetic results
            arithmetic_result = ir.GlobalVariable(self.module, i256, "arithmetic_result")
            arithmetic_result.initializer = i256(0)
            self.symbol_table.append(Symbol("arithmetic_result", int, i256, arithmetic_result))

            # Initialize msg.sender as global variables
            msg_sender_balance = ir.GlobalVariable(self.module, i256, "msg_sender_balance")
            msg_sender_balance.initializer = i256(0)
            self.symbol_table.append(Symbol("msg_sender_balance", int, i256, msg_sender_balance))

            # Initialize msg.value as global variables
            msg_value = ir.GlobalVariable(self.module, i256, "msg_value")
            msg_value.initializer = i256(0)
            self.symbol_table.append(Symbol("msg_value", int, i256, msg_value))

            # Declare built-in functions call.value
            fnty = ir.FunctionType(i256, [])
            func = ir.Function(self.module, fnty, name="call.value")
            block = func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            self.builder.ret(i256(0))

            # Declare built-in functions call.gas
            fnty = ir.FunctionType(i256, [])
            func = ir.Function(self.module, fnty, name="call.gas")
            block = func.append_basic_block(name="entry")
            self.builder = ir.IRBuilder(block)
            self.builder.ret(i256(0))

        # pre-compile
        for node in root.subNodes:
            # Go through the AST for user-defined types such as struct or enum
            if node.type == "StructDefinition":
                struct_name = node.name
                member_names = []
                member_types = []
                for member in node.members:
                    (member_name, member_type) = self._codegen(member)
                    member_names.append(member_name)
                    member_types.append(member_type)
                pyType = StructType(member_names, member_types)
                self.symbol_table.append(Symbol(struct_name, pyType, pyType.getLLVMType(), None))
            elif node.type == "EnumDefinition":
                enum_name = node.name
                member_names = []
                for i in range(0, len(node.members)):
                    member_name = node.members[i].name
                    member_names.append(member_name)
                pyType = EnumType(member_names)
                self.symbol_table.append(Symbol(enum_name, pyType, pyType.getLLVMType(), None))
            else:
                pass
        for node in root.subNodes:
            if node.type == "StateVariableDeclaration":
                (var_name, var_type) = self._codegen(node.variables[0])
                var_name = "global_%s_%s" % (self.contract, var_name)
                if var_type in BUILT_IN_TYPES:
                    var_addr = ir.GlobalVariable(self.module, var_type, var_name)
                    var_addr.initializer = var_type(1)
                    """
                    if node.initialValue:
                        var_value = self._codegen(node.initialValue)
                        if type(var_value) is Symbol:
                            var_value = self.builder.load(var_value.addr, name='initialValue')
                        else:
                            try:
                                var_value = self.builder.load(var_value, name='initialValue')
                            except:
                                var_value = var_value
                        if var_type != var_value.type:
                            var_type = var_value.type
                        var_addr = ir.GlobalVariable(self.module, var_type, var_name)
                        var_addr.initializer = var_value
                    else:
                        var_addr = ir.GlobalVariable(self.module, var_type, var_name)
                        var_addr.initializer = var_type(0)
                    """
                    self.symbol_table.append(Symbol(var_name, int, var_type, var_addr))
                elif type(var_type) is MappingType:
                    var_addr = ir.GlobalVariable(self.module, var_type.getLLVMType(), var_name)
                    self.symbol_table.append(Symbol(var_name, var_type, var_addr.type, var_addr))
                elif type(var_type) is ArrayType:
                    var_addr = ir.GlobalVariable(self.module, var_type.getLLVMType(), var_name)
                    self.symbol_table.append(Symbol(var_name, var_type, var_addr.type, var_addr))
                elif type(var_type) is ContractType:
                    var_addr = ir.GlobalVariable(self.module, var_type.getLLVMType(), var_name)
                    self.symbol_table.append(Symbol(var_name, var_type, var_addr.type, var_addr))
                elif type(var_type) is Symbol:
                    if type(var_type.pyType) is StructType:
                        var_addr = ir.GlobalVariable(self.module, var_type.llType, var_name)
                        self.symbol_table.append(Symbol(var_name, var_type.pyType, var_type.llType, var_addr))
                    elif type(var_type.pyType) is EnumType:
                        var_addr = ir.GlobalVariable(self.module, i256, var_name)
                        self.symbol_table.append(Symbol(var_name, var_type.pyType, i256, var_addr))
                    elif type(var_type.pyType) is ContractType:
                        var_addr = ir.GlobalVariable(self.module, address, var_name)
                        self.symbol_table.append(Symbol(var_name, var_type.pyType, address, var_addr))
                    else:
                        var_addr = ir.GlobalVariable(self.module, i256, var_name)
                        self.symbol_table.append(Symbol(var_name, int, i256, var_addr))
                else:
                    var_addr = ir.GlobalVariable(self.module, i256, var_name)
                    self.symbol_table.append(Symbol(var_name, int, i256, var_addr))
            elif node.type == "EventDefinition":
                # Solidity events are usually used for logging (no security issues)
                # We define events as functions with empty body
                (arg_names, arg_types) = self._codegen(node.parameters)

                arg_llTypes = []
                for i in range(0, len(arg_names)):
                    if arg_types[i] in BUILT_IN_TYPES:
                        arg_llTypes.append(arg_types[i])
                    elif type(arg_types[i]) is MappingType:
                        arg_llTypes.append(arg_types[i].getLLVMType())
                    elif type(arg_types[i]) is ArrayType:
                        arg_llTypes.append(arg_types[i].getLLVMType())
                    elif type(arg_types[i]) is Symbol:
                        if type(arg_types[i].pyType) is StructType:
                            arg_llTypes.append(arg_types[i].llType)
                        elif type(arg_types[i].pyType) is EnumType:
                            arg_llTypes.append(i256)
                        elif type(arg_types[i].pyType) is ContractType:
                            arg_llTypes.append(address)
                        else:
                            arg_llTypes.append(i256)
                    else:
                        arg_llTypes.append(i256)

                event_name = self.contract + "_Func_" + node.name + str(hash(str(arg_llTypes)))[1:7]

                for i in range(0, len(arg_names)):
                    arg_names[i] = "funcArg_%s_%s" % (event_name, arg_names[i])
                    if arg_types[i] in BUILT_IN_TYPES:
                        self.symbol_table.append(Symbol(arg_names[i], int, arg_types[i], None))
                    elif type(arg_types[i]) is MappingType:
                        self.symbol_table.append(Symbol(arg_names[i], arg_types[i], arg_types[i].getLLVMType(), None))
                    elif type(arg_types[i]) is ArrayType:
                        self.symbol_table.append(Symbol(arg_names[i], arg_types[i], arg_types[i].getLLVMType(), None))
                    elif type(arg_types[i]) is Symbol:
                        if type(arg_types[i].pyType) is StructType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, arg_types[i].llType, None))
                        elif type(arg_types[i].pyType) is EnumType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, i256, None))
                        elif type(arg_types[i].pyType) is ContractType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, address, None))
                        else:
                            self.symbol_table.append(Symbol(arg_names[i], int, i256, None))
                    else:
                        self.symbol_table.append(Symbol(arg_names[i], int, i256, None))

                fnty = ir.FunctionType(i256, tuple(arg_llTypes))
                func = ir.Function(self.module, fnty, name=event_name)                
                block = func.append_basic_block(name="entry")
                self.builder = ir.IRBuilder(block)
                for i in range(0, len(arg_names)):
                    arg_name = arg_names[i]
                    arg_type = arg_llTypes[i]
                    alloca = self._alloca(arg_name, arg_type)
                    self.builder.store(func.args[i], alloca)
                self.builder.ret(i256(0))
            elif node.type == "FunctionDefinition":
                # For the first AST iteration, we only handle function parameters and return type
                (arg_names, arg_types) = self._codegen(node.parameters)

                arg_llTypes = []
                for i in range(0, len(arg_names)):
                    if arg_types[i] in BUILT_IN_TYPES:
                        arg_llTypes.append(arg_types[i])
                    elif type(arg_types[i]) is MappingType:
                        arg_llTypes.append(arg_types[i].getLLVMType())
                    elif type(arg_types[i]) is ArrayType:
                        arg_llTypes.append(arg_types[i].getLLVMType())
                    elif type(arg_types[i]) is Symbol:
                        if type(arg_types[i].pyType) is StructType:
                            arg_llTypes.append(arg_types[i].llType)
                        elif type(arg_types[i].pyType) is EnumType:
                            arg_llTypes.append(i256)
                        elif type(arg_types[i].pyType) is ContractType:
                            arg_llTypes.append(address)
                        else:
                            arg_llTypes.append(i256)
                    else:
                        arg_llTypes.append(i256)
                
                if node.isConstructor:
                    self.function = self.contract + "_Constructor"
                else:
                    self.function = self.contract + "_Func_" + node.name + str(hash(str(arg_llTypes)))[1:7]

                for i in range(0, len(arg_names)):
                    arg_names[i] = "funcArg_%s_%s" % (self.function, arg_names[i])
                    if arg_types[i] in BUILT_IN_TYPES:
                        self.symbol_table.append(Symbol(arg_names[i], int, arg_types[i], None))
                    elif type(arg_types[i]) is MappingType:
                        self.symbol_table.append(Symbol(arg_names[i], arg_types[i], arg_types[i].getLLVMType(), None))
                    elif type(arg_types[i]) is ArrayType:
                        self.symbol_table.append(Symbol(arg_names[i], arg_types[i], arg_types[i].getLLVMType(), None))
                    elif type(arg_types[i]) is Symbol:
                        if type(arg_types[i].pyType) is StructType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, arg_types[i].llType, None))
                        elif type(arg_types[i].pyType) is EnumType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, i256, None))
                        elif type(arg_types[i].pyType) is ContractType:
                            self.symbol_table.append(Symbol(arg_names[i], arg_types[i].pyType, address, None))
                        else:
                            self.symbol_table.append(Symbol(arg_names[i], int, i256, None))
                    else:
                        self.symbol_table.append(Symbol(arg_names[i], int, i256, None))

                ret_llType = None
                if node.returnParameters:
                    if len(node.returnParameters.parameters) > 1:
                        ret_names = []
                        ret_types = []
                        for param in node.returnParameters.parameters:
                            (ret_name, ret_type) = self._codegen(param)
                            ret_name = "funcArg_%s_%s" % (self.function, ret_name)
                            ret_names.append(ret_name)
                            if ret_type in BUILT_IN_TYPES:
                                ret_types.append(ret_type)
                            elif type(ret_type) is MappingType:
                                ret_types.append(ret_type.getLLVMType())
                            elif type(ret_type) is ArrayType:
                                ret_types.append(ret_type.getLLVMType())
                            elif type(ret_type) is Symbol:
                                if type(ret_type.pyType) is StructType:
                                    ret_types.append(ret_type.llType)
                                elif type(ret_type.pyType) is EnumType:
                                    ret_types.append(i256)
                                elif type(ret_type.pyType) is ContractType:
                                    ret_types.append(address)
                                else:
                                    ret_types.append(i256)
                            else:
                                ret_types.append(i256)
                        ret_name = "funcArg_%s_%s" % (self.function, "retParam")
                        ret_type = StructType(ret_names, ret_types)
                        ret_llType = ret_type.getLLVMType()
                        self.symbol_table.append(Symbol(ret_name, ret_type, ret_llType, None))
                    else:
                        (ret_name, ret_type) = self._codegen(node.returnParameters.parameters[0])
                        if ret_name:
                            ret_name = "funcArg_%s_%s" % (self.function, ret_name)
                        else:
                            ret_name = "funcArg_%s_%s" % (self.function, "retParam")
                        if ret_type in BUILT_IN_TYPES:
                            ret_llType = ret_type
                            self.symbol_table.append(Symbol(ret_name, int, ret_llType, None))
                        elif type(ret_type) is MappingType:
                            ret_llType = ret_type.getLLVMType()
                            self.symbol_table.append(Symbol(ret_name, ret_type, ret_llType, None))
                        elif type(ret_type) is ArrayType:
                            ret_llType = ret_type.getLLVMType()
                            self.symbol_table.append(Symbol(ret_name, ret_type, ret_llType, None))
                        elif type(ret_type) is Symbol:
                            if type(ret_type.pyType) is StructType:
                                ret_llType = ret_type.llType
                                self.symbol_table.append(Symbol(ret_name, ret_type.pyType, ret_llType, None))
                            elif type(ret_type.pyType) is EnumType:
                                ret_llType = i256
                                self.symbol_table.append(Symbol(ret_name, ret_type.pyType, ret_llType, None))
                            elif type(ret_type.pyType) is ContractType:
                                ret_llType = address
                                self.symbol_table.append(Symbol(ret_name, ret_type.pyType, ret_llType, None))
                            else:
                                ret_llType = i256
                                self.symbol_table.append(Symbol(ret_name, int, ret_llType, None))
                        else:
                            ret_llType = i256
                            self.symbol_table.append(Symbol(ret_name, int, ret_llType, None))
                            
                else:
                    ret_name = "funcArg_%s_%s" % (self.function, "retParam")
                    ret_llType = i256
                    self.symbol_table.append(Symbol(ret_name, int, ret_llType, None))
                
                fnty = ir.FunctionType(ret_llType, tuple(arg_llTypes))
                func = ir.Function(self.module, fnty, name=self.function)
            else:
                pass

        # code generation
        for node in root.subNodes:
            if node.type == "FunctionDefinition":
                self._codegen(node)

    # ====== code generator for Type System

    def _codegen_EnumValue(self, node):
        return node.name
    
    def _codegen_BooleanLiteral(self, node):
        if node.value:
            return BOOL(1)
        return BOOL(0)
    
    def _codegen_StringLiteral(self, node):
        if node.value.startswith("0x"):
            return address(int(hash(str(node.value))))
        return str256(int(hash(str(node.value))))
    
    def _codegen_NumberLiteral(self, node):
        if node.number == "0x0":
            return address(0)
        if node.number.startswith("0x"):
            return address(int(hash(str(node.value))))
        if node.subdenomination and node.subdenomination.lower() == 'ether':
            # TODO: This conversion is not fully implemented
            return i256(int(float(node.number) * (10 ** 18)))
        return i256(int(node.number))
    
    def _codegen_ElementaryTypeNameExpression(self, node):
        return self._codegen(node.typeName)

    def _codegen_ElementaryTypeName(self, node):
        solidity_type = node.name
        if solidity_type.lower().find("bool") != -1:
            return BOOL
        elif solidity_type.lower().find("byte") != -1:
            return BYTE
        elif solidity_type.lower().find("int") != -1:
            return i256
        elif solidity_type.lower().find("address") != -1:
            return address
        elif solidity_type.lower().find("string") != -1:
            return str256
        else:
            return i256
    
    def _codegen_NewExpression(self, node):
        return self._codegen(node.typeName)

    def _codegen_UserDefinedTypeName(self, node):
        user_defined_type_name = node.namePath
        sym = self.symbol_table.lookup(user_defined_type_name)
        if sym:
            return sym
        elif user_defined_type_name in self.modules:
            return ContractType(user_defined_type_name, address(0))
        else:
            return user_defined_type_name
    
    def _codegen_Mapping(self, node):
        keyType = self._codegen(node.keyType)
        valueType = self._codegen(node.valueType)
        return MappingType(keyType, valueType)

    def _codegen_ArrayTypeName(self, node):
        baseTypeName = self._codegen(node.baseTypeName)
        return ArrayType(baseTypeName)
    
    def _codegen_TupleExpression(self, node):
        if not node.isArray:
            return self._codegen(node.components[0])
        else:
            # TODO: Currently arrays with initial values are not supported
            pass

    def _codegen_MemberAccess(self, node):
        # TODO: Getters and Setters are not fully implemented for aggregate types
        member_name = node.memberName
        aggregate = self._codegen(node.expression)

        if member_name in ("balance", "number", "length"):
            # TODO: address.balance, block.number and array.length are not implemented
            return i256(0)
        if member_name == "value":
            if aggregate == "call":
                return "call.value"
            else:
                return self.symbol_table.lookup("msg_value").addr
        if member_name in ("sender", "origin"):
            return address(0)
        if member_name == "data":
            # TODO: Initialize msg.data as global variable
            return i256("msg.data")
        if member_name == "timestamp":
            return i256(int(time.time()))
        if member_name == "gas":
            if aggregate == "call":
                return "call.gas"
            else:
                return i256(2300)
        if member_name in ("call", "callcode", "delegatecall", "blockhash", "balanceOf", "send", "transfer", "push", "pop"):
            return member_name
        
        if type(aggregate) is Symbol and type(aggregate.pyType) is StructType:
            aggr_value = self.builder.load(aggregate.addr, name='aggrValue')
            member_index = aggregate.pyType.elementNames.index(member_name)
            member_type = aggregate.pyType.elementTypes[member_index]
            member_value = self.builder.extract_value(aggr_value, member_index, name="ExtractValue_" + member_name)
            if member_type in SYSTEM_TYPES:
                member_addr = self._alloca("ExtractValue_" + member_name, member_type)
                self.builder.store(member_value, member_addr)
                return Symbol("ExtractValue_" + member_name, member_type, member_type, member_addr)
            else:
                member_addr = self._alloca("ExtractValue_" + member_name, member_type.getLLVMType())
                self.builder.store(member_value, member_addr)
                return Symbol("ExtractValue_" + member_name, member_type.getPyType(), member_type.getLLVMType(), member_addr)

        if type(aggregate) is str and type(self.symbol_table.lookup(aggregate)) is Symbol:
            sym = self.symbol_table.lookup(aggregate)
            if type(sym.pyType) is EnumType:
                member_index = sym.pyType.elementNames.index(member_name)
                return i256(member_index)
        
        if type(aggregate) is Symbol and type(aggregate.pyType) is ContractType:
            return (aggregate, member_name)
        
        return aggregate

    def _codegen_IndexAccess(self, node):
        # TODO: Getters and Setters are not fully implemented for aggregate types
        index = self._codegen(node.index)
        aggregate = self._codegen(node.base)
        if type(aggregate) is Symbol and type(aggregate.pyType) in (MappingType, ArrayType):
            return Symbol(aggregate.name, aggregate.pyType.getPyType(), aggregate.llType, aggregate.addr)
        return aggregate

    # ====== code generator for terminal keywords

    def _codegen_Continue(self, node):
        self.builder.branch(self.loop_cur_blocks[-1])
        return

    def _codegen_Break(self, node):
        self.builder.branch(self.loop_end_blocks[-1])
        return

    def _codegen_Return(self, node):
        pass

    def _codegen_Throw(self, node):
        ret_type = self.module.globals.get(self.function).return_value.type
        self.builder.ret(ret_type(-1))
        return
    
    # ====== code generator for Function Body

    def _codegen_Block(self, node):
        ret_value = None
        for statement in node.statements:
            if statement:
                ret_value = self._codegen(statement)
        return ret_value
    
    def _codegen_ExpressionStatement(self, node):
        return self._codegen(node.expression)
    
    def _codegen_EmitStatement(self, node):
        return self._codegen(node.eventCall)
    
    def _codegen_Identifier(self, node):        
        identifier = node.name
        if identifier.find("this") != -1:
            return address(0)
        elif identifier.find("now") != -1:
            alloca = self._alloca("now", i256)
            self.builder.store(i256(int(time.time())), alloca)
            return self.builder.load(alloca, name='now')
        elif identifier in ("require", "assert", "keccak256", "ecrecover"):
            # TODO: Digital signature functions, e.g. keccak256 and ecrecover, are not supported
            return identifier
        else:
            funcArg = self.symbol_table.lookup("funcArg_%s_%s" % (self.function, identifier))
            globalVar = self.symbol_table.lookup("global_%s_%s" % (self.contract, identifier))
            if funcArg:
                return funcArg
            elif globalVar:
                return globalVar
            else:
                for contract_name in self.modules:
                    scopeGlobalVar = self.symbol_table.lookup("global_%s_%s" % (contract_name, identifier))
                    if scopeGlobalVar:
                        return scopeGlobalVar
                return identifier
    
    def _codegen_VariableDeclarationStatement(self, node):            
        if len(node.variables) > 1 and node.initialValue and node.initialValue.type == "FunctionCall":
            variable_values = self._codegen(node.initialValue)
            for i in range(0, len(node.variables)):
                var_name = node.variables[i].name
                var_name = "funcArg_%s_%s" % (self.function, var_name)
                var_value = self.builder.extract_value(variable_values, i)
                var_type = var_value.type
                alloca = self._alloca(var_name, var_type)
                self.builder.store(var_value, alloca)
                self.symbol_table.append(Symbol(var_name, var_type, alloca.type, alloca))
            return

        (var_name, var_type) = self._codegen(node.variables[0])
        var_name = "funcArg_%s_%s" % (self.function, var_name)

        if var_type in BUILT_IN_TYPES:
            if node.initialValue:
                var_value = self._codegen(node.initialValue)
                if type(var_value) is Symbol:
                    var_value = self.builder.load(var_value.addr, name='initialValue')
                else:
                    try:
                        var_value = self.builder.load(var_value, name='initialValue')
                    except:
                        var_value = var_value
                if var_type != var_value.type:
                    var_type = var_value.type
                alloca = self._alloca(var_name, var_type)
                self.builder.store(var_value, alloca)
            else:
                alloca = self._alloca(var_name, var_type)
                self.builder.store(var_type(0), alloca)
            self.symbol_table.append(Symbol(var_name, int, var_type, alloca))
        elif type(var_type) is MappingType:
            alloca = self._alloca(var_name, var_type.getLLVMType())
            self.symbol_table.append(Symbol(var_name, var_type, alloca.type, alloca))
        elif type(var_type) is ArrayType:
            alloca = self._alloca(var_name, var_type.getLLVMType())
            self.symbol_table.append(Symbol(var_name, var_type, alloca.type, alloca))
        elif type(var_type) is ContractType:
            alloca = self._alloca(var_name, var_type.getLLVMType())
            self.symbol_table.append(Symbol(var_name, var_type, alloca.type, alloca))
        elif type(var_type) is Symbol:
            if type(var_type.pyType) is StructType:
                alloca = self._alloca(var_name, var_type.llType)
                self.symbol_table.append(Symbol(var_name, var_type.pyType, var_type.llType, alloca))
            elif type(var_type.pyType) is EnumType:
                alloca = self._alloca(var_name, i256)
                self.symbol_table.append(Symbol(var_name, var_type.pyType, i256, alloca))
            elif type(var_type.pyType) is ContractType:
                alloca = self._alloca(var_name, address)
                self.symbol_table.append(Symbol(var_name, var_type.pyType, address, alloca))
            else:
                alloca = self._alloca(var_name, i256)
                self.symbol_table.append(Symbol(var_name, int, i256, alloca))
        else:
            alloca = self._alloca(var_name, i256)
            self.symbol_table.append(Symbol(var_name, int, i256, alloca))

    def _codegen_VariableDeclaration(self, node):
        if node.name:
            var_name = node.name
        elif node.storageLocation:
            var_name = node.storageLocation
        else:
            var_name = None
        var_type = self._codegen(node.typeName)
        return (var_name, var_type)

    def _codegen_BinaryOperation(self, node):
        '''
          | Expression '**' Expression
          | Expression ('*' | '/' | '%') Expression
          | Expression ('+' | '-') Expression
          | Expression ('<<' | '>>') Expression
          | Expression '&' Expression
          | Expression '^' Expression
          | Expression '|' Expression
          | Expression ('<' | '>' | '<=' | '>=') Expression
          | Expression ('==' | '!=') Expression
          | Expression '&&' Expression
          | Expression '||' Expression
          | Expression ('=' | '|=' | '^=' | '&=' | '<<=' | '>>=' | '+=' | '-=' | '*=' | '/=' | '%=') Expression
        '''
        # TODO: Type inference is not fully implemented, sometimes the types of operands don't match with each other
        operator = node.operator
        left_operand = self._codegen(node.left)
        right_operand = self._codegen(node.right)

        if operator == "=" and type(right_operand) is Symbol and type(right_operand.pyType) is ContractType:
            self.builder.store(right_operand.pyType.address, left_operand.addr)
            self.symbol_table.update(left_operand.name, Symbol(left_operand.name, right_operand.pyType, address, left_operand.addr))
            return

        if type(left_operand) is Symbol:
            left_value = self.builder.load(left_operand.addr, name='leftOpValue')
        else:
            try:
                left_value = self.builder.load(left_operand, name='leftOpValue')
            except:
                left_value = left_operand
        if type(right_operand) is Symbol:
            right_value = self.builder.load(right_operand.addr, name='rightOpValue')
        else:
            try:
                right_value = self.builder.load(right_operand, name='rightOpValue')
            except:
                right_value = right_operand

        arithmetic_result = self.symbol_table.lookup("arithmetic_result").addr

        if operator == '=':
            assign_value = right_value
        elif operator == '|=':
            assign_value = self.builder.or_(left_value, right_value, 'assign_value')
        elif operator == '^=':
            assign_value = self.builder.xor(left_value, right_value, 'assign_value')
        elif operator == '&=':
            assign_value = self.builder.and_(left_value, right_value, 'assign_value')
        elif operator == '<<=':
            assign_value = self.builder.shl(left_value, right_value, 'assign_value')
        elif operator == '>>=':
            assign_value = self.builder.ashr(left_value, right_value, 'assign_value')
        elif operator == '+=':
            assign_value = self.builder.add(left_value, right_value, 'assign_value')
        elif operator == '-=':
            assign_value = self.builder.sub(left_value, right_value, 'assign_value')
        elif operator == '*=':
            assign_value = self.builder.mul(left_value, right_value, 'assign_value')
        elif operator == '/=':
            assign_value = self.builder.sdiv(left_value, right_value, 'assign_value')
        elif operator == '%=':
            assign_value = self.builder.urem(left_value, right_value, 'assign_value')
        elif operator == '**':
            return self.builder.mul(left_value, right_value, 'intMul')
        elif operator == '*':
            return self.builder.mul(left_value, right_value, 'intMul')
        elif operator == '/':
            return self.builder.sdiv(left_value, right_value, 'intDiv')
        elif operator == '%':
            return self.builder.urem(left_value, right_value, 'intRemainder')
        elif operator == '+':
            return self.builder.add(left_value, right_value, 'intAdd')
        elif operator == '-':
            return self.builder.sub(left_value, right_value, 'intSub')
        elif operator == '<<':
            return self.builder.shl(left_value, right_value, 'leftShift')
        elif operator == '>>':
            return self.builder.ashr(left_value, right_value, 'rightShift')
        elif operator == '&':
            return self.builder.and_(left_value, right_value, 'bitAND')
        elif operator == '^':
            return self.builder.xor(left_value, right_value, 'bitXOR')
        elif operator == '|':
            return self.builder.or_(left_value, right_value, 'bitOR')
        elif operator in ('<', '<=', '>', '>=', '==', '!='):
            if left_value.type != right_value.type:
                if type(left_value) is ir.Constant:
                    left_value = right_value.type(left_value.constant)
                elif type(right_value) is ir.Constant:
                    right_value = left_value.type(right_value.constant)
                else:
                    right_value = self.builder.zext(right_value, left_value.type, name='rightOpValue')
            cmp = self.builder.zext(self.builder.icmp_unsigned(operator, left_value, right_value, 'cmpOP'), i256, name='zextInst')
            return cmp
        elif operator == '&&':
            logic_and_bb = ir.Block(self.builder.function, "logicAndStart")
            left_bb = ir.Block(self.builder.function, "leftValue")
            right_bb = ir.Block(self.builder.function, "rightValue")
            not_null_bb = ir.Block(self.builder.function, "notNull")
            null_bb = ir.Block(self.builder.function, "null")
            merge_bb = ir.Block(self.builder.function, "endLogicAnd")

            self.builder.branch(logic_and_bb)

            self.builder.function.basic_blocks.append(logic_and_bb)
            self.builder.position_at_end(logic_and_bb)
            self.builder.branch(left_bb)

            self.builder.function.basic_blocks.append(left_bb)
            self.builder.position_at_end(left_bb)
            cmp = self.builder.icmp_unsigned('==', left_value, left_value.type(0), name='icmpEqual')
            self.builder.cbranch(cmp, null_bb, right_bb)

            self.builder.function.basic_blocks.append(right_bb)
            self.builder.position_at_end(right_bb)
            cmp = self.builder.icmp_unsigned('==', right_value, right_value.type(0), name='icmpEqual')
            self.builder.cbranch(cmp, null_bb, not_null_bb)

            self.builder.function.basic_blocks.append(null_bb)
            self.builder.position_at_end(null_bb)
            self.builder.store(i256(0), arithmetic_result)
            self.builder.branch(merge_bb)

            self.builder.function.basic_blocks.append(not_null_bb)
            self.builder.position_at_end(not_null_bb)
            self.builder.store(i256(1), arithmetic_result)
            self.builder.branch(merge_bb)

            self.builder.function.basic_blocks.append(merge_bb)
            self.builder.position_at_end(merge_bb)
            return self.builder.load(arithmetic_result, name='arithmetic_result')
        elif operator == '||':
            logic_or_bb = ir.Block(self.builder.function, "logicOrStart")
            left_bb = ir.Block(self.builder.function, "leftValue")
            right_bb = ir.Block(self.builder.function, "rightValue")
            not_null_bb = ir.Block(self.builder.function, "notNull")
            null_bb = ir.Block(self.builder.function, "null")
            merge_bb = ir.Block(self.builder.function, "endLogicOr")

            self.builder.branch(logic_or_bb)

            self.builder.function.basic_blocks.append(logic_or_bb)
            self.builder.position_at_end(logic_or_bb)
            self.builder.branch(left_bb)

            self.builder.function.basic_blocks.append(left_bb)
            self.builder.position_at_end(left_bb)
            cmp = self.builder.icmp_unsigned('==', left_value, left_value.type(0), name='icmpEqual')
            self.builder.cbranch(cmp, right_bb, not_null_bb)

            self.builder.function.basic_blocks.append(right_bb)
            self.builder.position_at_end(right_bb)
            cmp = self.builder.icmp_unsigned('==', right_value, right_value.type(0), name='icmpEqual')
            self.builder.cbranch(cmp, null_bb, not_null_bb)

            self.builder.function.basic_blocks.append(null_bb)
            self.builder.position_at_end(null_bb)
            self.builder.store(i256(0), arithmetic_result)
            self.builder.branch(merge_bb)

            self.builder.function.basic_blocks.append(not_null_bb)
            self.builder.position_at_end(not_null_bb)
            self.builder.store(i256(1), arithmetic_result)
            self.builder.branch(merge_bb)

            self.builder.function.basic_blocks.append(merge_bb)
            self.builder.position_at_end(merge_bb)
            return self.builder.load(arithmetic_result, name='arithmetic_result')
        else:
            return

        try:
            if type(assign_value) is Symbol:
                assign_value = self.builder.load(assign_value.addr, name='assignValue')
            else:
                try:
                    assign_value = self.builder.load(assign_value, name='assignValue')
                except:
                    assign_value = assign_value
            self.builder.store(assign_value, left_operand.addr)
            return
        except:
            return

    def _codegen_UnaryOperation(self, node):
        # TODO: Type inference is not fully implemented
        is_prefix = node.isPrefix
        unary_operator = node.operator
        unary_operand = self._codegen(node.subExpression)

        if type(unary_operand) is Symbol:
            unary_value = self.builder.load(unary_operand.addr, name='unaryOpValue')
        else:
            try:
                unary_value = self.builder.load(unary_operand, name='unaryOpValue')
            except:
                unary_value = unary_operand

        arithmetic_result = self.symbol_table.lookup("arithmetic_result").addr

        if unary_operator == "!":
            return self.builder.neg(unary_value, 'unaryBitNeg')
        elif unary_operator == "~":
            return self.builder.not_(unary_value, 'unaryBitNot')
        elif unary_operator == "delete":
            self.symbol_table.delete(unary_operand.name)
            return
        elif unary_operator == "+":
            return self.builder.add(unary_value, unary_value.type(0), 'unaryPositive')
        elif unary_operator == "-":
            return self.builder.sub(unary_value.type(0), unary_value, 'unaryNegative')
        elif unary_operator == "++":
            if is_prefix:
                unary_value = self.builder.add(unary_value, unary_value.type(1), 'unaryPreInc')
                self.builder.store(unary_value, arithmetic_result)
                try:
                    self.builder.store(unary_value, unary_operand)
                except:
                    pass
            else:
                self.builder.store(unary_value, arithmetic_result)
                try:
                    self.builder.store(self.builder.add(unary_value, unary_value.type(1), 'unaryPostInc'), unary_operand)
                except:
                    pass
        elif unary_operator == "--":
            if is_prefix:
                unary_value = self.builder.sub(unary_value, unary_value.type(1), 'unaryPreDec')
                self.builder.store(unary_value, arithmetic_result)
                try:
                    self.builder.store(unary_value, unary_operand)
                except:
                    pass
            else:
                self.builder.store(unary_value, arithmetic_result)
                try:
                    self.builder.store(self.builder.sub(unary_value, unary_value.type(1), 'unaryPostDec'), unary_operand)
                except:
                    pass
        else:
            return

        return self.builder.load(arithmetic_result, name='arithmetic_result')

    # ====== code generator for function definition, invocation and control flows

    def _codegen_Parameter(self, node):
        if node.name:
            var_name = node.name
        elif node.storageLocation:
            var_name = node.storageLocation
        else:
            var_name = None
        var_type = self._codegen(node.typeName)

        if var_type in BUILT_IN_TYPES:
            pass
        elif type(var_type) is MappingType:
            pass
        elif type(var_type) is ArrayType:
            pass
        elif type(var_type) is ContractType:
            pass
        elif type(var_type) is Symbol:
            pass
        else:
            var_type = i256
        
        return (var_name, var_type)

    def _codegen_ParameterList(self, node):
        arg_names = []
        arg_types = []
        for param in node.parameters:
            (arg_name, arg_type) = self._codegen(param)
            arg_names.append(arg_name)
            arg_types.append(arg_type)
        return (arg_names, arg_types)

    def _codegen_FunctionDefinition(self, node):
        (arg_names, arg_types) = self._codegen(node.parameters)

        arg_llTypes = []
        for i in range(0, len(arg_names)):
            if arg_types[i] in BUILT_IN_TYPES:
                arg_llTypes.append(arg_types[i])
            elif type(arg_types[i]) is MappingType:
                arg_llTypes.append(arg_types[i].getLLVMType())
            elif type(arg_types[i]) is ArrayType:
                arg_llTypes.append(arg_types[i].getLLVMType())
            elif type(arg_types[i]) is Symbol:
                if type(arg_types[i].pyType) is StructType:
                    arg_llTypes.append(arg_types[i].llType)
                elif type(arg_types[i].pyType) is EnumType:
                    arg_llTypes.append(i256)
                elif type(arg_types[i].pyType) is ContractType:
                    arg_llTypes.append(address)
                else:
                    arg_llTypes.append(i256)
            else:
                arg_llTypes.append(i256)
                
        if node.isConstructor:
            self.function = self.contract + "_Constructor"
        else:
            self.function = self.contract + "_Func_" + node.name + str(hash(str(arg_llTypes)))[1:7]
        
        func = self.module.globals[self.function]
        block = func.append_basic_block(name="entry")
        self.builder = ir.IRBuilder(block)

        for i in range(0, len(arg_names)):
            arg_names[i] = "funcArg_%s_%s" % (self.function, arg_names[i])
            sym_arg = self.symbol_table.lookup(arg_names[i])
            alloca = self._alloca(arg_names[i], sym_arg.llType)
            self.builder.store(func.args[i], alloca)
            sym_arg.addr = alloca
            self.symbol_table.update(arg_names[i], sym_arg)
        
        if node.returnParameters and len(node.returnParameters.parameters) == 1:
            (ret_name, ret_type) = self._codegen(node.returnParameters.parameters[0])
            if ret_name:
                ret_name = "funcArg_%s_%s" % (self.function, ret_name)
            else:
                ret_name = "funcArg_%s_%s" % (self.function, "retParam")
        else:
            ret_name = "funcArg_%s_%s" % (self.function, "retParam")
        sym_ret = self.symbol_table.lookup(ret_name)
        alloca = self._alloca(ret_name, sym_ret.llType)
        sym_ret.addr = alloca
        self.symbol_table.update(ret_name, sym_ret)
        
        ret_value = None
        ret_type = self.module.globals.get(self.function).return_value.type
        if node.body:
            ret_value = self._codegen(node.body)
        
        if not self.builder.block.is_terminated:
            if "retParam" not in ret_name:
                ret_value = self.builder.load(sym_ret.addr, name='funcRetValue')
            if ret_value:
                if type(ret_value) is Symbol:
                    ret_value = self.builder.load(ret_value.addr, name='funcRetValue')
                else:
                    try:
                        ret_value = self.builder.load(ret_value, name='funcRetValue')
                    except:
                        ret_value = ret_value
                try:
                    if ret_value.type == ret_type:
                        self.builder.ret(ret_value)
                    else:
                        self.builder.ret(ret_type(0))
                except:
                    self.builder.ret(ret_type(0))
            else:
                self.builder.ret(ret_type(0))

    def _codegen_FunctionCall(self, node):
        # TODO: Currently we only implement a few built-in functions (may occur error "not declared in this scope")
        # TODO: Contract inheritance is not supported (inter-contract function calls may fail)
        callee = self._codegen(node.expression)
        try:
            if type(callee) is ir.IntType or type(callee) is ir.Constant:
                arg_value = self._codegen(node.arguments[0])
                return callee(0)
            elif type(callee) is str and callee == "blockhash":
                return i256(int(hash(time.time())))
            elif type(callee) is str and callee == "balanceOf":
                return i256(0)
            elif type(callee) is str and callee in ("sha256", "keccak256"):
                arg_values = []
                for i in range(0, len(node.arguments)):
                    arg_value = self._codegen(node.arguments[i])
                    arg_values.append(arg_value)
                return i256(int(hash(str(arg_values))))
            elif type(callee) is str and callee == "ecrecover":
                arg_values = []
                for i in range(0, len(node.arguments)):
                    arg_value = self._codegen(node.arguments[i])
                    arg_values.append(arg_value)
                return address(int(hash(str(arg_values))))
            elif type(callee) is str and callee == "call.value":
                for module_name in self.modules:
                    if self.modules[module_name].globals.get("call.value") is not None:
                        callee_func = self.modules[module_name].globals.get("call.value")
                        break
                self.builder.call(callee_func, [], 'FunctionCall')
                return i256(0)
            elif type(callee) is str and callee == "call.gas":
                for module_name in self.modules:
                    if self.modules[module_name].globals.get("call.gas") is not None:
                        callee_func = self.modules[module_name].globals.get("call.gas")
                        break
                self.builder.call(callee_func, [], 'FunctionCall')
                return i256(0)
            elif type(callee) is str and callee == "push":
                return i256(1024)
            elif type(callee) is str and callee == "pop":
                # todo
                pass
            elif type(callee) is str and callee in ("send", "transfer"):
                if callee == "transfer":
                    arg_value = self._codegen(node.arguments[1])
                else:
                    arg_value = self._codegen(node.arguments[0])
                if type(arg_value) is Symbol:
                    transfer_balance = self.builder.load(arg_value.addr, name='trxAmount')
                else:
                    try:
                        transfer_balance = self.builder.load(arg_value, name='trxAmount')
                    except:
                        transfer_balance = arg_value
                receiver_addr = self.symbol_table.lookup("msg_sender_balance").addr
                start_balance = self.builder.load(receiver_addr, name='recvBalance')
                final_balance = self.builder.add(start_balance, transfer_balance, name='sendingBalance')
                self.builder.store(final_balance, receiver_addr)
                return i256(1)
            elif type(callee) is str and (callee == "assert" or callee == "require"):
                sanity_check_bb = ir.Block(self.builder.function, callee + "Start")
                unsatisfied_bb = ir.Block(self.builder.function, "sanityCheckUnsatisfied")
                satisfied_bb = ir.Block(self.builder.function, "end" + callee.capitalize())

                self.builder.branch(sanity_check_bb)
                self.builder.function.basic_blocks.append(sanity_check_bb)
                self.builder.position_at_end(sanity_check_bb)

                cond_value = self._codegen(node.arguments[0])
                if type(cond_value) is Symbol:
                    cond_value = self.builder.load(cond_value.addr, name='condValue')
                else:
                    try:
                        cond_value = self.builder.load(cond_value, name='condValue')
                    except:
                        cond_value = cond_value
                
                cmp = self.builder.icmp_unsigned('!=', cond_value, cond_value.type(0), 'notNull')
                # branch to either unsatisfied_bb or satisfied_bb depending on cmp
                self.builder.cbranch(cmp, satisfied_bb, unsatisfied_bb)

                # 'unsatisfied' part
                self.builder.function.basic_blocks.append(unsatisfied_bb)
                self.builder.position_at_end(unsatisfied_bb)
                # throw
                ret_type = self.module.globals.get(self.function).return_value.type
                self.builder.ret(ret_type(-1))

                # 'endSanityCheck' part
                self.builder.function.basic_blocks.append(satisfied_bb)
                self.builder.position_at_end(satisfied_bb)
                return
            elif type(callee) is str and callee in self.modules:
                arg_value = self._codegen(node.arguments[0])
                if type(arg_value) is Symbol:
                    contract_addr = self.builder.load(arg_value.addr, name='contractAddr')
                else:
                    try:
                        contract_addr = self.builder.load(arg_value, name='contractAddr')
                    except:
                        contract_addr = arg_value
                sym_addr = self._alloca("contractAddr", address)
                self.builder.store(contract_addr, sym_addr)
                return Symbol(None, ContractType(callee, contract_addr), address, sym_addr)
            elif type(callee) is tuple:
                contract_name = callee[0].pyType.contract_name
                call_arg_values = []
                call_arg_types = []
                for i in range(0, len(node.arguments)):
                    arg_value = self._codegen(node.arguments[i])
                    if type(arg_value) is Symbol:
                        arg_value = self.builder.load(arg_value.addr, name='callArgValue')
                    else:
                        try:
                            arg_value = self.builder.load(arg_value, name='callArgValue')
                        except:
                            arg_value = arg_value
                    arg_type = arg_value.type
                    call_arg_values.append(arg_value)
                    call_arg_types.append(arg_type)
                
                callee_name = contract_name + "_Func_" + callee[1] + str(hash(str(call_arg_types)))[1:7]
                callee_func = self.modules[contract_name].globals.get(callee_name)
                if callee_func:
                    return self.builder.call(callee_func, call_arg_values, 'FunctionCall')
                else:
                    global_name = "global_%s_%s" % (contract_name, callee[1])
                    global_sym = self.symbol_table.lookup(global_name)
                    if global_sym:
                        return global_sym
                    else:
                        current_block = self.builder.block
                        fnty = ir.FunctionType(i256, tuple(call_arg_types))
                        func = ir.Function(self.module, fnty, name=callee)
                        callee_func = func
                        self.builder.position_at_end(current_block)
                        return self.builder.call(callee_func, call_arg_values, 'FunctionCall')
            else:
                call_arg_values = []
                call_arg_types = []
                for i in range(0, len(node.arguments)):
                    arg_value = self._codegen(node.arguments[i])
                    if type(arg_value) is Symbol:
                        arg_value = self.builder.load(arg_value.addr, name='callArgValue')
                    else:
                        try:
                            arg_value = self.builder.load(arg_value, name='callArgValue')
                        except:
                            arg_value = arg_value
                    arg_type = arg_value.type
                    call_arg_values.append(arg_value)
                    call_arg_types.append(arg_type)
                
                callee = self.contract + "_Func_" + callee + str(hash(str(call_arg_types)))[1:7]
                callee_func = self.module.globals.get(callee)
                if callee_func:
                    pass
                else:
                    current_block = self.builder.block
                    if "Func_call" in callee or "Func_delegatecall" in callee:
                        fnty = ir.FunctionType(BOOL, tuple(call_arg_types))
                    else:
                        fnty = ir.FunctionType(i256, tuple(call_arg_types))
                    func = ir.Function(self.module, fnty, name=callee)
                    callee_func = func
                    self.builder.position_at_end(current_block)
                
                return self.builder.call(callee_func, call_arg_values, 'FunctionCall')
        except:
            return

    def _codegen_IfStatement(self, node):
        # create basic blocks
        if_bb = ir.Block(self.builder.function, "ifStart")
        then_bb = ir.Block(self.builder.function, "then")
        else_bb = ir.Block(self.builder.function, "else")
        merge_bb = ir.Block(self.builder.function, "endIf")

        self.builder.branch(if_bb)

        self.builder.function.basic_blocks.append(if_bb)
        self.builder.position_at_end(if_bb)

        cond_value = self._codegen(node.condition)
        if type(cond_value) is Symbol:
            cond_value = self.builder.load(cond_value.addr, name='ifCondValue')
        else:
            try:
                cond_value = self.builder.load(cond_value, name='ifCondValue')
            except:
                cond_value = cond_value
        
        cmp = self.builder.icmp_unsigned('!=', cond_value, cond_value.type(0), 'notNull')

        if node.FalseBody != None:
            # branch to either then_bb or else_bb depending on cmp
            self.builder.cbranch(cmp, then_bb, else_bb)
        else:
            self.builder.cbranch(cmp, then_bb, merge_bb)

        # 'then' part
        self.builder.function.basic_blocks.append(then_bb)
        self.builder.position_at_end(then_bb)
        self._codegen(node.TrueBody)
        if not self.builder.block.is_terminated:
            self.builder.branch(merge_bb)

        if node.FalseBody != None:
            # 'else' part
            self.builder.function.basic_blocks.append(else_bb)
            self.builder.position_at_end(else_bb)
            self._codegen(node.FalseBody)
            if not self.builder.block.is_terminated:
                self.builder.branch(merge_bb)

        # 'endIf' part
        self.builder.function.basic_blocks.append(merge_bb)
        self.builder.position_at_end(merge_bb)

        return

    def _codegen_ForStatement(self, node):
        # define blocks
        forLoop_start_bb = ir.Block(self.builder.function, "forLoopStart")
        forLoop_cond_bb = ir.Block(self.builder.function, "forLoopCond")
        forLoop_body_bb = ir.Block(self.builder.function, "forLoopBody")
        forLoop_after_bb = ir.Block(self.builder.function, "forLoopAfter")
        self.loop_cur_blocks.append(forLoop_cond_bb)
        self.loop_end_blocks.append(forLoop_after_bb)

        self.builder.branch(forLoop_start_bb)

        # loop start
        self.builder.function.basic_blocks.append(forLoop_start_bb)
        self.builder.position_at_end(forLoop_start_bb)
        self._codegen(node.initExpression)
        # jump to loop condition
        self.builder.branch(forLoop_cond_bb)

        # compute the end condition
        self.builder.function.basic_blocks.append(forLoop_cond_bb)
        self.builder.position_at_end(forLoop_cond_bb)

        forLoop_end_cond = self._codegen(node.conditionExpression)
        if type(forLoop_end_cond) is Symbol:
            forLoop_end_cond = self.builder.load(forLoop_end_cond.addr, name='forCondValue')
        else:
            try:
                forLoop_end_cond = self.builder.load(forLoop_end_cond, name='forCondValue')
            except:
                forLoop_end_cond = forLoop_end_cond
        
        cmp = self.builder.icmp_unsigned('!=', forLoop_end_cond, forLoop_end_cond.type(0), 'forLoopCond')

        # goto loop body if condition satisfied, otherwise, loop after
        self.builder.cbranch(cmp, forLoop_body_bb, forLoop_after_bb)

        # loop body, note that we ignore the value computed by the body
        self.builder.function.basic_blocks.append(forLoop_body_bb)
        self.builder.position_at_end(forLoop_body_bb)
        # evaluate the step and update the counter
        self._codegen(node.body)
        self._codegen(node.loopExpression)
        # jump to loop condition
        if not self.builder.block.is_terminated:
            self.builder.branch(forLoop_cond_bb)

        # loop after
        self.builder.function.basic_blocks.append(forLoop_after_bb)
        self.builder.position_at_end(forLoop_after_bb)
        self.loop_cur_blocks.pop()
        self.loop_end_blocks.pop()

        return

    def _codegen_WhileStatement(self, node):
        # define blocks
        whileLoop_start_bb = ir.Block(self.builder.function, "whileLoopStart")
        whileLoop_cond_bb = ir.Block(self.builder.function, "whileLoopCond")
        whileLoop_body_bb = ir.Block(self.builder.function, "whileLoopBody")
        whileLoop_after_bb = ir.Block(self.builder.function, "whileLoopAfter")
        self.loop_cur_blocks.append(whileLoop_cond_bb)
        self.loop_end_blocks.append(whileLoop_after_bb)

        self.builder.branch(whileLoop_start_bb)

        # loop start
        self.builder.function.basic_blocks.append(whileLoop_start_bb)
        self.builder.position_at_end(whileLoop_start_bb)
        # jump to loop condition
        self.builder.branch(whileLoop_cond_bb)

        # compute the end condition
        self.builder.function.basic_blocks.append(whileLoop_cond_bb)
        self.builder.position_at_end(whileLoop_cond_bb)

        whileLoop_end_cond = self._codegen(node.condition)
        if type(whileLoop_end_cond) is Symbol:
            whileLoop_end_cond = self.builder.load(whileLoop_end_cond.addr, name='whileCondValue')
        else:
            try:
                whileLoop_end_cond = self.builder.load(whileLoop_end_cond, name='whileCondValue')
            except:
                whileLoop_end_cond = whileLoop_end_cond
        
        cmp = self.builder.icmp_unsigned('!=', whileLoop_end_cond, whileLoop_end_cond.type(0), 'whileLoopCond')
        
        # goto loop body if condition satisfied, otherwise, loop after
        self.builder.cbranch(cmp, whileLoop_body_bb, whileLoop_after_bb)

        # loop body, note that we ignore the value computed by the body
        self.builder.function.basic_blocks.append(whileLoop_body_bb)
        self.builder.position_at_end(whileLoop_body_bb)
        self._codegen(node.body)
        # jump to loop condition
        if not self.builder.block.is_terminated:
            self.builder.branch(whileLoop_cond_bb)

        # loop after
        self.builder.function.basic_blocks.append(whileLoop_after_bb)
        self.builder.position_at_end(whileLoop_after_bb)
        self.loop_cur_blocks.pop()
        self.loop_end_blocks.pop()

        return
