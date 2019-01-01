        lda allone
        sta ddra

start:  lda 3
        sta porta
        #out


        lda *
        add 12
        sta ret
        
        jmp fn

        lda 27
        sta porta
        #out
        hlt


fn:     lda 7
        sta porta
        #out

        lda ret
        sta thunk_
thunk:  jmp ret

ret:    dcb 0
        hlt
        
        org 240
ddra:   dcb 0
ddrb:   dcb 0
porta:  dcb 0
portb:  dcb 0
        
