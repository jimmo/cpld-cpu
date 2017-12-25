start: statement+

ID_CHAR: "a".."z"|"_"
ID: ID_CHAR+

DEREF_ID: "[" ID "]"

DEC_NUMBER: /[1-9]\d*l?/i
HEX_NUMBER: /0x[\da-f]*l?/i
OCT_NUMBER: /0o?[0-7]*l?/i
CHR_NUMBER: /'.'/i
NUMBER: DEC_NUMBER | HEX_NUMBER | OCT_NUMBER | CHR_NUMBER

TYPE: "i8"|"i16"|"u8"|"u16"

BIN_OP: "+"|"-"|"&"|"|"|"^"
BIN_CMP: "=="|"!="|"<"|">"|"<="|">="

statement: TYPE ID "=" expr -> new_assign
    | ID "=" expr -> assign
    | DEREF_ID "=" expr -> deref_assign
    | "if" (ID | DEREF_ID | NUMBER) BIN_CMP (ID | DEREF_ID | NUMBER) "goto" ID -> goto
    | "goto" ID -> goto
    | ID ":" -> label
    | "hlt" -> hlt

?expr: "(" expr ")"
    | expr BIN_OP expr -> bin_op
    | NUMBER
    | (ID | DEREF_ID)

%import common.WS
%ignore WS

COMMENT: /#[^\n]*/
%ignore COMMENT
