        load a, 0
        load c:d, 0x80
        mov g:h, c:d

        load b, 0x8f

loop:
        # Write value
	wmem g:h, a

        # Save value
	mov e, a

        # Check and increment destination
	mov a, h
        cmp
        load c:d, done
        je c:d
	inc a
	mov h, a

        # Restore value
        mov a, e

        # Increment value
        inc a
        load c:d, loop
	jmp c:d

done:
        load c:d, done
        jmp c:d
