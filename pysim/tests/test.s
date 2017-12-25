# Fills 0x80 -> 0x8f with 00 -> 0f

        # Starting value
        load a, 0

        # Memory destination
        load c:d, 0x80
        mov g:h, c:d

        # Stop after this memory location
        load b, 0x8f

loop:
        # Write value
	wmem g:h, a

        # Save value
	mov e, a

        # Check and increment destination
	mov a, h
        load c:d, done
        cmp
        je c:d
	inc a
	mov h, a

        # Restore value
        mov a, e

        # Increment value
        inc a

        # Loop
        load c:d, loop
	jmp c:d

done:
        hlt
