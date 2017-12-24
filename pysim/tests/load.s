load al, 1
load ah, 2
load bl, 3
load bh, 4
load cl, 5
load ch, 6
load dl, 7
load dh, 8

mov e, a
mov f, b
mov g, c
mov h, d

add a
add c
sub a
sub c

load c:d, 0x10
mov g:h, c:d
load c:d, 0x20
load a, 0x23
wmem c:d, a
load a, 0x45
mov e, a
wmem g:h, e

load a, 0
load c:d, 0x80
mov g:h, c:d
load c:d, loop

loop:
inc a
wmem g:h, a
mov e, a
mov a, h
inc a
mov h, a
mov a, e
jmp c:d
