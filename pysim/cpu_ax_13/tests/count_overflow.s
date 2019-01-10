        lda allone
        sta ddra

        lda zero
        
loop:   
        sta porta
        add one

        jmp loop

nn:     dcb 1
        
