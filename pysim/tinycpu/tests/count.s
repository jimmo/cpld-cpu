        lda count
cloop:  out
        add one
        jcc cloop

        hlt

count:  dcb 250
        
