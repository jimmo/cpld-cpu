        lda count
cloop:  add one
        jcc cloop

done:   jcc done

count:  dcb 250
        
