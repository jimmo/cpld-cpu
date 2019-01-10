        lda allone
        sta ddra

        lda data
        sta porta

        nor allone
        ldx 1
        add data
        ldx 0
        sta porta

        nor allone
        ldx 2
        add data
        ldx 0
        sta porta

        nor allone
        ldx 3
        add data
        ldx 0
        sta porta
        
        hlt
        

data:   dcb 0
        dcb 64
        dcb 5
        dcb 3
        dcb 4
        dcb 5
        dcb 6
        dcb 7
        
