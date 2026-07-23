#!/usr/bin/env python3
"""Construct a q=4 collision using a sparse companion linear layer.

For a 16-stage shift register, coordinate-wise S-boxes preserve the support of
a nonzero difference.  We enumerate two-tap feedback positions and input
coordinates for which the 28-step support misses output coordinates 0..3, and
then search deterministic feedback coefficients accepted by the current
official matrix verifier's irreducible-characteristic-polynomial shortcut.

The resulting matrix, if found, contains zeros and is not an MDS matrix in the
all-minors sense.  This is deliberately an exact verifier audit, not a claim
about the default Cauchy-MDS challenge instance.
"""
from __future__ import annotations
import json, math, random, sys, time
from pathlib import Path

P=2130706433; T=16; RF=8; RP=20; ALPHA=3
OFFICIAL_SHA='60075da7c0521d9493749a035b1f30d4eda37138'
ROOT=Path(__file__).resolve().parents[2]
OFFICIAL=ROOT/'official_poseidon_tools'
sys.path.insert(0,str(OFFICIAL))
from poseidon.mds_matrix import _check_minpoly, verify_mds_matrix
from poseidon.poseidon import Poseidon
from bounties.partial_collision_verifier import _hash, verify_collision_solution


def matrix(a,b,k):
    M=[[0]*T for _ in range(T)]
    for j in range(T-1):
        M[j+1][j]=1
    M[0][15]=a%P
    M[k][15]=b%P
    return M


def support_step(S,k):
    out=set()
    for j in S:
        if j<15: out.add(j+1)
        else: out.update((0,k))
    return out


def support_sequence(start,k):
    S={start}; out=[sorted(S)]
    for _ in range(RF+RP):
        S=support_step(S,k); out.append(sorted(S))
    return out


def main():
    safe=[]
    for k in range(1,T):
        for start in range(4,T):
            seq=support_sequence(start,k)
            if not (set(range(4)) & set(seq[-1])):
                safe.append((0 if math.gcd(T,k)==1 else 1,len(seq[-1]),k,start,seq))
    safe.sort()
    print('safe_patterns',[(k,start,seq[-1],math.gcd(T,k)) for _,_,k,start,seq in safe])
    assert safe

    rng=random.Random(0xC09DE4_1604)
    started=time.time(); found=None; tested=0
    for _,_,k,start,supports in safe:
        # gcd(16,k)=1 patterns are tried first because M^r does not preserve
        # residue classes modulo a nontrivial divisor.
        for local_attempt in range(1,1001):
            tested+=1
            a=rng.randrange(1,P); b=rng.randrange(1,P)
            M=matrix(a,b,k)
            if not _check_minpoly(M,T,P):
                if tested%100==0: print('tested',tested,'pattern',k,start,'seconds',time.time()-started)
                continue
            assert verify_mds_matrix(M,P)
            X=[0]*15
            Y=[0]*15
            Y[start-1]=1  # padded state coordinate `start`
            pos=Poseidon(prime=P,alpha=ALPHA,t=T,r_f=RF,r_p=RP,mds=M)
            hx=_hash(X,pos,P,T,T); hy=_hash(Y,pos,P,T,T)
            found={
                'official_sha':OFFICIAL_SHA,'tested':tested,'local_attempt':local_attempt,
                'feedback_position_k':k,'input_state_coordinate':start,
                'feedback_a':a,'feedback_b':b,'matrix':M,
                'support_sequence':supports,'final_support_upper_bound':supports[-1],
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
        if found is not None: break
    if found is None:
        found={'found':False,'tested':tested,'seconds':time.time()-started,
               'safe_patterns':[(k,start,seq[-1],math.gcd(T,k)) for _,_,k,start,seq in safe]}
        print(json.dumps(found,indent=2,sort_keys=True))
    (ROOT/'research/poseidon_q4/companion_verifier_result.json').write_text(json.dumps(found,indent=2,sort_keys=True))

if __name__=='__main__': main()
