        # Fills up memory with 30..0
        # No indexing instructions, so uses self-modifying code to change offset.

        lda count
loop:   out
        sta count
        
        # Write to result+n
op:     sta result

        # Modify `op`
        lda op
        add one
        sta op

        # Subtract one from `count`
        lda count
        sub one
        jcc loop

done:   hlt

count:  dcb 30
result: dcb 0
        # ... and 29 more bytes left uninitialized.
        
