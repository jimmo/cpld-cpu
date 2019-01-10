# Use the `page` macro to simplify the previous example.

start:  
        lda addr0
        out

        lda addr1a
        out
        
        lda one
        sta page1

        lda addr0
        out

        lda addr1a
        out
        
        lda two
        sta page1

        lda addr0
        out

        lda addr1a
        out

        jmp code


two:    dcb 2


        org 0x180
addr0:  dcb 7

        page p1 1
        org 0x180
addr1a: dcb 8
        
        page p2 1
        org 0x180
addr1b: dcb 9

num:    dcb 33

code:   lda num
        out

        lda threex
        sta page0
        jmp resume
        
        hlt

threex: dcb 3
        
        page p3 0
resume: lda three
        add three
        add three
        add three
        add three
        add three
        sta three
        out
        out

        hlt

three:  dcb 3
