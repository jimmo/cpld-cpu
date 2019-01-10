        lda allone
        sta ddra

        lda 0
        sta ddrb

loop:
        lda portb
        nor 254
        sta porta
        jmp loop
