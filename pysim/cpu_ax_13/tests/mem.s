        lda count

loop:   sub one
        out

        # Store to result+offset
        ldx offset
        sta result
        addx one
        stx offset
        clrx
        
        jnz loop

hlt

count:  dcb 20
offset: dcb 0
        dcb 0xaa
result: dcb 0
        # And 10 more uninitialized bytes.
