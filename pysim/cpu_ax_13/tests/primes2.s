        # Reset variables.
        lda 0
        sta subs
        lda 3
        sta number

        # Setup GPIO.
        lda allone
        sta ddra

        # Hardcode 2 as prime.
        lda 2
        sta porta

        # Wait for button press
wait1:  lda portb
        nor 254
        jz wait1
wait2:  lda portb
        nor 254
        jnz wait2

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

        # Try the next dividend if subs * 2 < number
        lda subs
        add subs
        sub number
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
        add 2
        sta number
        jmp start

subs:   dcb 0
number: dcb 3
