       
loop:   lda count
        sub one
        jcs end
        out
        sta count

op:     sta result

        lda op_
        add 2
        sta op_
        
        jmp loop
        
end:    hlt

count:  dcb 10
offset: dcb 0
result: dcb 0
