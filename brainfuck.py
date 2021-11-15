import sys
from time import perf_counter

def load_symbols_from_file(filepath):
    symbols = []
    with open(filepath, "r") as fo:
        file = fo.readlines()
    for l in file:
        for c in l.strip():
            if c in ('>', '<', '+', '-', '.', ',', '[', ']'):
                symbols.append(c)
    return symbols


class BrainFuckInterpreter:
    def __init__(self, symbols):
        self.symbols = symbols
        self.execution_operations = []
        self.ops = BrainFuckOperations()
    
    def optimize(self):
        new_exec_stack = []
        i = 0
        while i < len(self.execution_operations):
            op, arg = self.execution_operations[i]
            op_type = op.__name__
            if op_type in ['add', 'sub', 'inc_pointer', 'dec_pointer']:
                j = 0
                targ = 0
                while i+j < len(self.execution_operations):
                    nop, narg = self.execution_operations[i+j]
                    nop_type = nop.__name__
                    if op_type != nop_type:
                        break
                    else:
                        targ += narg
                        j+=1
                new_exec_stack.append((op, targ))
                i = i + j
            else:
                new_exec_stack.append((op, arg))
                i+=1
        self.optimizer_fix_jumppoints(new_exec_stack)
        self.execution_operations = new_exec_stack

    def optimizer_fix_jumppoints(self, stack):
        to_be_fixed_openers = {}
        for i, ex in enumerate(stack):
            op : self.JumpPoint = ex[0]
            if isinstance(op, self.JumpPoint):
                if op.isOpener :
                    src = op.source
                    new_src = i
                    for j in range(i+1, len(stack)):
                        jop : self.JumpPoint = stack[j][0]
                        if isinstance(jop, self.JumpPoint):
                            if jop.toPoint == src:
                                jop.toPoint = new_src
                                to_be_fixed_openers[jop.source] = op
                                break
                else:
                    oop = to_be_fixed_openers[op.source]
                    oop.toPoint = i


    def compile(self):
        return_stack = []
        index = 0
        for symbol in self.symbols:
            func = None
            if symbol == '>':
                func = (self.ops.inc_pointer, 1)
            elif symbol == '<':
                func = (self.ops.dec_pointer, 1)
            elif symbol == '+':
                func = (self.ops.add, 1)
            elif symbol == '-':
                func = (self.ops.sub, 1)
            elif symbol == '.':
                func = (self.ops.output, 1)
            elif symbol == ',':
                func = (self.ops.input, 1)
            elif symbol == '[':
                jmp = self.JumpPoint(index, isOpener = True)
                ret = [jmp, index, None]
                return_stack.append(ret)
                func = (jmp, 1)
            elif symbol == ']':
                assert return_stack, index+":COMPILE ERROR: No opening loop symbol"
                ret = return_stack.pop()
                assert ret[2] == None, index+":COMPILE ERROR: Closing loop does not match to a opening loop symbol"
                ret[2] = index
                ret[0].toPoint = index
                jmp = self.JumpPoint(index)
                jmp.toPoint = ret[1]
                func = (jmp, 1)
    
            if func != None:
                self.execution_operations.append(func)
                index += 1
        if len(return_stack) > 0:
            print("COMPILE ERROR: Some loops where never closed")
            for ret in return_stack:
                print("@", ret[1], ret[2])
            exit()
    
    def execute(self):
        i = 0
        while i < len(self.execution_operations):
            op, arg = self.execution_operations[i]
            if isinstance(op, self.JumpPoint):
                assert op.toPoint != None, "\nInvalid JumpPoint"
                dat = self.ops.get()
                if op.isOpener:
                    if(dat == 0):
                        i = op.toPoint
                else:
                    if(dat != 0):
                        i = op.toPoint
            elif callable(op):
                op(arg)
            else:
                assert False, "INTERPRETER ERROR: Invalid execution operation"
            i+=1

    def print_ops(self):
        for i, exec in enumerate(self.execution_operations):
            op, arg = exec
            if isinstance(op, self.JumpPoint):
                print(i, ": JMP :", op)
            else:
                fn_name = op.__name__
                print(i, ": OP  :", f"{fn_name}({arg})")
    
    class JumpPoint:
        def __init__(self, src, isOpener = False):
            self.source = src
            self.toPoint = None
            self.isOpener = isOpener
            self.__name__ = "jmp"
        def __str__(self) -> str:
            return "jmp -> " + str(self.toPoint)

class BrainFuckOperations:
    def __init__(self):
        self.STACK_SIZE = 30_000
        self.pointer = 0
        self.stack = [0] * self.STACK_SIZE
        self.input_queue = []
    
    def get_index(self):
        return (self.pointer + (self.STACK_SIZE // 2)) % self.STACK_SIZE
    
    def get(self):
        i = self.get_index()
        return self.stack[i]

    def add(self, n):
        i = self.get_index()
        self.stack[i] = (self.stack[i] + n) % 256
    
    def sub(self, n):
        i = self.get_index()
        self.stack[i] = (self.stack[i] - n) % 256

    def debug_set(self, dat):
        i = self.get_index()
        self.stack[i] = dat % 256

    def inc_pointer(self, n):
        self.pointer += n
    
    def dec_pointer(self, n):
        self.pointer -= n
    
    def input(self, _):
        if len(self.input_queue) == 0:
            uinp = input(':')
            if len(uinp) <= 0:
                uinp = '\n'
            self.input_queue.extend(reversed(list(uinp)))
        inp = self.input_queue.pop()
        dat = int.from_bytes(inp.encode('ascii'), sys.byteorder)
        self.stack[self.get_index()] = dat % 256

    def output(self, _):
        data = self.stack[self.get_index()]
        bdata = int.to_bytes(data, 1, sys.byteorder)
        sdata = bdata.decode("ascii", "ignore") 
        print(sdata, end="", flush=True)

FLAG_OPTIMIZE = True

if __name__ == "__main__":
    if(len(sys.argv) != 2):
        print(f"Usage: \n interpreter.py program.b")
        exit()
    filepath = sys.argv[1]
    sym = load_symbols_from_file(filepath)

    bf = BrainFuckInterpreter(sym)

    compile_start = perf_counter()
    bf.compile()
    
    if FLAG_OPTIMIZE:
        ops_before = len(bf.execution_operations)
        bf.optimize()
        ops_after = len(bf.execution_operations)
        print(f"[COMPILE] Optimizer: {ops_before} --> {ops_after} OPS")

    interpreter_start = perf_counter()
    print('[COMPILE] Compilation took:', round(interpreter_start - compile_start, 4), 's')
    
    #bf.print_ops()
    
    bf.execute()

    #if(perf_counter() - interpreter_start > 0):
    print('\n[INTERPRETER] Program took:', round(perf_counter() - interpreter_start, 6), 's')