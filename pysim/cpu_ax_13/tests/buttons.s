        lda allone
        sta ddra

        lda 0
        sta ddrb

loop:
        lda portb
        sta porta
        jmp loop
        
