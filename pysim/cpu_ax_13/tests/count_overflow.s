        lda allone
        sta ddra

        lda zero
        
loop:   
        sta porta
        add one

        jmp loop

nn:     dcb 1
        
        org 240
ddra:   dcb 0
        org 242
porta:  dcb 0
        
