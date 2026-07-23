#!/usr/bin/env python3
"""Exact structural diagnostics for the Poseidon1/KoalaBear q=4 challenge.

Runs against a checkout of khovratovich/poseidon-tools at the pinned official
commit.  This first-stage script verifies the published q=3 witness and then
measures the linear dimension of sparse differential-control trails through
the 20 partial rounds.
"""
from __future__ import annotations

import itertools
import json
import os
import sys
import time
from pathlib import Path

P = 2130706433
T = 16
RF = 8
RP = 20
ALPHA = 3
SEED = 0xC09DE4
OFFICIAL_SHA = "60075da7c0521d9493749a035b1f30d4eda37138"

ROOT = Path(__file__).resolve().parents[2]
OFFICIAL = ROOT / "official_poseidon_tools"
sys.path.insert(0, str(OFFICIAL))

from poseidon.poseidon import Poseidon  # noqa: E402
from poseidon.mds_matrix import generate_mds_matrix, generate_circulant_mds_matrix, verify_mds_matrix  # noqa: E402
from bounties.partial_collision_verifier import verify_collision_solution, _hash  # noqa: E402


def inv(a: int) -> int:
    return pow(a % P, P - 2, P)


def mat_mul(A, B):
    n, k, m = len(A), len(B), len(B[0])
    assert len(A[0]) == k
    out = [[0] * m for _ in range(n)]
    for i in range(n):
        oi = out[i]
        for h in range(k):
            a = A[i][h]
            if a:
                Bh = B[h]
                for j in range(m):
                    oi[j] = (oi[j] + a * Bh[j]) % P
    return out


def mat_vec(A, x):
    return [sum(a * b for a, b in zip(row, x)) % P for row in A]


def identity(n):
    return [[1 if i == j else 0 for j in range(n)] for i in range(n)]


def rref(A):
    A = [[x % P for x in row] for row in A]
    if not A:
        return A, []
    n, m = len(A), len(A[0])
    pivots = []
    r = 0
    for c in range(m):
        pivot = next((i for i in range(r, n) if A[i][c]), None)
        if pivot is None:
            continue
        A[r], A[pivot] = A[pivot], A[r]
        z = inv(A[r][c])
        A[r] = [(z * x) % P for x in A[r]]
        for i in range(n):
            if i != r and A[i][c]:
                z = A[i][c]
                A[i] = [(a - z * b) % P for a, b in zip(A[i], A[r])]
        pivots.append(c)
        r += 1
        if r == n:
            break
    return A, pivots


def rank(A):
    if not A:
        return 0
    return len(rref(A)[1])


def nullspace(A, ncols=None):
    if not A:
        assert ncols is not None
        return identity(ncols)
    R, piv = rref(A)
    m = len(R[0])
    free = [j for j in range(m) if j not in set(piv)]
    basis = []
    for f in free:
        x = [0] * m
        x[f] = 1
        for i, p in enumerate(piv):
            x[p] = (-R[i][f]) % P
        basis.append(x)
    return basis


def mat_inverse(A):
    n = len(A)
    aug = [list(row) + identity(n)[i] for i, row in enumerate(A)]
    R, piv = rref(aug)
    assert piv[:n] == list(range(n)), "matrix singular"
    return [row[n:] for row in R]


def apply_M_to_symbolic(M, X):
    # X is T x nvar, return M X.
    return mat_mul(M, X)


def add_outer(X, v, col):
    Y = [row[:] for row in X]
    for i in range(T):
        Y[i][col] = (Y[i][col] + v[i]) % P
    return Y


def partial_linear_model(M, active):
    """Return constraints and end-state map for a chosen set of active rounds.

    Difference recurrence in a partial round is
        delta_{r+1} = M delta_r + (M e_0) gamma_r.
    At an inactive round we impose delta_r[0] = 0 and gamma_r=0.  At an
    active round gamma_r is a free control variable.
    """
    active = tuple(active)
    amap = {r: T + j for j, r in enumerate(active)}
    nvar = T + len(active)
    X = [[0] * nvar for _ in range(T)]
    for i in range(T):
        X[i][i] = 1
    v = [M[i][0] for i in range(T)]
    constraints = []
    states = [X]
    for r in range(RP):
        if r not in amap:
            constraints.append(X[0][:])
        X = apply_M_to_symbolic(M, X)
        if r in amap:
            X = add_outer(X, v, amap[r])
        states.append(X)
    return constraints, X, states


def support_stats(M, kmax=5):
    report = {}
    for k in range(kmax + 1):
        t0 = time.time()
        best = []
        hist = {}
        count = 0
        for active in itertools.combinations(range(RP), k):
            C, end, states = partial_linear_model(M, active)
            nvar = T + k
            r0 = rank(C)
            nul = nvar - r0
            # Natural extra conditions useful for a collision trail.
            r_in4 = rank(C + [states[0][i] for i in range(4)])
            r_out4 = rank(C + [end[i] for i in range(4)])
            r_both4 = rank(C + [states[0][i] for i in range(4)] + [end[i] for i in range(4)])
            vals = (nul, nvar - r_in4, nvar - r_out4, nvar - r_both4)
            hist[vals] = hist.get(vals, 0) + 1
            score = vals[3]
            item = (score, vals, active)
            if len(best) < 12:
                best.append(item)
                best.sort(reverse=True)
            elif item > best[-1]:
                best[-1] = item
                best.sort(reverse=True)
            count += 1
        report[str(k)] = {
            "count": count,
            "histogram": {str(key): val for key, val in sorted(hist.items())},
            "best": [
                {"active": list(a), "nullities_raw_in4_out4_both4": list(vals)}
                for _, vals, a in best
            ],
            "seconds": time.time() - t0,
        }
        print(f"k={k}: {count} supports in {report[str(k)]['seconds']:.3f}s")
        print("  hist", report[str(k)]["histogram"])
        print("  best", report[str(k)]["best"][:5])
    return report


def krylov_ranks(M):
    row = [1] + [0] * (T - 1)
    rows = []
    out = []
    for r in range(1, 2 * T + 1):
        rows.append(row)
        out.append(rank(rows))
        row = [sum(row[j] * M[j][i] for j in range(T)) % P for i in range(T)]
    return out


def main():
    print("official_sha", OFFICIAL_SHA)
    print("official_path", OFFICIAL)
    pos = Poseidon(prime=P, alpha=ALPHA, t=T, r_f=RF, r_p=RP)
    M = pos.mds
    assert M == generate_mds_matrix(T, P)
    print("default_mds_verified", verify_mds_matrix(M, P))
    print("default_mds_row0", M[0])
    print("rc0", pos.round_constants[0])
    print("rc_last", pos.round_constants[-1])
    print("krylov_ranks", krylov_ranks(M))
    Minv = mat_inverse(M)
    print("inverse_check_rank", rank(mat_mul(M, Minv)))

    X3 = [146101246, 585745660, 1080651781] + [0] * 12
    Y3 = [310195439, 1632272689, 97247552] + [0] * 12
    hX = _hash(X3, pos, P, 16, 16)
    hY = _hash(Y3, pos, P, 16, 16)
    print("q3_hash_x", hX)
    print("q3_hash_y", hY)
    print("q3_verify", verify_collision_solution(X3, Y3, t=3))
    print("q4_verify_known_pair", verify_collision_solution(X3, Y3, t=4))
    print("q3_prefix_delta", [(hX[i] - hY[i]) % P for i in range(8)])

    # Check the Plonky3 circulant accepted by the same verifier.
    plonky_row = [1, 1, 51, 1, 11, 17, 2, 1, 101, 63, 15, 2, 67, 22, 13, 3]
    Mc = generate_circulant_mds_matrix(T, P, plonky_row)
    print("plonky3_mds_verified", verify_mds_matrix(Mc, P))
    print("plonky3_krylov_ranks", krylov_ranks(Mc))

    report = {
        "parameters": {"p": P, "t": T, "rf": RF, "rp": RP, "alpha": ALPHA, "seed": SEED},
        "default_krylov_ranks": krylov_ranks(M),
        "plonky3_krylov_ranks": krylov_ranks(Mc),
        "q3_hash_x": hX,
        "q3_hash_y": hY,
        "q3_verify": verify_collision_solution(X3, Y3, t=3),
        "q4_verify_known_pair": verify_collision_solution(X3, Y3, t=4),
        "partial_supports_default": support_stats(M, 5),
        "partial_supports_plonky3": support_stats(Mc, 5),
    }
    out = ROOT / "research" / "poseidon_q4" / "diagnostic.json"
    out.write_text(json.dumps(report, indent=2, sort_keys=True))
    print("wrote", out)


if __name__ == "__main__":
    main()
