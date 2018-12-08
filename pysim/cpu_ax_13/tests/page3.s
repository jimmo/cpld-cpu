# Use the `page` macro to simplify the previous example.

start:  
        lda data_p0
        out

        lda data_p1
        out

        ldpg p1

        lda data_p0
        out

        lda data_p1
        out

        ldpg p2

        lda data_p0
        out

        lda data_p2
        out

        jmp code
        
data_p0:  dcb 7


        
        page p1 1
data_p1: dcb 8


        
        page p2 1
data_p2: dcb 9

code:   lda 33
        out

        ldpg p3
        jmp resume
        
        hlt


        
        page p3 0
resume: lda 3
        add 3
        add 3
        add 3
        add 3
        add 3
        out
        out

        hlt
        
