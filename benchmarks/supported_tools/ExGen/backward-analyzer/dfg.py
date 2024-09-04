from node import Node

class DataflowGraph(object):
    def __init__(self, filename):
        self.dfg = {}
        self.global_deps = {}
        self.codelines = []
        llvmfile = open(filename)
        for line in llvmfile:
            line = line.strip()
            self.codelines.append(line)
        
    def dfg_constructor(self):
        for i in range(0, len(self.codelines)):
            if "define " in self.codelines[i]:
                pos1 = self.codelines[i].index("@")
                pos2 = -1
                pos3 = -1
                for char_idx in range(pos1, len(self.codelines[i])):
                    if self.codelines[i][char_idx] == "(":
                        pos2 = char_idx
                        break
                for char_idx in range(pos2, len(self.codelines[i])):
                    if self.codelines[i][char_idx] == ")":
                        pos3 = char_idx

                if pos2 != -1 and pos3 != -1:
                    func_name = self.codelines[i][pos1+1:pos2]
                    
                    codeline = self.codelines[i][pos2+1:pos3]
                    while "%\"struct" in codeline:
                        idx = codeline.index("%\"struct")
                        for char_idx in range(idx+2, len(codeline)):
                            if codeline[char_idx] == "\"":
                                codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                                break
                    while r"%struct" in codeline:
                        idx = codeline.index(r"%struct")
                        for char_idx in range(idx+2, len(codeline)):
                            if codeline[char_idx] == "," or codeline[char_idx] == "*" or codeline[char_idx] == " ":
                                codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                                break
                    while "%\"class" in codeline:
                        idx = codeline.index("%\"class")
                        for char_idx in range(idx+2, len(codeline)):
                            if codeline[char_idx] == "\"":
                                codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                                break
                    while r"%class" in codeline:
                        idx = codeline.index(r"%class")
                        for char_idx in range(idx+2, len(codeline)):
                            if codeline[char_idx] == "," or codeline[char_idx] == "*" or codeline[char_idx] == " ":
                                codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                                break
                    if codeline:
                        func_params = codeline.split(", ")
                        for param_idx in range(0, len(func_params)):
                            if " " in func_params[param_idx]:
                                func_params[param_idx] = func_params[param_idx].split(" ")[-1]
                                if "%" not in func_params[param_idx] and "@" not in func_params[param_idx]:
                                    func_params[param_idx] = "%" + str(param_idx)
                            else:
                                func_params[param_idx] = "%" + str(param_idx)
                    else:
                        func_params = []
                    self.dfg[func_name] = {}
                    self.dfg[func_name]["params"] = func_params
                    self.dfg[func_name]["code_start"] = i
                
        for func_name in self.dfg:
            code_start = self.dfg[func_name]["code_start"]
            for i in range(code_start, len(self.codelines)):
                if self.codelines[i] == "}":
                    self.dfg[func_name]["code_end"] = i
                    break
            self.dfg[func_name]["dataflows"] = []
            self.dfg[func_name]["unsafe_variables"] = []
            self.dfg[func_name]["buggy_insts"] = []
            self.dfg[func_name]["callers"] = {}
            for param in self.dfg[func_name]["params"]:
                self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + param)

    def taint_analyzer(self):
        for func_name in self.dfg:
            code_start = self.dfg[func_name]["code_start"]
            code_end = self.dfg[func_name]["code_end"]
            for i in range(code_start, code_end):
                codeline = self.codelines[i]
                while "%\"struct" in codeline:
                    idx = codeline.index("%\"struct")
                    for char_idx in range(idx+2, len(codeline)):
                        if codeline[char_idx] == "\"":
                            codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                            break
                while r"%struct" in codeline:
                    idx = codeline.index(r"%struct")
                    for char_idx in range(idx+2, len(codeline)):
                        if codeline[char_idx] == "," or codeline[char_idx] == "*" or codeline[char_idx] == " ":
                            codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                            break
                while "%\"class" in codeline:
                    idx = codeline.index("%\"class")
                    for char_idx in range(idx+2, len(codeline)):
                        if codeline[char_idx] == "\"":
                            codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                            break
                while r"%class" in codeline:
                    idx = codeline.index(r"%class")
                    for char_idx in range(idx+2, len(codeline)):
                        if codeline[char_idx] == "," or codeline[char_idx] == "*" or codeline[char_idx] == " ":
                            codeline = codeline.replace(codeline[idx:char_idx+1], "i64")
                            break
                
                op0 = None
                op1 = None
                op2 = None

                # Propagate taint flag based on instruction type
                if " = add" in codeline:
                    op0 = codeline.split(" = add ")[0]
                    op1 = codeline.split(" = add ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = add ")[1].split(", ")[1]

                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if op1 or op2:
                        self.dfg[func_name]["buggy_insts"].append((i, self.codelines[i], op0, op1, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = mul" in codeline:
                    op0 = codeline.split(" = mul ")[0]
                    op1 = codeline.split(" = mul ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = mul ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if op1 or op2:
                        self.dfg[func_name]["buggy_insts"].append((i, self.codelines[i], op0, op1, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = sub" in codeline:
                    op0 = codeline.split(" = sub ")[0]
                    op1 = codeline.split(" = sub ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = sub ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if op1 or op2:
                        self.dfg[func_name]["buggy_insts"].append((i, self.codelines[i], op0, op1, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = and" in codeline:
                    op0 = codeline.split(" = and ")[0]
                    op1 = codeline.split(" = and ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = and ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = xor" in codeline:
                    op0 = codeline.split(" = xor ")[0]
                    op1 = codeline.split(" = xor ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = xor ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = shl" in codeline:
                    op0 = codeline.split(" = shl ")[0]
                    op1 = codeline.split(" = shl ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = shl ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = ashr" in codeline:
                    op0 = codeline.split(" = ashr ")[0]
                    op1 = codeline.split(" = ashr ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = ashr ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = lshr" in codeline:
                    op0 = codeline.split(" = lshr ")[0]
                    op1 = codeline.split(" = lshr ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = lshr ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = sdiv" in codeline:
                    op0 = codeline.split(" = sdiv ")[0]
                    op1 = codeline.split(" = sdiv ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = sdiv ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = urem" in codeline:
                    op0 = codeline.split(" = urem ")[0]
                    op1 = codeline.split(" = urem ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = urem ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = icmp" in codeline:
                    op0 = codeline.split(" = icmp ")[0]
                    op1 = codeline.split(" = icmp ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = icmp ")[1].split(", ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = load" in codeline:
                    op0 = codeline.split(" = load ")[0]
                    typ = codeline.split(" = load ")[1].split(", ")[0]
                    op1 = codeline.split(" = load ")[1].split(", ")[1].split(" ")[-1]

                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif "store " in codeline:
                    # nop = codeline.split("store ")[0]
                    op0 = codeline.split("store ")[1].split(", ")[0].split(" ")[-1]
                    op1 = codeline.split("store ")[1].split(", ")[1].split(" ")[-1]

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if func_name + "$" + op0 in self.dfg[func_name]["unsafe_variables"]:
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if type(op0) == Node and op0.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op1)
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op1, op0))
                    
                    if type(op1) == Node and op1.func == "global":
                        if op1.name in self.global_deps:
                            if func_name in self.global_deps[op1.name]:
                                self.global_deps[op1.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op1.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op1.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = zext" in codeline:
                    op0 = codeline.split(" = zext ")[0]
                    op1 = codeline.split(" = zext ")[1].split(" to ")[0].split(" ")[-1]
                    # op2 = codeline.split(" = zext ")[1].split(" to ")[1]

                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = bitcast" in codeline:
                    op0 = codeline.split(" = bitcast ")[0]
                    op1 = codeline.split(" = bitcast ")[1].split(" to ")[0].split(" ")[-1]
                    # op2 = codeline.split(" = bitcast ")[1].split(" to ")[1]
                                
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = ptrtoint" in codeline:
                    op0 = codeline.split(" = ptrtoint ")[0]
                    op1 = codeline.split(" = ptrtoint ")[1].split(" to ")[0].split(" ")[-1]
                    # op2 = codeline.split(" = ptrtoint ")[1].split(" to ")[1]
                                
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = inttoptr" in codeline:
                    op0 = codeline.split(" = inttoptr ")[0]
                    op1 = codeline.split(" = inttoptr ")[1].split(" to ")[0].split(" ")[-1]
                    # op2 = codeline.split(" = inttoptr ")[1].split(" to ")[1]
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = select" in codeline:
                    # %52 = select i1 %50, i64 -2, i64 %51
                    # %26 = select i1 %25, i32 %12, i32 %24
                    op0 = codeline.split(" = select ")[0]
                    op1 = codeline.split(" = select ")[1].split(", ")[0].split(" ")[-1]
                    op2 = codeline.split(" = select ")[1].split(", ")[1].split(" ")[-1]
                    op3 = codeline.split(" = select ")[1].split(", ")[2].split(" ")[-1]

                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None
                    
                    if "@" in op2:
                        op2 = Node("global", op2, "unsafe")
                    elif "%" in op2:
                        if func_name + "$" + op2 in self.dfg[func_name]["unsafe_variables"]:
                            op2 = Node(func_name, op2, "unsafe")
                        else:
                            op2 = Node(func_name, op2, "safe")
                    else:
                        op2 = None
                    
                    if "@" in op3:
                        op3 = Node("global", op3, "unsafe")
                    elif "%" in op3:
                        if func_name + "$" + op3 in self.dfg[func_name]["unsafe_variables"]:
                            op3 = Node(func_name, op3, "unsafe")
                        else:
                            op3 = Node(func_name, op3, "safe")
                    else:
                        op3 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if (type(op1) == Node and op1.attr == "unsafe") or (type(op2) == Node and op2.attr == "unsafe") or (type(op3) == Node and op3.attr == "unsafe"):
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None

                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    if op0 and op2:
                        self.dfg[func_name]["dataflows"].append((op0, op2))
                    if op0 and op3:
                        self.dfg[func_name]["dataflows"].append((op0, op3))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = getelementptr" in codeline:
                    op0 = codeline.split(" = getelementptr ")[0]
                    arg_str = codeline.split(" = getelementptr ")[1]
                    if "@" in arg_str:
                        idx = arg_str.index("@")
                        for char_idx in range(idx, len(arg_str)):
                            if arg_str[char_idx] == ",":
                                end = char_idx
                                break
                        op1 = arg_str[idx:end]
                    elif "%" in arg_str:
                        idx = arg_str.index("%")
                        for char_idx in range(idx, len(arg_str)):
                            if arg_str[char_idx] == ",":
                                end = char_idx
                                break
                        op1 = arg_str[idx:end]
                    else:
                        op1 = ""
                    
                    if "@" in op1:
                        op1 = Node("global", op1, "unsafe")
                    elif "%" in op1:
                        if func_name + "$" + op1 in self.dfg[func_name]["unsafe_variables"]:
                            op1 = Node(func_name, op1, "unsafe")
                        else:
                            op1 = Node(func_name, op1, "safe")
                    else:
                        op1 = None

                    if "@" in op0:
                        op0 = Node("global", op0, "unsafe")
                    elif "%" in op0:
                        if type(op1) == Node and op1.attr == "unsafe":
                            self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                            op0 = Node(func_name, op0, "unsafe")
                        else:
                            op0 = Node(func_name, op0, "safe")
                    else:
                        op0 = None
                    
                    if op0 and op1:
                        self.dfg[func_name]["dataflows"].append((op0, op1))
                    
                    if type(op0) == Node and op0.func == "global":
                        if op0.name in self.global_deps:
                            if func_name in self.global_deps[op0.name]:
                                self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                        else:
                            self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                elif " = call" in codeline:
                    op0 = codeline.split(" = call ")[0]
                    if " " in op0:
                        op0 = op0.split(" ")[0]
                    
                    callee_str = codeline.split(" = call ")[1]
                    if "@" in callee_str:
                        pos1 = callee_str.index("@")
                        for char_idx in range(pos1, len(callee_str)):
                            if callee_str[char_idx] == "(":
                                pos2 = char_idx
                                break
                        for char_idx in range(pos2, len(callee_str)):
                            if callee_str[char_idx] == ")":
                                pos3 = char_idx
                        callee_name = callee_str[pos1+1:pos2]

                        if callee_name in self.dfg:
                            arg_str = callee_str[pos2+1:pos3]
                            if arg_str:
                                func_args = arg_str.split(", ")
                                for arg_idx in range(0, len(func_args)):
                                    if " " in func_args[arg_idx]:
                                        func_args[arg_idx] = func_args[arg_idx].split(" ")[-1]
                            else:
                                func_args = []
                            for arg_idx in range(0, len(func_args)):
                                try:
                                    if "@" in func_args[arg_idx]:
                                        func_args[arg_idx] = Node("global", func_args[arg_idx], "unsafe")
                                    elif "%" in func_args[arg_idx]:
                                        if func_name + "$" + func_args[arg_idx] in self.dfg[func_name]["unsafe_variables"]:
                                            func_args[arg_idx] = Node(func_name, func_args[arg_idx], "unsafe")
                                        else:
                                            func_args[arg_idx] = Node(func_name, func_args[arg_idx], "safe")
                                    else:
                                        func_args[arg_idx] = None
                                except:
                                    continue
                            
                            unsafe_flag = False
                            for arg_idx in range(0, len(func_args)):
                                if type(func_args[arg_idx]) == Node and func_args[arg_idx].attr == "unsafe":
                                    unsafe_flag = True
                                    break
                            if "@" in op0:
                                op0 = Node("global", op0, "unsafe")
                            elif "%" in op0:
                                if unsafe_flag:
                                    self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                                    op0 = Node(func_name, op0, "unsafe")
                                else:
                                    op0 = Node(func_name, op0, "safe")
                            else:
                                op0 = None
                            
                            for arg_idx in range(0, len(func_args)):
                                try:
                                    if func_args[arg_idx]:
                                        if op0:
                                            self.dfg[func_name]["dataflows"].append((op0, func_args[arg_idx]))
                                        param = Node(callee_name, self.dfg[callee_name]["params"][arg_idx], "unsafe")
                                        self.dfg[callee_name]["dataflows"].append((param, func_args[arg_idx]))
                                except:
                                    continue
                            
                            if func_name in self.dfg[callee_name]["callers"]:
                                self.dfg[callee_name]["callers"][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.dfg[callee_name]["callers"][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}] 
                        
                        if type(op0) == Node and op0.func == "global":
                            if op0.name in self.global_deps:
                                if func_name in self.global_deps[op0.name]:
                                    self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                                else:
                                    self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                            else:
                                self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                    if "call.value" in callee_name or "call.gas" in callee_name:
                        # reentrancy
                        self.dfg[func_name]["buggy_insts"].append((i, self.codelines[i], op0, op1, op2))
                    if "Func_selfdestruct" in callee_name or "Func_call" in callee_name or "Func_delegatecall" in callee_name or "Func_callcode" in callee_name:
                        # selfdestruct and call-family
                        self.dfg[func_name]["buggy_insts"].append((i, self.codelines[i], op0, op1, op2))
                elif "call " in codeline:
                    op0 = codeline.split("call ")[0]
                    if " " in op0:
                        op0 = op0.split(" ")[0]
                    
                    callee_str = codeline.split("call ")[1]
                    if "@" in callee_str:
                        pos1 = callee_str.index("@")
                        for char_idx in range(pos1, len(callee_str)):
                            if callee_str[char_idx] == "(":
                                pos2 = char_idx
                                break
                        for char_idx in range(pos2, len(callee_str)):
                            if callee_str[char_idx] == ")":
                                pos3 = char_idx
                        callee_name = callee_str[pos1+1:pos2]

                        if callee_name in self.dfg:
                            arg_str = callee_str[pos2+1:pos3]
                            if arg_str:
                                func_args = arg_str.split(", ")
                                for arg_idx in range(0, len(func_args)):
                                    if " " in func_args[arg_idx]:
                                        func_args[arg_idx] = func_args[arg_idx].split(" ")[-1]
                            else:
                                func_args = []
                            for arg_idx in range(0, len(func_args)):
                                try:
                                    if "@" in func_args[arg_idx]:
                                        func_args[arg_idx] = Node("global", func_args[arg_idx], "unsafe")
                                    elif "%" in func_args[arg_idx]:
                                        if func_name + "$" + func_args[arg_idx] in self.dfg[func_name]["unsafe_variables"]:
                                            func_args[arg_idx] = Node(func_name, func_args[arg_idx], "unsafe")
                                        else:
                                            func_args[arg_idx] = Node(func_name, func_args[arg_idx], "safe")
                                    else:
                                        func_args[arg_idx] = None
                                except:
                                    continue
                            
                            unsafe_flag = False
                            for arg_idx in range(0, len(func_args)):
                                if type(func_args[arg_idx]) == Node and func_args[arg_idx].attr == "unsafe":
                                    unsafe_flag = True
                                    break
                            if "@" in op0:
                                op0 = Node("global", op0, "unsafe")
                            elif "%" in op0:
                                if unsafe_flag:
                                    self.dfg[func_name]["unsafe_variables"].append(func_name + "$" + op0)
                                    op0 = Node(func_name, op0, "unsafe")
                                else:
                                    op0 = Node(func_name, op0, "safe")
                            else:
                                op0 = None
                            
                            for arg_idx in range(0, len(func_args)):
                                try:
                                    if func_args[arg_idx]:
                                        if op0:
                                            self.dfg[func_name]["dataflows"].append((op0, func_args[arg_idx]))
                                        param = Node(callee_name, self.dfg[callee_name]["params"][arg_idx], "unsafe")
                                        self.dfg[callee_name]["dataflows"].append((param, func_args[arg_idx]))
                                except:
                                    continue
                            
                            if func_name in self.dfg[callee_name]["callers"]:
                                self.dfg[callee_name]["callers"][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                            else:
                                self.dfg[callee_name]["callers"][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}] 
                        
                        if type(op0) == Node and op0.func == "global":
                            if op0.name in self.global_deps:
                                if func_name in self.global_deps[op0.name]:
                                    self.global_deps[op0.name][func_name].append({"inst_num": i, "inst_str": self.codelines[i]})
                                else:
                                    self.global_deps[op0.name][func_name] = [{"inst_num": i, "inst_str": self.codelines[i]}]
                            else:
                                self.global_deps[op0.name] = {func_name: [{"inst_num": i, "inst_str": self.codelines[i]}]}
                else:
                    pass
