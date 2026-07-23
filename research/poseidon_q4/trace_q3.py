#!/usr/bin/env python3
from __future__ import annotations
import json, sys
from pathlib import Path

P=2130706433; T=16; RF=8; RP=20; ALPHA=3; SEED=0xc09de4
ROOT=Path(__file__).resolve().parents[2]
OFFICIAL=ROOT/'official_poseidon_tools'
sys.path.insert(0,str(OFFICIAL))
from poseidon.poseidon import Poseidon

X=[146101246,585745660,1080651781]+[0]*12
Y=[310195439,1632272689,97247552]+[0]*12


def mm(M,v): return [sum(a*b for a,b in zip(row,v))%P for row in M]
def sub(a,b): return [(x-y)%P for x,y in zip(a,b)]
def wt(v): return sum(x!=0 for x in v)
def signed(x): return x if x<=P//2 else x-P

def one_round(pos,state,r):
    off=r*T
    pre=[(state[i]+pos.round_constants[off+i])%P for i in range(T)]
    full=(r<RF//2 or r>=RF//2+RP)
    sb=pre[:]
    if full:
        sb=[pow(x,ALPHA,P) for x in pre]
    else:
        sb[0]=pow(sb[0],ALPHA,P)
    out=mm(pos.mds,sb)
    return pre,sb,out,full

def main():
    pos=Poseidon(prime=P,alpha=ALPHA,t=T,r_f=RF,r_p=RP)
    sx=[SEED]+X; sy=[SEED]+Y
    rounds=[]
    for r in range(RF+RP):
        px,bx,ox,full=one_round(pos,sx,r)
        py,by,oy,_=one_round(pos,sy,r)
        dx=sub(sy,sx); db=sub(by,bx); dy=sub(oy,ox)
        rounds.append({
            'round':r,'kind':'full' if full else 'partial',
            'state_diff_wt':wt(dx),'sbox_output_diff_wt':wt(db),'next_diff_wt':wt(dy),
            'state_diff_zero_coords':[i for i,z in enumerate(dx) if z==0],
            'sbox_diff_zero_coords':[i for i,z in enumerate(db) if z==0],
            'active_input_diff0_signed':signed(dx[0]),
            'active_output_diff0_signed':signed(db[0]),
            'x_active_pre':px[0],'y_active_pre':py[0],
            'state_diff_signed':[signed(z) for z in dx],
        })
        sx,sy=ox,oy
    perm_dx=sub(sy,sx)
    in_dx=sub([SEED]+Y,[SEED]+X)
    hx=[(sx[i]+([SEED]+X)[i])%P for i in range(T)]
    hy=[(sy[i]+([SEED]+Y)[i])%P for i in range(T)]
    out={
        'input_diff_signed':[signed(z) for z in in_dx],
        'permutation_output_diff_signed':[signed(z) for z in perm_dx],
        'hash_diff_signed':[signed((hy[i]-hx[i])%P) for i in range(T)],
        'hash_X':hx,'hash_Y':hy,
        'partial_rounds_inactive':[r['round'] for r in rounds if r['kind']=='partial' and r['active_input_diff0_signed']==0],
        'rounds':rounds,
    }
    (ROOT/'research/poseidon_q4/q3_trace.json').write_text(json.dumps(out,indent=2))
    print(json.dumps({k:v for k,v in out.items() if k!='rounds'},indent=2))
    for r in rounds:
        print(r['round'],r['kind'],r['state_diff_wt'],r['sbox_output_diff_wt'],r['next_diff_wt'],r['state_diff_zero_coords'])
if __name__=='__main__': main()
