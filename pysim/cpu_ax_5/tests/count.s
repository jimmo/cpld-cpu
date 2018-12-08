        lda start1
up:     out
        add one
        jcc up

#         lda start2
# down:   out
#         sub one
#         jnz down

        hlt
        
start1:  dcb 250
start2:  dcb 7
        
