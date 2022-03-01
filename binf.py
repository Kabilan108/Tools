""" binf.py
These are methods, functions and classes that I've used for different
Bioinformatics Applications including custom implementation of certain
algorithms.
"""

# Imports
import Bio.Align as Align
import numpy as np
from typing import Union as _Union


# Definitions
def swalign(a: str, b: str, gap: int=-5, submat: Align.substitution_matrices.Array=None,
            scoreonly: bool=False, identonly: bool=False) -> _Union[int, float, dict]:
    """
    This is a custom implementation of the Smith-Waterman Local Sequence Alignment Algorithm.
    It is based on a code written by Dr. Ahmet Sacan <ahmetmsacan@gmail.com>
    It uses the Dynamic Programming algorithm to obtain an optimal sequence alignment.
    This function only supports linear gap penalties.
    @param a: str, b: str
        Sequences to align
    @param gap: int
        Gap score
    @param submat: Align.substitution_matrices.Array
        Scoring matrix (BLOSUM62 is the default)
    @param scoreonly: bool
        Return alignment score only
    @param identonly: bool
        Return percent identity only
    @return
        Alignment score, percent identiy, and or alignment
    """

    # Default substitution matrix
    if submat is None:
        submat = Align.substitution_matrices.load('BLOSUM62')
    # Define sequence lengths
    A = len(a)
    B = len(b)
    # Initialize Dynamic Programming (score) table
    T = np.zeros( (A+1, B+1) ).tolist()

    if scoreonly:
        for i in range(A):
            # Define variables that reference positions in the score table
            # This is a speed optimization - directly reference position instead of searching
            # for it each time
            submat_ai = submat[a[i]]
            Ti = T[i]
            Ti_plus1 = T[i+1]
            for j in range(B):
                # reset, diag, horz, vert.
                Ti_plus1[j+1] = max( 0, Ti[j]+submat_ai[b[j]], Ti_plus1[j]+gap, Ti[j+1]+gap )
        return np.max(T, axis=None)

    elif identonly:
        # Initialize counts
        MC = np.zeros((A+1, B+1), dtype=int).tolist() # match counts
        AL = np.zeros((A+1, B+1), dtype=int).tolist() # alignment lengths

        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i];	Ti_plus1 = T[i+1];
            MCi = MC[i];	MCi_plus1 = MC[i+1];
            ALi = AL[i];	ALi_plus1 = AL[i+1];

            for j in range(B):
                # reset, diag, horz, vert.
                options = ( 0, Ti[j]+submat_ai[b[j]], Ti_plus1[j]+gap, Ti[j+1]+gap )
                bestmove = np.argmax(options)
                Ti_plus1[j+1] = options[bestmove]

                if bestmove == 1: # Diagonal
                    MCi_plus1[j+1] = MCi[j] + (a[i] == b[j])
                    ALi_plus1[j+1] = ALi[j] + 1
                elif bestmove == 2: # Horizontal
                    MCi_plus1[j+1] = MCi_plus1[j]
                    ALi_plus1[j+1] = ALi_plus1[j] + 1
                elif bestmove == 3: # Vertical
                    MCi_plus1[j+1] = MCi[j+1]
                    ALi_plus1[j+1] = ALi[j+1] + 1

    else:
        # Store the best direction (we only keep one when there are multiple good options.)
        P = np.zeros((A+1, B+1), dtype=int).tolist()
        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Ti_plus1 = T[i+1]
            Pi_plus1 = P[i+1]

            for j in range(B):
                # reset, diag, horz, vert.
                options = ( 0, Ti[j]+submat_ai[b[j]], Ti_plus1[j]+gap, Ti[j+1]+gap )
                bestmove = np.argmax(options)
                Ti_plus1[j+1] = options[bestmove]
                Pi_plus1[j+1] = bestmove

    # Determine score positions
    scorepos = np.unravel_index(np.argmax(T, axis=None), (A+1, B+1))
    r,c = scorepos # r=scorepos[0]; c=scorepos[1]
    if identonly:
        # Compute and return percent identity
        return MC[r][c] / AL[r][c] * 100

    # Store alginment score
    score = T[r][c]

    # Reconstruct Alignment (#? Bactracking)
    align_a = []; align_b = []
    while T[r][c] != 0 and P[r][c] != 0:
        move = P[r][c]
        # Define alignment characters
        if move == 1:
            r = r-1
            c = c-1
            achar = a[r]
            bchar = b[c]
        elif move == 2:
            c = c-1
            achar = '-'
            bchar = b[c]
        elif move == 3:
            r = r-1
            achar = a[r]
            bchar = '-'

        align_a.append(achar); align_b.append(bchar);

    # Reverse alignments and convert to strings
    align_a.reverse(); align_b.reverse()
    align = [''.join(align_a), ''.join(align_b)]

    # Compute percent identity
    L = len(align[0])
    ident = np.count_nonzero([align[0][i] == align[1][i] for i in range(L)]) / L * 100

    return {'score': score, 'align': align, 'ident': ident}