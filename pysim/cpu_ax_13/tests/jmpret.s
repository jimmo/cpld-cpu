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
