# by Ahmet Sacan.
# bmes.py should already be on the path.


from cmath import inf


def fasta_readfirst(file):
    from Bio import SeqIO

    for ret in SeqIO.parse(file, "fasta"):
        return ret


def sample_ratptn():
    import bmes

    file = bmes.downloadurl(
        "https://www.uniprot.org/uniprot/Q5Y4N8.fasta", "rat.agre1.ptn.fasta"
    )
    return fasta_readfirst(file)


def sample_humanptn():
    import bmes

    file = bmes.downloadurl(
        "https://www.uniprot.org/uniprot/Q14246.fasta", "human.agre1.ptn.fasta"
    )
    return fasta_readfirst(file)


def swalign(a, b, gap=-5, submat=None, scoreonly=False, identonly=False):
    import numpy

    if submat is None:
        from Bio import Align

        submat = Align.substitution_matrices.load("BLOSUM62")
    A = len(a)
    B = len(b)
    T = numpy.zeros((A + 1, B + 1)).tolist()  # score table
    if scoreonly:
        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Tiplus1 = T[i + 1]
            for j in range(B):
                Tiplus1[j + 1] = max(
                    0, Ti[j] + submat_ai[b[j]], Tiplus1[j] + gap, Ti[j + 1] + gap
                )
        return numpy.max(T, axis=None)

    elif identonly:
        MC = numpy.zeros((A + 1, B + 1), dtype=int).tolist()
        # match counts
        AL = numpy.zeros((A + 1, B + 1), dtype=int).tolist()
        # align lengths
        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Tiplus1 = T[i + 1]
            MCi = MC[i]
            MCiplus1 = MC[i + 1]
            ALi = AL[i]
            ALiplus1 = AL[i + 1]

            for j in range(B):
                options = (
                    0,
                    Ti[j] + submat_ai[b[j]],
                    Tiplus1[j] + gap,
                    Ti[j + 1] + gap,
                )
                # reset, diag, horz, vert
                bestmove = numpy.argmax(options)
                Tiplus1[j + 1] = options[bestmove]
                if bestmove == 1:
                    MCiplus1[j + 1] = MCi[j] + (a[i] == b[j])
                    ALiplus1[j + 1] = ALi[j] + 1
                    # diag
                elif bestmove == 2:
                    MCiplus1[j + 1] = MCiplus1[j]
                    ALiplus1[j + 1] = ALiplus1[j] + 1
                    # horz
                elif bestmove == 3:
                    MCiplus1[j + 1] = MCi[j + 1]
                    ALiplus1[j + 1] = ALi[j + 1] + 1
                    # vert

    else:
        P = numpy.zeros((A + 1, B + 1), dtype=int).tolist()
        # best direction (we only keep one when there are multiple good options.)
        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Tiplus1 = T[i + 1]
            Piplus1 = P[i + 1]
            for j in range(B):
                options = (
                    0,
                    Ti[j] + submat_ai[b[j]],
                    Tiplus1[j] + gap,
                    Ti[j + 1] + gap,
                )
                # reset, diag, horz, vert.
                bestmove = numpy.argmax(options)
                Tiplus1[j + 1] = options[bestmove]
                Piplus1[j + 1] = bestmove

    scorepos = numpy.unravel_index(numpy.argmax(T, axis=None), (A + 1, B + 1))
    r = scorepos[0]
    c = scorepos[1]
    if identonly:
        return MC[r][c] / AL[r][c] * 100

    score = T[r][c]

    # reconstruct the alignment:
    align_a = []
    align_b = []
    while T[r][c] != 0 and P[r][c] != 0:
        move = P[r][c]
        if move == 1:
            r = r - 1
            c = c - 1
            achar = a[r]
            bchar = b[c]
        elif move == 2:  # horz
            c = c - 1
            achar = "-"
            bchar = b[c]
        elif move == 3:  # vert
            r = r - 1
            achar = a[r]
            bchar = "-"

        align_a.append(achar)
        align_b.append(bchar)
    align_a.reverse()
    align_b.reverse()
    align = ["".join(align_a), "".join(align_b)]

    L = len(align[0])
    ident = (
        numpy.count_nonzero([align[0][i] == align[1][i] for i in range(L)]) / L * 100
    )

    # return {'score':score,'align':align,'scoretable':T,'pathtable':P}
    return {"score": score, "align": align, "ident": ident}


if __name__ == "__main__":
    pass
