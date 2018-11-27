foo:
        load c:d, foo
        load a, 0x80
        load b, 0x80
        add a
        #cmp
        jc c:d
