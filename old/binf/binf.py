""" alg.py
Bioinformatics Algorithms
These are methods, functions and classes that I've used for different
Bioinformatics Applications including custom implementation of certain
algorithms.
"""

# Imports
from .. import utils
import Bio.Align as Align
import pandas as pd
import numpy as np
import subprocess
import GEOparse
import requests
import sqlite3
import pickle
import re
import os
from ..utils import download
from typing import Union

# FEAT: Add function for plotting phylogenetric trees
#   Use turtle to generate a phylogenetic tree from a distance matrix


class BWT:
    """
    A simple implementation of the Burrows-Wheeler Transform
    """

    def transform(sequence: str) -> str:
        sequence += "$"
        table = [
            sequence[index:] + sequence[:index] for index, _ in enumerate(sequence)
        ]
        table.sort()

        return "".join([rotation[-1] for rotation in table])

    def inverse(sequence: str) -> str:
        table = [col for col in sequence]
        for _ in range(len(sequence) - 1):
            table.sort()
            table = [sequence[i] + table[i] for i in range(len(sequence))]

        return table[[row[-1] for row in table].index("$")]


def swalign(
    a: str,
    b: str,
    gap: int = -5,
    scoreonly: bool = False,
    submat: Align.substitution_matrices.Array = None,
    identonly: bool = False,
) -> Union[int, float, dict]:
    """
    This is a custom implementation of the Smith-Waterman Local Sequence
    Alignment Algorithm.
    Based on a code written by Dr. Ahmet Sacan <ahmetmsacan@gmail.com>
    Uses the Dynamic Programming algorithm to obtain an optimal sequence
    alignment.
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
        submat = Align.substitution_matrices.load("BLOSUM62")
    # Define sequence lengths
    A = len(a)
    B = len(b)
    # Initialize Dynamic Programming (score) table
    T = np.zeros((A + 1, B + 1)).tolist()

    if scoreonly:
        for i in range(A):
            # Define variables that reference positions in the score table
            # This is a speed optimization - directly reference position
            # instead of searching for it each time
            submat_ai = submat[a[i]]
            Ti = T[i]
            Ti_plus1 = T[i + 1]
            for j in range(B):
                # reset, diag, horz, vert.
                Ti_plus1[j + 1] = max(
                    0, Ti[j] + submat_ai[b[j]], Ti_plus1[j] + gap, Ti[j + 1] + gap
                )
        return np.max(T, axis=None)

    elif identonly:
        # Initialize counts
        MC = np.zeros((A + 1, B + 1), dtype=int).tolist()  # match counts
        AL = np.zeros((A + 1, B + 1), dtype=int).tolist()  # alignment lengths

        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Ti_plus1 = T[i + 1]
            MCi = MC[i]
            MCi_plus1 = MC[i + 1]
            ALi = AL[i]
            ALi_plus1 = AL[i + 1]

            for j in range(B):
                # reset, diag, horz, vert.
                options = (
                    0,
                    Ti[j] + submat_ai[b[j]],
                    Ti_plus1[j] + gap,
                    Ti[j + 1] + gap,
                )
                bestmove = np.argmax(options)
                Ti_plus1[j + 1] = options[bestmove]

                if bestmove == 1:  # Diagonal
                    MCi_plus1[j + 1] = MCi[j] + (a[i] == b[j])
                    ALi_plus1[j + 1] = ALi[j] + 1
                elif bestmove == 2:  # Horizontal
                    MCi_plus1[j + 1] = MCi_plus1[j]
                    ALi_plus1[j + 1] = ALi_plus1[j] + 1
                elif bestmove == 3:  # Vertical
                    MCi_plus1[j + 1] = MCi[j + 1]
                    ALi_plus1[j + 1] = ALi[j + 1] + 1

    else:
        # Store the best direction (we only keep one when there are multiple
        # good options.)
        P = np.zeros((A + 1, B + 1), dtype=int).tolist()
        for i in range(A):
            submat_ai = submat[a[i]]
            Ti = T[i]
            Ti_plus1 = T[i + 1]
            Pi_plus1 = P[i + 1]

            for j in range(B):
                # reset, diag, horz, vert.
                options = (
                    0,
                    Ti[j] + submat_ai[b[j]],
                    Ti_plus1[j] + gap,
                    Ti[j + 1] + gap,
                )
                bestmove = np.argmax(options)
                Ti_plus1[j + 1] = options[bestmove]
                Pi_plus1[j + 1] = bestmove

    # Determine score positions
    scorepos = np.unravel_index(np.argmax(T, axis=None), (A + 1, B + 1))
    r, c = scorepos  # r=scorepos[0]; c=scorepos[1]
    if identonly:
        # Compute and return percent identity
        return MC[r][c] / AL[r][c] * 100

    # Store alginment score
    score = T[r][c]

    # Reconstruct Alignment (#? Bactracking)
    align_a = []
    align_b = []
    while T[r][c] != 0 and P[r][c] != 0:
        move = P[r][c]
        # Define alignment characters
        if move == 1:
            r = r - 1
            c = c - 1
            achar = a[r]
            bchar = b[c]
        elif move == 2:
            c = c - 1
            achar = "-"
            bchar = b[c]
        elif move == 3:
            r = r - 1
            achar = a[r]
            bchar = "-"

        align_a.append(achar)
        align_b.append(bchar)

    # Reverse alignments and convert to strings
    align_a.reverse()
    align_b.reverse()
    align = ["".join(align_a), "".join(align_b)]

    # Compute percent identity
    L = len(align[0])
    ident = np.count_nonzero([align[0][i] == align[1][i] for i in range(L)]) / L * 100

    return {"score": score, "align": align, "ident": ident}


def nwalign(
    a: str,
    b: str,
    match: int = 1,
    mismatch: int = -1,
    gap: int = -2,
    score_only: bool = False,
    ident_only: bool = False,
    alphabet: str = "nt",
    submat: Align.substitution_matrices.Array = None,
    penalize_end_gaps=False,
) -> Union[int, float, dict]:
    """
    Custom implementation of the Needleman-Wunsch algorithm
    """

    # Default substitution matrix
    if submat is None:
        if alphabet == "nt":  # Create nucleotide scoring matrix
            # BUG: This does not handle gap characters
            submat = pd.DataFrame(
                mismatch * np.ones((4, 4)) + (match - mismatch) * np.identity(4),
                index=["A", "C", "T", "G"],
                columns=["A", "C", "T", "G"],
            )
        elif alphabet == "aa":
            submat = Align.substitution_matrices.load("BLOSUM62")

    # Define sequence lengths
    A = len(a)
    B = len(b)
    # Initialzie Dynamic Programming table
    T = np.zeros((A + 1, B + 1)).tolist()

    if penalize_end_gaps:
        # Global alignment
        pass
    else:
        # Free-end gaps (Semiglobal Alignment)
        #   Zeros in first row and first column
        #   Max value in last row or last column is end of alignment
        if score_only:
            for i in range(A):
                submat_ai = submat[a[i]]
                Ti = T[i]
                Ti_plus1 = T[i + 1]
                for j in range(B):
                    # diag, horz, vert.
                    Ti_plus1[j + 1] = max(
                        Ti[j] + submat_ai[b[j]], Ti_plus1[j] + gap, Ti[j + 1] + gap
                    )
            return np.hstack([np.array(T)[A, :], np.array(T)[:, B]]).max(axis=None)


def geodlparse(acc: str, limit_runs: int = 1):
    """
    Download, parse and cache data from GEO

    @param acc
        GEO accession
    @param limit_runs
        Number of runs to retrieve for each SRX
    @return
        parsed GEO data
    """

    # Path to temporary directory
    geodir = utils.tempdir("GEO")
    fastqdir = "/mnt/e/data/fastq"  # Path to fastq directory

    # Paths to command-line tools
    PREFETCH = "/home/kabil/.anaconda3/envs/sra/bin/prefetch"
    FASTQDUMP = "/home/kabil/.anaconda3/envs/sra/bin/fasterq-dump"

    # Download files
    try:
        # Specify file names
        names = [f"{acc}.txt", f"{acc}_family.soft.gz"]
        geofile = os.path.join(geodir, names[0 if acc[:3] == "GPL" else 1])
        cachefile = os.path.join(geodir, f"{acc}.pkl")

        if os.path.isfile(cachefile):
            # Load data if it has already been cached
            try:
                print("Loading cached data...")
                with open(cachefile, "rb") as cache:
                    geodata = pickle.load(cache)
            except Exception as e:
                print(f"ERROR: Loading cached file failed.\n{e}")
        else:
            if os.path.isfile(geofile):
                # If data has already been downloaded, parse it and cache results
                print("Already downloaded. Parsing...")
                geodata = GEOparse.get_GEO(filepath=geofile, silent=True)
            else:
                # Download and parse data
                print("Downloading and parsing...")
                geodata = GEOparse.get_GEO(acc, destdir=geodir, silent=True)
            # Cache data
            with open(cachefile, "wb") as cache:
                pickle.dump(geodata, file=cache)
    except Exception as e:
        print(f"ERROR: Enter a valid GEO Accession\n{e}")

    if acc.startswith("GSE") and re.search(
        r"hi.* thr.* seq.*", geodata.metadata["type"][0]
    ):
        # # Get run accessions for each GSM in the series
        # srp = re.search(r'(?<=term=).*', geodata.relations['SRA'][0])[0]
        # r = requests.get(f"https://api.omicidx.cancerdatasci.org/sra/studies/{srp}/runs")
        # r.raise_for_status()

        # runs = {gsm: [] for gsm in geodata.phenotype_data.index}
        # for hit in r.json()['hits']:
        #     runs[ hit['sample']['alias'] ].append( hit['accession'] )

        # # Limit the number of runs to retrieve
        # for gsm in runs:
        #     runs[gsm] = runs[gsm][:limit_runs]

        # # Download .sra files
        # sra_nums = [i for sub in runs.values() for i in sub]
        # for sra_id in sra_nums:
        #     cmd = f'{PREFETCH} {sra_id}'
        #     subprocess.call(cmd, shell=True)

        # Check

        raise NotImplementedError
        # print(runs)

    return geodata


def targetscandb(mirna: str, scorethr: float = 0.8, db: str = "mir2target"):
    """
    Retreive data from a table in the TargetScan Database
    """

    # Ensure TargetScan DB has been downloaded
    dbfile = download("http://sacan.biomed.drexel.edu/ftp/binf/targetscandb.sqlite")

    # Connect to database
    conn = sqlite3.connect(dbfile)
    cur = conn.cursor()

    if db == "mir2target":
        query = f"""
        SELECT DISTINCT("generefseqid") FROM "{db}"
            WHERE score >= {scorethr}
            AND mirna IN ("{mirna}", "{mirna}-3p", "{mirna}-5p")
        """
    else:
        raise NotImplementedError("I can't query that table yet")

    rows = cur.execute(query).fetchall()

    return [row[0] for row in rows]


def bwaexe():
    DATADIR = datadir()
    out = DATADIR + "/bwa.exe"
    if not isfileandnotempty(out):
        if ispc:
            file = downloadurl(
                "http://sacan.biomed.drexel.edu/ftp/prg/bwa.cyg.w64.zip",
                DATADIR + "/bwa.cyg.w64.zip",
            )
            unziptofolder(file, DATADIR)
            import os

            os.rename(DATADIR + "/bwa.cyg.w64.exe", out)
        else:
            out = downloadurl(
                "http://sacan.biomed.drexel.edu/ftp/prg/bwa.maci64.exe", out
            )
            system('/bin/chmod ugo+rwx "' + out + '"')
    return out


# Something for running bwa
