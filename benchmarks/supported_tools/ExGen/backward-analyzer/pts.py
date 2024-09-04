import json
from node import Node
from dfg import DataflowGraph

class PartiallyTxnSet(object):
    def __init__(self, filename, vul_type):
        file_dfg = DataflowGraph(filename)
        file_dfg.dfg_constructor()
        file_dfg.taint_analyzer()
        self.vul_type = vul_type
        self.dfg = file_dfg.dfg
        self.global_deps = file_dfg.global_deps

    def pts_constructor(self):
        # collect injection points
        inj_pts = {}
        for func_name in self.dfg:
            inj_insts = []
            for inst in self.dfg[func_name]["buggy_insts"]:
                op1 = inst[3]
                op2 = inst[4]
                # Append critical instructions to inj_insts based on vulnerability type
                if self.vul_type == "intflow":
                    if type(op1) == Node and (op1.attr == "unsafe" or op1.func + "$" + op1.name in self.dfg[func_name]["unsafe_variables"]):
                        inj_insts.append({"inst_num": inst[0], "inst_str": inst[1]})
                    elif type(op2) == Node and (op2.attr == "unsafe" or op2.func + "$" + op2.name in self.dfg[func_name]["unsafe_variables"]):
                        inj_insts.append({"inst_num": inst[0], "inst_str": inst[1]})
                    else:
                        pass
                elif self.vul_type == "reentrancy":
                    if "call.value" in inst[1] or "call.gas" in inst[1]:
                        inj_insts.append({"inst_num": inst[0], "inst_str": inst[1]})
                    else:
                        pass
                elif self.vul_type == "teether":
                    if "Func_selfdestruct" in inst[1] or "Func_callcode" in inst[1] or "Func_delegatecall" in inst[1] or "Func_call" in inst[1]:
                        inj_insts.append({"inst_num": inst[0], "inst_str": inst[1]})
                    else:
                        pass
                else:
                    pass
            if inj_insts:
                inj_pts[func_name] = inj_insts

        # function call sequence
        call_sequence = []
        for func_name in inj_pts:
            call_sequence.append([{"func_name": func_name, "instructions": inj_pts[func_name]}])

        ITER_LIMIT = 2 # change the number to adjust the length limit of call sequence
        for i in range(0, ITER_LIMIT):
            new_call_sequence = []
            for seq in call_sequence:
                callee = seq[-1]["func_name"]
                if self.dfg[callee]["callers"]:
                    for caller in self.dfg[callee]["callers"]:
                        new_call_sequence.append(seq + [{"func_name": caller, "instructions": self.dfg[callee]["callers"][caller]}])
                else:
                    new_call_sequence.append(seq)
            call_sequence = new_call_sequence
        direct_call_sequence = call_sequence

        new_call_sequence = []
        for seq in call_sequence:
            global_vars = []
            exist_funcs = {}
            call_idx = 0
            for call in seq:
                func_name = call["func_name"]
                exist_funcs[func_name] = call_idx
                for dataflow in self.dfg[func_name]["dataflows"]:
                    src = dataflow[1]
                    if type(src) == Node and src.func == "global" and (src.name not in global_vars):
                        global_vars.append(src.name)
                call_idx += 1
            
            new_sequence = []
            dyn_sequence = [seq]
            bak_sequence = dyn_sequence
            for gvar_name in global_vars:
                if gvar_name in self.global_deps:
                    for caller in self.global_deps[gvar_name]:
                        if caller in exist_funcs:
                            for dyn_seq_idx in range(0, len(dyn_sequence)):
                                if exist_funcs[caller] !=0 and self.global_deps[gvar_name][caller][-1] not in dyn_sequence[dyn_seq_idx][exist_funcs[caller]]["instructions"]:
                                    dyn_sequence[dyn_seq_idx][exist_funcs[caller]]["instructions"] += [self.global_deps[gvar_name][caller][-1]]
                        else:
                            for dyn_seq in dyn_sequence:
                                new_sequence.append(dyn_seq + [{"func_name": caller, "instructions": [self.global_deps[gvar_name][caller][-1]]}])
                    if new_sequence:
                        dyn_sequence = new_sequence
                        new_sequence = []
            if dyn_sequence == bak_sequence:
                new_call_sequence.append(seq)
            else:
                new_call_sequence += dyn_sequence
            if len(new_call_sequence) > 10000:
                break
        if call_sequence != new_call_sequence:
            call_sequence = new_call_sequence
        
        call_sequence = call_sequence + direct_call_sequence
        for func_name in inj_pts:
            call_sequence.append([{"func_name": func_name, "instructions": inj_pts[func_name]}])

        filtered_call_sequence = []
        for seq in call_sequence:
            if "@wasm_rt_call_stack_depth" not in str(seq):
                # Eliminate the integer-flow false positives of @wasm_rt_call_stack_depth
                filtered_call_sequence.append(seq)
        return json.dumps(filtered_call_sequence)
