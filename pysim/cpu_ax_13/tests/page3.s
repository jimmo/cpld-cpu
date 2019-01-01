# Use the `page` macro to simplify the previous example.

        lda allone
        sta ddra

        lda zero
        sta porta

start:  
        lda data_p0
        sta porta
        #out

        lda data_p1
        sta porta
        #out

        ldpg p1

        lda data_p0
        sta porta
        #out

        lda data_p1
        sta porta
        #out
        hlt

        #ldpg p2

        #lda data_p0
        #sta porta
        ##out

        #lda data_p2
        #sta porta
        #out

        #jmp code
        hlt

        org 230
data_p0:  dcb 7
        dcb 0x55

        org 240
ddra:   dcb 0
ddrb:   dcb 0
porta:  dcb 0
portb:  dcb 0
        
        org 248
bank0:  dcb 0
bank1:  dcb 0
        
        page p1 1
        
        org 230
        dcb 0xaa
data_p1: dcb 8


        
#         page p2 1
# data_p2: dcb 9

# code:   lda 33
#         sta porta
#         #out

#         ldpg p3
#         jmp resume
        
#         hlt


        
#         page p3 0
# resume: lda 3
#         add 3
#         add 3
#         add 3
#         add 3
#         add 3
#         #sta porta
#         #out
#         #out

#         hlt
        
