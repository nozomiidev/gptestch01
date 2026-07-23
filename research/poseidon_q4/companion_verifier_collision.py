#!/usr/bin/env python3
"""Construct a q=4 collision using a sparse companion linear layer.

The linear layer is a 16-stage shift register with feedback only to state
coordinates 0 and 4.  A difference introduced in state coordinate 8 has, after
28 rounds, support contained in {4,8,12}; coordinate-wise S-boxes cannot create
new support.  Therefore the first four compression outputs collide.

We search deterministic feedback coefficients for which the *current official
verifier* accepts the matrix via its irreducible-characteristic-polynomial
shortcut.  The matrix contains zeros and is therefore not an MDS matrix in the
usual all-minors sense; this script is an exact verifier audit.
"""
from __future__ import annotations
import json, random, sys, time
from pathlib import Path

P=2130706433; T=16; RF=8; RP=20; ALPHA=3
OFFICIAL_SHA='60075da7c0521d9493749a035b1f30d4eda37138'
ROOT=Path(__file__).resolve().parents[2]
OFFICIAL=ROOT/'official_poseidon_tools'
sys.path.insert(0,str(OFFICIAL))
from poseidon.mds_matrix import _check_minpoly, verify_mds_matrix
from poseidon.poseidon import Poseidon
from bounties.partial_collision_verifier import _hash, verify_collision_solution


def matrix(a,b):
    M=[[0]*T for _ in range(T)]
    for j in range(T-1):
        M[j+1][j]=1
    M[0][15]=a%P
    M[4][15]=b%P
    return M


def support_step(S):
    out=set()
    for j in S:
        if j<15: out.add(j+1)
        else: out.update((0,4))
    return out


def main():
    S={8}; supports=[sorted(S)]
    for _ in range(RF+RP):
        S=support_step(S); supports.append(sorted(S))
    print('support_after_28',supports[-1])
    assert not (set(range(4)) & set(supports[-1]))

    rng=random.Random(0xC09DE4_1604)
    started=time.time(); found=None
    for attempt in range(1,501):
        a=rng.randrange(1,P); b=rng.randrange(1,P)
        M=matrix(a,b)
        if not _check_minpoly(M,T,P):
            if attempt%10==0: print('tested',attempt,'seconds',time.time()-started)
            continue
        assert verify_mds_matrix(M,P)
        X=[0]*15
        Y=[0]*15
        Y[7]=1  # padded state coordinate 8
        pos=Poseidon(prime=P,alpha=ALPHA,t=T,r_f=RF,r_p=RP,mds=M)
        hx=_hash(X,pos,P,T,T); hy=_hash(Y,pos,P,T,T)
        found={
            'official_sha':OFFICIAL_SHA,'attempt':attempt,'feedback_a':a,'feedback_b':b,
            'matrix':M,'support_sequence':supports,
            'X':X,'Y':Y,'hash_X':hx,'hash_Y':hy,
            'hash_difference':[(hy[i]-hx[i])%P for i in range(T)],
            'verify_mds_matrix':verify_mds_matrix(M,P),
            'check_minpoly':_check_minpoly(M,T,P),
            'verify_q4':verify_collision_solution(X,Y,t=4,mds=M),
            'verify_q5':verify_collision_solution(X,Y,t=5,mds=M),
            'verify_q7':verify_collision_solution(X,Y,t=7,mds=M),
            'verify_q16':verify_collision_solution(X,Y,t=16,mds=M),
            'seconds':time.time()-started,
            'warning':'Verifier-accepted but not a mathematical MDS matrix because it has zero 1x1 minors.'
        }
        print(json.dumps(found,indent=2,sort_keys=True))
        break
    if found is None:
        found={'found':False,'attempts':500,'seconds':time.time()-started,'support_sequence':supports}
        print(json.dumps(found,indent=2,sort_keys=True))
    (ROOT/'research/poseidon_q4/companion_verifier_result.json').write_text(json.dumps(found,indent=2,sort_keys=True))

if __name__=='__main__': main()
