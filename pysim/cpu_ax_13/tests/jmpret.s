start:  lda 3
        out


        lda *
        add 12
        sta ret
        
        jmp fn

        lda 27
        out
        hlt


fn:     lda 7
        out

        lda ret
        sta thunk_
thunk:  jmp ret

ret:    dcb 0
        hlt
        
