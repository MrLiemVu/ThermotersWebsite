
# find positions of elements in the list
def pozicija(testlist, cond):
    '''
    This function returns a list of indices of elements
    in `testlist` that satisfy the condition `cond`.
    
    Parameters:
        testlist : The list to search.
        cond : The condition to satisfy.
    
    Returns:
        [i for i,x in enumerate(testlist) if cond(x)] : The list of indices of elements that satisfy the condition.
    '''
    return [i for i,x in enumerate(testlist) if cond(x)]

def polynom(c, x):
    '''
    Calculate a polynomial.
    
    Parameters:
        c : The coefficients of the polynomial.
        x : The variable of the polynomial.
    
    Returns:
        npsum(out, axis=0) : The value of the polynomial.
    '''
    from numpy import sum as npsum
    
    out = [k*x**j for j,k in enumerate(c)]
    return npsum(out, axis=0)

def is_number(x):
    return isinstance(x, int) # Test this
    try:
        int(eval(x))
        return True
    except:
        return False

def mode(l): # Why not use np mode?
    
    from collections import Counter
    
    return Counter(l).most_common(1)[0][0]

def moving_average(a, n=3) :
    '''
    Calculate the moving average of a time series.
    
    Parameters:
        a : The time series.
        n : The number of points to average.
    
    Returns:
        ret[n - 1:] / n : The moving average of the time series.
    '''
    from numpy import cumsum
    
    ret = cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:] / n

def moving_sum(a, n=3) :
    '''
    Calculate the moving sum of a time series.
    
    Parameters:
        a : The time series.
        n : The number of points to sum.
    
    Returns:
        ret[n - 1:] / n : The moving sum of the time series.
    '''
    from numpy import cumsum
    
    ret = cumsum(a, dtype=float)
    ret[n:] = ret[n:] - ret[:-n]
    return ret[n - 1:]

def autocorr(sett, dtrange, nsplits = 1):
    '''
    Autocorrelation function.
    
    Parameters:
        sett : The time series.
        dtrange : The range of time lags.
        nsplits : The number of splits.
    
    Returns:
        out : The autocorrelation function.
    '''
    from numpy import zeros, corrcoef, array, mean, std
    
    if nsplits == 1:
        ret = zeros(len(dtrange))
        for k,i in enumerate(dtrange):
            if i==0:
                ret[k] = 1.
            else:
                ret[k] = corrcoef(sett[:len(sett)-i],sett[i:])[0,1]
        return ret
    else:
        out = []        
        for j in range(nsplits):
            ret = zeros(len(dtrange))
            ss = sett[j*len(sett)//nsplits : (j+1)*len(sett)//nsplits]
            for k,i in enumerate(dtrange):
                if i==0:
                    ret[k] = 1.
                else:
                    ret[k] = corrcoef(ss[:len(ss)-i],ss[i:])[0,1]
            out += [ret]
        out = array(out)
        return ( mean(out,axis=0), std(out,axis=0) )

def OU(theta, mu, sigma, tmax, x0, dt):
    '''
    Simulate an Ornstein-Uhlenbeck process with parameters theta, mu, sigma
    and initial condition x0 for a time tmax with time step dt.
    
    Parameters:
        theta : The parameter of the Ornstein-Uhlenbeck process.
        mu : The mean of the Ornstein-Uhlenbeck process.
        sigma : The standard deviation of the Ornstein-Uhlenbeck process.
        tmax : The maximum time.
        x0 : The initial condition.
        dt : The time step.
    
    Returns:
    
    '''
    from random import randn
    from numpy import empty
    
    maxindex = int(float(tmax)/dt)
    x = empty(maxindex)
    x[0] = x0
    w  = randn(maxindex)
    a1 = 1.-theta*dt
    a2 = mu*theta*dt
    b  = sigma*dt**.5*w
    for t in range(maxindex-1):
        x[t + 1] = a1 * x[t] - a2 + b[t]
    return x


def order(unordered_list):
    '''
    Return the order of elements in a list.
    
    Parameters:
        unordered_list : The list to order.
    
    Returns:
        out : The order of the elements in the list.
    '''
    import numpy as np
    

    tmp = sorted([[i, el] for i, el in enumerate(unordered_list)], key=lambda xi: xi[1])
    return np.array([el[0] for el in tmp])
    
def tally(mylist, pandas=False):
    ''' 
    Tally elements in a list
    
    Parameters:
        mylist : The list to tally.
        pandas : Whether to tally from pandas series, default = False.
    
    Returns:
        out : The tally of the elements in the list.
    '''
    if pandas:
        import pandas as pd
        return pd.Series(mylist).value_counts().sort_index()
    
    from collections import Counter
    return sorted(Counter(mylist).most_common(), key=lambda duple: duple[0])

def multi_map(some_function, iterable, processes=1):
    '''
    Apply a function to an iterable using multiple processes.
    
    Parameters:
        some_function : The function to apply to the iterable.
        iterable : The iterable to apply the function to.
        processes : The number of processes to use.
    
    Returns:
        out : The output of the function applied to the iterable.
    '''
    assert type(processes) == int
    if processes == 1:
        out = map(some_function, iterable)
    elif processes > 1:
        from multiprocessing import Pool
        pool = Pool(processes)
        out  = pool.map(some_function, iterable)
        pool.close()
        pool.join()
    else:
        print ("invalid number of processes", processes)
        quit()
    return out


from contextlib import contextmanager
@contextmanager
def suppress_stdout():
    ''' Suppress the output of a block of code. '''
    import sys, os
    

    with open(os.devnull, "w") as devnull:
        old_stdout = sys.stdout
        sys.stdout = devnull
        try:  
            yield
        finally:
            sys.stdout = old_stdout

def stochasticMaximize(fun,x0,steps = 10000, temp = 1., step = .1):
    '''
    Stochastic optimization of a function.
    
    Parameters:
        fun : The function to optimize.
        x0 : The initial guess.
        steps : The number of steps to take.
        temp : The temperature of the system.
        step : The step size.
    
    Returns:
        outPars : The optimized parameters.
        fun(outPars) : The value of the function at the optimized parameters.
    '''
    import numpy as np
    
    global exponent, MCMC
    exec(open('MCMCworker_RNApOnly_exclusions.py').read())
    from os.path import expanduser
    import numpy as np

    nPars = len(x0)
    exponent = fun
    mcmc = MCMC(x0, Nsave=10*nPars, filename=expanduser('~/tmp/mcmc'), step = step, temp = temp, exclude=np.array([],dtype=int))
    mcmc = MCMC(x0, Nsave=10*nPars, filename=expanduser('~/tmp/mcmc'), step = step, temp = temp, exclude=np.array([],dtype=int))
    mcmc.cycle(steps,adjust=True)
    outPars = np.loadtxt(mcmc.filename+".out", skiprows=steps//10//nPars*9//10)[:,1:-1].mean(axis=0)
    return outPars, fun(outPars)
 
def deep_getsizeof(obj, ids):
    """Find the memory footprint of a Python object
 
    This is a recursive function that drills down a Python object graph
    like a dictionary holding nested dictionaries with lists of lists
    and tuples and sets.
 
    The sys.getsizeof function does a shallow size of only. It counts each
    object inside a container as pointer only regardless of how big it
    really is.
 
    :param o: the object
    :param ids:
    :return:
    """
    from collections.abc import Mapping, Container
    from sys import getsizeof

    d = deep_getsizeof
    if id(obj) in ids:
        return 0
 
    curr_size = getsizeof(obj)
    ids.add(id(obj))
 
    if isinstance(obj, str) or isinstance(0, str):
        return curr_size
 
    if isinstance(obj, Mapping):
        return curr_size + sum(d(key, ids) + d(val, ids) for key, val in obj.iteritems())
 
    if isinstance(obj, Container):
        return curr_size + sum(d(x, ids) for x in obj)
 
    return curr_size 

import numpy as np

def tensum(values, indices):
    """
    Calculates the sum of values at specified indices.

    Parameters:
        values: A 1D numpy array of values.
        indices: A 2D numpy array of indices, where each row represents a set of indices.

    Returns:
        A 1D numpy array of the same length as indices, where each element is the sum of values at the corresponding indices.
    """
    return np.array([np.sum(values[idx]) for idx in indices])

def bindingEnergies(matrix, sequences):
    """
    Calculates the binding energies of sequences to a matrix.

    Parameters:
        matrix: A 2D numpy array representing the binding matrix. matrix.shape is (L,4)
        sequences: A 2D numpy array of sequences, where each row represents a sequence. seqs.shape is (n, L),

    Returns:
        A 1D numpy array of binding energies, where each element corresponds to the binding energy of the corresponding sequence.
    """
    assert matrix.shape[0] == sequences.shape[1]
    ns = len(sequences)
    L = len(sequences[0])
    energies = np.zeros(ns)
    for i in range(ns):
        for j in range(L):
            energies[i] += matrix[j, sequences[i, j]]
    return energies
    # return np.array([np.sum(matrix[seq]) for seq in sequences])

# def getDiNu(coord1, coord2, n1, minSpacer, n2, sequences, nSpacer):
#     """
#     Calculates the dinucleotide indices for a given set of coordinates.

#     Parameters:
#         coord1: The first coordinate.
#         coord2: The second coordinate.
#         n1: The size of the first matrix.
#         minSpacer: The minimum spacer length.
#         n2: The size of the second matrix.
#         sequences: A 2D numpy array of sequences.
#         nSpacer: The number of spacers.

#     Returns:
#         A 2D numpy array of dinucleotide indices, where each row represents a dinucleotide index.
#     """
#     nSeq, seqL = sequences.shape
#     Lout = seqL - n1 - n2 - minSpacer + 1
#     out = np.zeros((nSpacer, Lout, nSeq), dtype=int)
#     for iS in range(nSpacer):
#         for iL in range(Lout):
#             for iSeq in range(nSeq):
#                 out[iS, iL, iSeq] = sequences[iSeq, coord1 + iL + iS] * n1 + sequences[iSeq, coord2 + iL + iS]
#     return out

def getDiNu(p1,b1,p2, b2, n1, minSpacer, n2, sequences, nSpacer):
    
    minMsize = minSpacer+n1+n2
    nSeq = sequences.shape[0]
    seqL = sequences.shape[1]
    diNu = np.zeros((nSpacer,seqL-minMsize-nSpacer+1,nSeq),dtype=np.intc)#.astype(np.int32)
    diNu_view = diNu.view()
    
    if p1>=n1: p1 -= nSpacer//2
    if p2>=n1: p2 -= nSpacer//2

    for iS in range(nSpacer):
        x0 = nSpacer-iS
        for i in range(x0,seqL-minMsize-iS+1):
            for js in range(nSeq):
                if sequences[js][i+p1]==b1 and sequences[js][i+p2]==b2:
                    diNu_view[iS,i-x0,js] = 1
#                     diNu[iS,i-x0,js] = 1
        if p1>=n1: p1 += 1
        if p2>=n1: p2 += 1

    return diNu