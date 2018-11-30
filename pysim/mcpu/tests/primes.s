        lda two
        out

start:  lda allone
        add allone
        sta subs

loop:   lda number
inner:  add subs
        jcs inner

        sub subs
        add allone
        jcc noprime

        lda subs
        add allone
        sta subs

        add number
        add allone
        jcs loop

        lda number
        out

noprime:        lda number
        add two
        sta number

        jmp start

two:    dcb 2
subs:   dcb 0
number: dcb 3

