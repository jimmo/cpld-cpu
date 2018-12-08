loop:   
        lda rng
        out

        lda count
        jz end
        sub one
        sta count
        jmp loop

end:    hlt
        
count:  dcb 10
