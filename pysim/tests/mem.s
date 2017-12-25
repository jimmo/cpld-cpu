        load a, 0x10
        load b, 0x20
        load c:d, 0x0000
        wmem c:d, a
        load c:d, 0x0001
        wmem c:d, b

        load a, 0x00
        load b, 0x00
        load c:d, 0x0000
        rmem a, c:d
        load c:d, 0x0001
        rmem b, c:d

        hlt
