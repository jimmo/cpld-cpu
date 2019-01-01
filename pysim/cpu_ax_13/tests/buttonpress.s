        lda allone
        sta ddra

        lda 0
        sta ddrb

loop:
        lda portb
        nor 254
        sta porta
        jmp loop
        
        
        org 240
ddra:   dcb 0
ddrb:   dcb 0
porta:  dcb 0
portb:  dcb 0

