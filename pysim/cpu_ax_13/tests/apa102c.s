        lda 0xff
        sta ddra
        lda 0x00
        sta ddrb
        sta red
        sta green
        sta blue
        jmp loop

fn_thunk:
        jmp fn_ret
fn_ret: dcb 0        
fn_data:dcb 0
        
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
        dec
        sta count
        jnz header

        lda 10
        sta count
leds:
        
        lda brightness
        sta fn_data
        lda *
        add 12
        sta fn_ret
        jmp fn
        
        lda blue
        sta fn_data
        lda *
        add 12
        sta fn_ret
        jmp fn
        
        lda green
        sta fn_data
        lda *
        add 12
        sta fn_ret
        jmp fn
        
        lda red
        sta fn_data
        lda *
        add 12
        sta fn_ret
        jmp fn        
        
        # Loop
        lda count
        dec
        sta count
        jnz leds

        lda 32
        sta count
        lda 0x80
        sta porta
footer:
        lda 0xc0
        sta porta
        lda 0x80
        sta porta

        lda count
        dec
        sta count
        jnz footer


        lda portb
        nor 254
        jz done_b0
        lda red
        add 64
        sta red
done_b0:
        lda portb
        nor 253
        jz done_b1
        lda green
        add 64
        sta green
done_b1:
        lda portb
        nor 251
        jz done_b2
        lda blue
        add 64
        sta blue
done_b2:
        
        jmp loop

fn:
        lda 8
        sta bit
fn_loop:
        lda fn_data
        and 0x80
        sta porta
        or 0x40
        sta porta
        lda fn_data
        shl
        sta fn_data
        lda bit
        dec
        sta bit
        jnz fn_loop

        lda fn_ret
        sta fn_thunk_
        jmp fn_thunk

        

count:  dcb 0
bit:    dcb 0
brightness: dcb 0b11100100
red:    dcb 0
green:  dcb 0
blue:   dcb 0
        
