        lda 2
        out

start:  lda 2
        sta subs

loop:   lda number

        # Keep 'subtracting' subs while we have a remainder.
inner:  sub subs
        jcc inner

        # Add back the final one.
        add subs

        # If non-zero (i.e. there was a remainder), this will set carry.
        jz noprime

        # 'add' 2 to subs (or one if 2)
        lda subs
        sub 2
        jz inc23
        lda subs
        add 2
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
        add 2
        sta number
        jmp start

subs:   dcb 0
number: dcb 3
