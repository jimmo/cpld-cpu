start: statement+

LABEL_CHAR: "a".."z"|"0".."9"|"_"
LABEL: ("a".."z"|"_") LABEL_CHAR+

DEC_NUMBER: /[1-9]\d*l?/i
HEX_NUMBER: /0x[\da-f]*l?/i
OCT_NUMBER: /0o?[0-7]*l?/i
NUMBER: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER

LOCATION: "*"

CMD_ORG: "org"
CMD_PAGE: "page"

OP_DCB: "dcb"

OP_NOR: "nor"
OP_ADD: "add"
OP_STA: "sta"
OP_NORX: "norx"
OP_ADDX: "addx"
OP_STX: "stx"
OP_JCC: "jcc"
OP_JNZ: "jnz"

OP_CLR: "clr"
OP_LDA: "lda"
OP_NOT: "not"
OP_SUB: "sub"
OP_CLRX: "clrx"
OP_LDX: "ldx"
OP_NOTX: "notx"
OP_SUBX: "subx"
        
OP_JMP: "jmp"
OP_JCS: "jcs"
OP_JZ: "jz"

OP_LDPG: "ldpg"

OP_HLT: "hlt"

OP_OUT: "out"

statement: cmd | op

cmd: (CMD_ORG NUMBER
        | CMD_PAGE LABEL NUMBER)

_value: LABEL | NUMBER | LOCATION

op: [LABEL ":"] (OP_DCB NUMBER
        | OP_NOR _value
        | OP_ADD _value
        | OP_STA _value
        | OP_NORX _value
        | OP_ADDX _value
        | OP_STX _value
        | OP_JCC LABEL
        | OP_JNZ LABEL
        | OP_CLR
        | OP_LDA _value
        | OP_NOT
        | OP_SUB _value
        | OP_CLRX
        | OP_LDX _value
        | OP_NOTX
        | OP_SUBX _value
        | OP_JMP LABEL
        | OP_JCS LABEL
        | OP_JZ LABEL
        | OP_HLT
        | OP_LDPG LABEL
        | OP_OUT)


%import common.WS
%ignore WS

COMMENT: /#[^\n]*/
%ignore COMMENT
