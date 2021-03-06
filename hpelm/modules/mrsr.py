# -*- coding: utf-8 -*-
"""Multiresponse Sparse Regression algorithm in Python

Uses np library from Python

| Input:
| **T**    is an (n x p) matrix of targets. The columns of T should
      have zero mean and same scale (e.g. equal variance).
| **X**    is an (n x m) matrix of regressors. The columns of X should
      have zero mean and same scale (e.g. equal variance).
| **kmax** is an integer fixing the number of steps to be run, which
      equals to the maximum number of regressors in the model.
  
| Output:
| **W**    is an (m x p*kmax) sparse matrix of regression
      coefficients. It can be converted to full matrix by command   
      full(W). Regression coefficients of the k:th step are given
      by W(:,(k-1)*p+1:k*p).
| **i1**   is a (1 x kmax) vector of indices revealing the order in
      which the regressors enter model. 
 
The estimates for T may be obtained by Y = X*W, where the k:th
estimate Y(:,(k-1)*p+1:k*p) uses k regressors.
  
| Reference: 
| Timo Simila, Jarkko Tikka. Multiresponse sparse regression with
 application to multidimensional scaling. International Conference
 on Artificial Neural Networks (ICANN). Warsaw, Poland. September
 11-15, 2005. LNCS 3697, pp. 97-102.

Copyright (C) 2005 by Timo Simila and Jarkko Tikka.

This function is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License as
published by the Free Software Foundation; either version 2 of
the License, or any later version.   

The function is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE. See the `GNU
General Public License  <http://www.gnu.org/copyleft/gpl.html>`_  
for more details.
"""

import numpy as np


def mrsr(X, T, kmax):

    n,m = X.shape
    n,p = T.shape
    kmax = min(kmax, m)
    if p > 15:
        print "Too many targets (%d) - MRSR has O(2^targets) complexity"
    """    print "Reducing to 15 randomly selected targets (6x slowdown)"
        print "Using max 10 targets (1.08x slowdown) recommended"
        ti = np.arange(p)
        np.random.shuffle(ti)
        ti = ti[:15]
        T = T[:,ti]
        p = 15
    """
    i1 = np.array([], dtype = np.int32)
    i2 = np.arange(m).astype(np.int32)
    XT = np.dot(X.T,T)
    XX = np.zeros([m, m])
	
    S = np.ones([2**p, p])
    S[0:2**(p-1), 0] = -1
    for j in np.arange(1, p):
        S[:, j] = np.concatenate((S[np.arange(1, 2**p, 2), j-1], S[np.arange(1, 2**p, 2), j-1]))
	
	
	
    # Make the first step
	
    A     = np.transpose(XT)
    cmax  = np.amax(abs(A).sum(0), 0)
    cind  = np.argmax(abs(A).sum(0), 0)
    A     = np.delete(A, cind, 1)
    ind   = int(i2[cind])
    i2    = np.delete(i2, cind)
    i1    = np.append(i1, ind)
    # here Xi1 and Xi2 are just faster alternatives to X[:,i1] and X[:,i2]
    Xi2   = X.copy(order='F')  # column-contiguous copy of X
    Xi2[:, cind:-1] = Xi2[:, cind+1:];  Xi2   = Xi2[:,:-1]  # delete <cind> col
    Xi1   = X[:,ind].reshape((n,1))  # add 1 column at a time

    XX[np.ix_([ind], [ind])] = np.dot(X[:,ind], X[:,ind])
    
    invXX = 1 / XX[ind, :][ind]
    Wols  = invXX * XT[ind, :]
    Yols  = np.dot(Xi1, np.reshape(Wols, (1,-1)))
    B     = np.dot(Yols.T, Xi2)
    G     = (cmax+np.dot(S,A))/(cmax+np.dot(S,B))
    g     = G[G>=0].min()
    Y = g*Yols
	
    # Rest of the steps
    for k in np.arange(2,kmax+1):
        #print "calculating rank %d/%d" % (k-1, kmax)		
        #print "mrsr %d/%d" % (k+1, kmax)
  
        A    = np.dot((T-Y).T, Xi2)  # true slow
        cmax = np.amax(abs(A).sum(0), 0)
        cind = np.argmax(abs(A).sum(0), 0)
        A    = np.delete(A, cind, 1)
        ind  = int(i2[cind])
        i2   = np.delete(i2, cind)
        i1   = np.append(i1, ind)
        #Xi1  = np.hstack((Xi1, X[:,ind].reshape((n,1), order='C')))  # slow for large k
        Xi1  = np.hstack((Xi1, X[:,ind].reshape((-1,1))))  # slow for large k
        xX   = np.dot(X[:, ind].T, Xi1)
		
        XX[np.ix_([ind], i1)] = xX
        XX[np.ix_(i1, [ind])] = np.reshape(xX, (i1.size, -1))
	
        v3 = XX.take(i1,axis=0).take(i1,axis=1)  # XX[i1, :][:, i1]
        #v3 = XX[i1, :][:, i1]
        try:
            invXX = np.linalg.inv(v3)	   
        except np.linalg.linalg.LinAlgError:
            print 'got singular matrix, using pinv()', i1
            invXX = np.linalg.pinv(v3)
    
        Wols = np.dot(invXX, XT.take(i1,axis=0))
        Yols = np.dot(Xi1, Wols)  # true slow
        # deletes [cind] row, slow for large k
        Xi2[:, cind:-1] = Xi2[:, cind+1:];  Xi2 = Xi2[:,:-1]
        
        B    = np.dot((Yols-Y).T, Xi2)  # true slow
        
        G    = (cmax + S.dot(A)) / (cmax + S.dot(B))  # true slow for many outputs
        # now we remove that line using a condition:
        # G = numpy.concatenate(([2*(k==m)-1], G.flatten()), 1)
        if k == kmax:  # G[G>=0] is empty if k==kmax; empty.min() will give error
            Y = Yols
        else:
            g = G[G>=0].min()
            Y = (1-g)*Y+g*Yols
		
    return i1
	
