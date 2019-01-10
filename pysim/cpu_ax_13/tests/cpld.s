        lda allone
        sta ddra


        lda start1
up:     sta porta
        add one
        jcc up

        lda start2
down:   sta porta
        sub one
        jnz down

        hlt
        
start1:  dcb 254
start2:  dcb 2      
        
