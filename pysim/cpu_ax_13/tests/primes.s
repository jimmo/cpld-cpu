        lda zero
        sta subs
        lda 3
        sta number

        lda allone
        sta ddra

        lda two
        sta porta

        # Wait for button press
wait1:  lda portb
        nor 254
        jz wait1
wait2:  lda portb
        nor 254
        jnz wait2
        
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

        # Wait for button press
wait3:  lda portb
        nor 254
        jz wait3
wait4:  lda portb
        nor 254
        jnz wait4

        # Found a dividend, test the next odd number.
noprime:
        lda number
        add two
        sta number
        jmp start

two:    dcb 2
subs:   dcb 0
number: dcb 3

