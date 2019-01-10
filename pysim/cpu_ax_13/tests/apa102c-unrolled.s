        lda 0xff
        sta ddra

loop:   

        lda 32
        sta count
        lda 0
        sta porta
header:
        lda 0x40
        sta porta
        lda 0
        sta porta

        lda count
        sub 1
        sta count
        jnz header

        lda 10
        sta count
leds:
        # Brightness
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta

        # Blue
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta

        # Green
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta

        # Red
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0x80
        sta porta
        lda 0xc0
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta
        
        lda 0
        sta porta
        lda 0x40
        sta porta

        # Loop
        lda count
        sub 1
        sta count
        jnz leds

        lda 0xc02
        sta count
        lda 0x80
        sta porta
footer:
        lda 0xc0
        sta porta
        lda 0x80
        sta porta

        lda count
        sub 1
        sta count
        jnz footer
        
        jmp loop

count:  dcb 0
        
