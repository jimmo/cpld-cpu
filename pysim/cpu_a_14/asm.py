import collections
from lark import Lark, UnexpectedInput

l = Lark(open("cpu_a_14/asm.g").read(), parser="earley", lexer="auto")


class AssemblerTransformer:
    def __init__(self, assembler):
        self.assembler = assembler

    def transform(self, ast):
        for statement in ast.children:
            if statement.data == "statement":
                statement = statement.children[0]
                if statement.data == "cmd":
                    self.cmd(statement.children)
                elif statement.data == "op":
                    self.op(statement.children)
                else:
                    raise ValueError("Unknown statment", statement)

    def parse_number(self, token):
        if token.type != "NUMBER":
            raise ValueError(f'Invalid number token type {token.type} "{token}"')
        if token.startswith("0x"):
            return int(token, 16)
        if token.startswith("0o"):
            return int(token, 8)
        return int(token, 10)

    def cmd(self, m):
        print(" ".join(x.value for x in m))
        if m[0].type == "CMD_ORG":
            self.assembler.org(self.parse_number(m[1]))
        else:
            raise ValueError(f"Unknown command: {m}")

    def op(self, m):
        if m[0].type == "LABEL":
            print(m[0] + ":")
            self.assembler.label(self.assembler.create_label(m[0]))
            m = m[1:]

        print(" ".join(x.value for x in m))
        if m[0].type == "OP_DCB":
            self.assembler.dcb(self.parse_number(m[1]))
            return

        label = None
        if len(m) == 2:
            if m[1].type == "NUMBER":
                label = self.assembler.const(self.parse_number(m[1]))
            else:
                label = self.assembler.create_label(m[1])

        if m[0].type == "OP_NOR":
            self.assembler.nor(label)
        elif m[0].type == "OP_ADD":
            self.assembler.add(label)
        elif m[0].type == "OP_STA":
            self.assembler.sta(label)
        elif m[0].type == "OP_CLR":
            self.assembler.nor(self.assembler.create_label("allone"))
        elif m[0].type == "OP_LDA":
            self.assembler.lda(label)
        elif m[0].type == "OP_NOT":
            self.assembler.nor(self.assembler.create_label("zero"))
        elif m[0].type == "OP_SUB":
            self.assembler.nor(self.assembler.create_label("zero"))
            self.assembler.add(label)
            self.assembler.nor(self.assembler.create_label("zero"))
        elif m[0].type == "OP_JCC":
            self.assembler.jcc(label)
        elif m[0].type == "OP_JMP":
            self.assembler.jcc(label)
            self.assembler.jcc(label)
        elif m[0].type == "OP_JCS":
            self.assembler.jcs(label)
        elif m[0].type == "OP_HLT":
            self.assembler.hlt()
        elif m[0].type == "OP_OUT":
            self.assembler.sta(self.assembler.create_label("display"))
            self.assembler.lda(self.assembler.create_label("trigger"))
            self.assembler.nor(self.assembler.create_label("one"))
            self.assembler.sta(self.assembler.create_label("trigger"))
            self.assembler.lda(self.assembler.create_label("display"))
        else:
            raise ValueError(f"Unknown op: {m}")


class Assembler:
    PREFIX_NOR = 0b00000000_00000000
    PREFIX_ADD = 0b01000000_00000000
    PREFIX_STA = 0b10000000_00000000
    PREFIX_JCC = 0b11000000_00000000

    def __init__(self, data, addr):
        print(len(data))
        self._data = data
        self._offset = 0
        self._labels = collections.defaultdict(Assembler.Label)
        self._indent = 0
        self._consts = {}
        self._nreserved = 0

    def log(self, s):
        print("  0x{:04x}: {}{}".format(self._offset, "  " * self._indent, s))

    def create_label(self, name):
        l = self._labels[name]
        l._name = name
        return l

    class Label:
        def __init__(self):
            self._offset = None
            self._name = None
            self._fixups = []
            self._register = False

        def addr(self):
            return self._offset

    def write_instr(self, instr):
        self._data[self._offset] = instr >> 8
        self._data[self._offset + 1] = instr & 0xFF
        self._offset += 2

    def write_byte(self, b):
        self._data[self._offset] = b & 0xFF
        self._offset += 1

    def __enter__(self):
        self.reserve("one", 1, register=True)
        self.reserve("allone", 0xFF, register=True)
        self.reserve("zero", 0, register=True)
        self.reserve("trigger", 0, register=True)
        self.reserve("display", 0, register=True)
        self.reserve("page1", 0, register=True)
        self.reserve("page0", 0, register=True)
        self.reserve("_tmp1", 0, register=True)
        self.reserve("_tmp2", 0, register=True)
        self.reserve("_sp", 0, register=True)
        self.reserve("_stack", [0] * 32, register=True)
        return self

    def __exit__(self, a, b, c):
        for l in self._labels.values():
            if l._offset is None:
                raise ValueError(f'Undefined label "{l._name}"')
            for offset in l._fixups:
                addr = l.addr()
                self._data[offset] |= (addr >> 8) & 0x3F
                self._data[offset + 1] |= addr & 0xFF

    def org(self, addr):
        self._offset = addr

    def const(self, value):
        if value in self._consts:
            return self._consts[value]
        name = "_const_{}".format(value)
        l = self.create_label(name)
        self.reserve(name, value)
        self._consts[value] = l
        return l

    def reserve(self, name, value, register=False):
        if isinstance(value, int):
            value = [value]
        prev_offset = self._offset
        self._offset = 2 ** 14 - len(value) - self._nreserved
        self._nreserved += len(value)
        self.label(self.create_label(name), register)
        offset = self._offset
        for x in value:
            self.dcb(x)
        self._offset = prev_offset
        return offset

    def label(self, l, register=False):
        self.log('  label "{}" at 0x{:04x}'.format(l._name, self._offset))
        if l._offset is not None:
            raise ValueError(f"Label redefinition: {l._name}")
        l._offset = self._offset
        l._register = register

        l1 = self.create_label(l._name + "_")
        l1._offset = self._offset + 1

    def placeholder(self, label):
        label._fixups.append(self._offset)

    def nor(self, label):
        self.log("  nor {}".format(label._name))
        self.placeholder(label)
        self.write_instr(Assembler.PREFIX_NOR)

    def add(self, label):
        self.log("  add {}".format(label._name))
        self.placeholder(label)
        self.write_instr(Assembler.PREFIX_ADD)

    def sta(self, label):
        self.log("  sta {}".format(label._name))
        self.placeholder(label)
        self.write_instr(Assembler.PREFIX_STA)

    def lda(self, label):
        self.log("  lda {}".format(label._name))
        self._indent += 1
        self.nor(self.create_label("allone"))
        self.add(label)
        self._indent -= 1

    def jcc(self, label):
        self.log("  jcc {}".format(label._name))
        self.placeholder(label)
        self.write_instr(Assembler.PREFIX_JCC)

    def jcs(self, label):
        self.log("  jcs {}".format(label._name))
        self.write_instr(Assembler.PREFIX_JCC | (self._offset + 4))
        self._indent += 1
        self.jcc(label)
        self._indent -= 1

    def hlt(self):
        self.log("  hlt")
        self.write_instr(Assembler.PREFIX_JCC | self._offset)
        self.write_instr(Assembler.PREFIX_JCC | self._offset)

    def dcb(self, v):
        self.log("  dcb 0x{:02x}".format(v))
        self.write_byte(v)

    def parse(self, path):
        with open(path) as f:
            contents = f.read()
            try:
                ast = l.parse(contents)
            except UnexpectedInput as e:
                self.log(f"{path}:{e.line}:{e.column}: unexpected input.")
                self.log("  " + contents.split("\n")[e.line - 1])
                self.log("  " + " " * e.column + "^")
                return False
            AssemblerTransformer(self).transform(ast)
            return True
