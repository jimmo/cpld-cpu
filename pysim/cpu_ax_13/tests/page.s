# Simple demo to show that reading from bank 1 is affected by the bank1 register.

        org 0

        lda addr0
        out

        lda addr1
        out
        
        lda one
        sta bank1

        lda addr0
        out

        lda addr1
        out
        
        lda two
        sta bank1

        lda addr0
        out

        lda addr1
        out

        hlt

two:    dcb 2


        org 0x180
addr0:  dcb 7

        org 0x1180
addr1:  dcb 8
        
        org 0x2180
addr1a: dcb 9
