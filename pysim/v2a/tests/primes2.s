        lda two
        out

start:  lda two
        sta subs

loop:   lda number

        # Keep 'subtracting' subs while we have a remainder.
inner:  sub subs
        jcc inner

        # Add back the final one.
        add subs

        # If non-zero (i.e. there was a remainder), this will set carry.
        jz noprime

        # 'add' two to subs (or one if 2)
        lda subs
        sub two
        jz inc23
        lda subs
        add two
        jmp inc
inc23:  lda subs
        add one
inc:    sta subs
        #out

        # Try the next dividend if subs * 2 < number
        lda subs
        add subs
        #sub one
        sub number
        jcs loop

        # No subs worked --> prime
        lda number
        out

        # Found a dividend, test the next odd number.
noprime:        lda number
        add two
        sta number
        jmp start

two:    dcb 2
subs:   dcb 0
number: dcb 3
wut:    dcb 80
