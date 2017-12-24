start: op+

LABEL_CHAR: "a".."z"|"_"
LABEL: LABEL_CHAR+

DEC_NUMBER: /[1-9]\d*l?/i
HEX_NUMBER: /0x[\da-f]*l?/i
OCT_NUMBER: /0o?[0-7]*l?/i
NUMBER: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER

OP_ALU: "not"|"xor"|"or"|"and"|"add"|"sub"|"cmp"|"shl"|"shr"|"inc"|"dec"|"neg"|"clf"|"inv"|"rol"|"ror"
OP_LOAD: "load"
OP_LOAD8: "load"
OP_LOAD16: "load"
OP_MOV: "mov"
OP_MOV16: "mov"
OP_RMEM: "rmem"
OP_WMEM: "wmem"
OP_JMP: "jmp"|"jz"|"je"|"jnz"|"jne"|"jn"|"jp"|"jls"|"jges"|"jc"|"jlu"|"jnc"|"jgeu"|"jo"|"jno"

REG_ALU: "a"|"c"
REG_LOAD: "al"|"ah"|"bl"|"bh"|"cl"|"ch"|"dl"|"dh"
REG_LOAD8: "a"|"b"|"c"|"d"
REG_LOAD16: "a:b"|"b:c"|"c:d"
REG_MOV: "a"|"b"|"c"|"d"|"e"|"f"|"g"|"h"
REG_MOV16: "a:b"|"b:c"|"c:d"|"d:e"|"e:f"|"f:g"|"g:h"
REG_ADDR: "c:d"|"g:h"
REG_MEM: "a"|"e"

op: [LABEL ":"] (OP_ALU REG_ALU
                 | OP_LOAD REG_LOAD "," NUMBER
                 | OP_LOAD8 REG_LOAD8 "," NUMBER
                 | OP_LOAD16 REG_LOAD16 "," (NUMBER | LABEL)
                 | OP_MOV REG_MOV "," REG_MOV
                 | OP_MOV16 REG_MOV16 "," REG_MOV16
                 | OP_RMEM REG_MEM "," REG_ADDR
                 | OP_WMEM REG_ADDR "," REG_MEM
                 | OP_JMP REG_ADDR)


%import common.WS
%ignore WS

COMMENT: /#[^\n]*/
%ignore COMMENT
