        lda allone
        sta ddra

        lda two
        sta porta

start:  lda allone
        add allone
        sta subs
        # subs is 254 (i.e. -2)

loop:   lda number

        # Keep 'subtracting' subs while we have a remainder.
inner:  add subs
        jcs inner

        # Add back the final one.
        sub subs

        # If non-zero (i.e. there was a remainder), this will set carry.
        add allone
        jcc noprime

        # 'add' one to subs
        lda subs
        add allone
        sta subs

        # Try the next dividend if subs < number
        add number
        add allone
        jcs loop

        # No subs worked --> prime
        lda number
        sta porta

        # Found a dividend, test the next odd number.
noprime:        lda number
        add two
        sta number
        jmp start

two:    dcb 2
subs:   dcb 0
number: dcb 3

        org 240
ddra:   dcb 0
        org 242
porta:  dcb 0
        
