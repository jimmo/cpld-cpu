foo:    lda allone
        sta ddra

        lda nn
        sta porta
        add one
        sta nn

        jmp foo

nn:     dcb 1
        
        org 240
ddra:   dcb 0
        org 242
porta:  dcb 0
        
