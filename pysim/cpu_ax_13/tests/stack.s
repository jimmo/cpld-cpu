loop:   lda ii
        out
        jz end
        sub one
        sta ii
        
        lda nn       
        ldx _sp
        sta _stack
        clrx
        add one
        sta nn
        
        lda _sp
        add one
        sta _sp

        jmp loop

end:    
        hlt
        
nn:     dcb 32
ii:     dcb 10
