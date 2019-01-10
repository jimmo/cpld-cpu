        lda allone
        sta ddra

        lda 0
        sta ddrb

loop:
        lda portb
        nand 1
        and 1
        shl
        shl
        sta porta
        jmp loop
