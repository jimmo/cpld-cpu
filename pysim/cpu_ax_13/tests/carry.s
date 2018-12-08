        lda two
        sub one
#        sub one
#        sub one
        jcc cc
        lda one
        out
        jmp part2
cc:     lda zero
        out

part2:  
        lda two
        sub one
#        sub one
#        sub one
        jcs cs
        lda zero
        out
        jmp part3
cs:     lda one
        out

part3:
        lda two
        sub two  # 0
        jnz znz
        lda zero
        out
        jmp part4
znz:     lda one
        out

part4:  
        lda two
        sub one
        sub one
        sub one
        add one # 0
        jz zz
        # it's non-zero
        lda one
        out
        jmp part5
zz:     # it's zero
        lda zero
        out

part5:  
        hlt
        
        
two:    dcb 2
        
