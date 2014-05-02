#!/usr/bin/env python2

from sklearn.datasets import load_svmlight_file
from gzip import GzipFile
from Embedding import *
import cPickle as pickle
import os

from sklearn.feature_extraction.text import TfidfTransformer

LEN_BIN = len(' bin=')

class EmbeddingLoader:
    
    def __init__(self):
        self.emb = Embedding()
        
    def load(self, dirname, tfidf = False, svd_k = 0):
        self.dirname = dirname
        self.emb.x, self.emb.y = load_svmlight_file(dirname + EMBEDDING_FILENAME)
        
        if tfidf:
            tfidf = TfidfTransformer()
            self.emb.x =  tfidf.fit_transform(self.emb.x)

        if svd_k != 0:
            try:
                import sparsesvd
                import scipy.sparse
                
                X = self.emb.x.T
                X = scipy.sparse.csc_matrix(X)
                Ut, S, Vt = sparsesvd.sparsesvd(X, svd_k)
                self.emb.x = scipy.sparse.csr_matrix(Vt.T)


            except ImportError:
                print 'Warning: Cannot perform SVD without sparsesvd module'

        self._loadFeatureTable()
        self._loadTOC()
        self._loadDistances()
        return self.emb
    
    def _loadFeatureTable(self):
        
        filename = self.dirname + FEATURE_FILENAME
        if not os.path.exists(filename):
            return

        f  = GzipFile(filename)
        
        # discard first line
        f.readline()

        while True:
            line = f.readline().rstrip()
            if line == '': break
            
            (feat, n) = self._parseHashTableLine(line)
            
            self.emb.featTable[feat] = n
            self.emb.rFeatTable[n] = feat
            
        f.close()
    
    def _parseHashTableLine(self, line):
        n, feat = line[LEN_BIN+1:].split(':',1)
        n = int(n , 16)
        feat = feat.lstrip().rstrip()
        return (feat, n)

    def _loadTOC(self):
        filename = self.dirname + TOC_FILENAME
        f = file(filename)
        TOCLines = [x.rstrip() for x in f.readlines()]
        f.close()
        
        for i in range(len(self.emb.y)):
            label = self.emb.y[i]
            name = TOCLines[int(label)]
            self.emb.rTOC[name] = i
            self.emb.TOC.append(name)

    def _loadDistances(self):
        
        nniFilename = self.dirname + NNI_FILENAME
       
        if os.path.exists(nniFilename):
            import h5py
            self.emb.NNI = h5py.File(nniFilename, 'r')['distanceM']
            

if __name__ == '__main__':
    import sys
    s = EmbeddingLoader()
    s.load(sys.argv[1])
    
