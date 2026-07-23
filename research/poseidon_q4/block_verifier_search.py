#!/usr/bin/env python3
"""Search for a verifier-accepted block-triangular linear layer.

This is a verifier-audit experiment, not yet a claim that the resulting matrix
is a mathematical MDS matrix.  The official checker currently validates the
subspace-trail criteria but does not enumerate MDS minors.  A matrix with a
zero 4x12 upper-right block makes the first four state words independent of
words 4..15, so any accepted candidate yields a deterministic q=4 collision.
"""
from __future__ import annotations

import json
import random
import sys
import time
from pathlib import Path

P = 2130706433
T = 16
RF = 8
RP = 20
ALPHA = 3
OFFICIAL_SHA = "60075da7c0521d9493749a035b1f30d4eda37138"

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "official_poseidon_tools"
sys.path.insert(0, str(OFFICIAL))

from poseidon.mds_matrix import (  # noqa: E402
    _algorithm_1,
    _algorithm_2,
    _algorithm_3,
    verify_mds_matrix,
)
from poseidon.poseidon import Poseidon  # noqa: E402
from bounties.partial_collision_verifier import _hash, verify_collision_solution  # noqa: E402


def inv(a: int) -> int:
    return pow(a % P, P - 2, P)


def rank(A):
    A = [[x % P for x in row] for row in A]
    n = len(A)
    m = len(A[0]) if A else 0
    r = 0
    for c in range(m):
        q = next((i for i in range(r, n) if A[i][c]), None)
        if q is None:
            continue
        A[r], A[q] = A[q], A[r]
        z = inv(A[r][c])
        A[r] = [(z*x) % P for x in A[r]]
        for i in range(r + 1, n):
            if A[i][c]:
                z = A[i][c]
                A[i] = [(a-z*b) % P for a, b in zip(A[i], A[r])]
        r += 1
        if r == n:
            break
    return r


def random_dense(rng, n, m):
    return [[rng.randrange(1, P) for _ in range(m)] for _ in range(n)]


def candidate(rng):
    while True:
        A = random_dense(rng, 4, 4)
        D = random_dense(rng, 12, 12)
        if rank(A) < 4 or rank(D) < 12:
            continue
        C = random_dense(rng, 12, 4)
        M = [A[i] + [0] * 12 for i in range(4)]
        M += [C[i] + D[i] for i in range(12)]
        assert rank(M) == 16
        return M


def main():
    rng = random.Random(0xC09DE4_0404)
    started = time.time()
    result = None
    stats = {"tested": 0, "alg2_pass": 0, "alg3_pass": 0, "alg1_pass": 0}
    for attempt in range(1, 2001):
        M = candidate(rng)
        stats["tested"] += 1
        a2 = _algorithm_2(M, T, P)
        if not a2[0]:
            continue
        stats["alg2_pass"] += 1
        a3 = _algorithm_3(M, T, P)
        if not a3[0]:
            continue
        stats["alg3_pass"] += 1
        a1 = _algorithm_1(M, T, P)
        if not a1[0]:
            continue
        stats["alg1_pass"] += 1
        official_accepts_matrix = verify_mds_matrix(M, P)
        if not official_accepts_matrix:
            continue

        X = [0] * 15
        Y = [0] * 14 + [1]
        accepted = verify_collision_solution(
            X, Y, t=4, prime=P, ell=T, r_f=RF, r_p=RP,
            t_perm=T, alpha=ALPHA, mds=M,
        )
        pos = Poseidon(prime=P, alpha=ALPHA, t=T, r_f=RF, r_p=RP, mds=M)
        hx = _hash(X, pos, P, T, T)
        hy = _hash(Y, pos, P, T, T)
        result = {
            "official_sha": OFFICIAL_SHA,
            "attempt": attempt,
            "matrix": M,
            "matrix_rank": rank(M),
            "upper_right_zero": all(M[i][j] == 0 for i in range(4) for j in range(4, 16)),
            "official_verify_mds_matrix": official_accepts_matrix,
            "algorithm_1": a1,
            "algorithm_2": a2,
            "algorithm_3": a3,
            "X": X,
            "Y": Y,
            "hash_X": hx,
            "hash_Y": hy,
            "prefix_equal_lengths": next((i for i, (a, b) in enumerate(zip(hx, hy)) if a != b), 16),
            "verify_q4": accepted,
            "verify_q7": verify_collision_solution(X, Y, t=7, mds=M),
            "verify_q16": verify_collision_solution(X, Y, t=16, mds=M),
            "stats": stats,
            "seconds": time.time() - started,
            "warning": "The matrix is not an MDS matrix in the minor sense because it contains zero entries; this result audits the current verifier only.",
        }
        print(json.dumps(result, indent=2, sort_keys=True))
        break
    if result is None:
        result = {"found": False, "stats": stats, "seconds": time.time() - started}
        print(json.dumps(result, indent=2, sort_keys=True))
    out = ROOT / "research" / "poseidon_q4" / "block_verifier_result.json"
    out.write_text(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
