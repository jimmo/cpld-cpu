start: op+

LABEL_CHAR: "a".."z"|"0".."9"|"_"
LABEL: ("a".."z"|"_") LABEL_CHAR+

DEC_NUMBER: /[1-9]\d*l?/i
HEX_NUMBER: /0x[\da-f]*l?/i
OCT_NUMBER: /0o?[0-7]*l?/i
NUMBER: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER

OP_DCB: "dcb"

OP_NOR: "nor"
OP_ADD: "add"
OP_STA: "sta"
OP_JCC: "jcc"

OP_CLR: "clr"
OP_LDA: "lda"
OP_NOT: "not"
OP_JMP: "jmp"
OP_JCS: "jcs"
OP_SUB: "sub"
OP_HLT: "hlt"

OP_OUT: "out"

op: [LABEL ":"] (OP_DCB NUMBER
        | OP_NOR LABEL
        | OP_ADD LABEL
        | OP_STA LABEL
        | OP_JCC LABEL
        | OP_CLR
        | OP_LDA LABEL
        | OP_NOT
        | OP_JMP LABEL
        | OP_JCS LABEL
        | OP_SUB LABEL
        | OP_HLT
        | OP_OUT)


%import common.WS
%ignore WS

COMMENT: /#[^\n]*/
%ignore COMMENT
