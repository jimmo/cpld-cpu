        lda zero
        out
        add one
        out
        add one
        out

        jmp high
        hlt
        
        org 200
high:   lda zero
        add one
        add one
        add one
        add one
        out
        hlt
        
