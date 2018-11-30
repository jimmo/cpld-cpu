        lda count

loop:   sub one

        # Store to result+offset
        ldx offset
        sta result
        addx one
        stx offset
        clrx
        
        jnz loop

hlt

count:  dcb 255
offset: dcb 0
result: dcb 0
        # And 10 more uninitialized bytes.
