"""Compact even-square turning-grille codec; no target key/text embedded."""
from dataclasses import dataclass
@dataclass(frozen=True)
class Grille:
    side:int
    holes:tuple
    def __post_init__(self):
        n=self.side
        if n<2 or n%2:raise ValueError('side must be positive even')
        if len(self.holes)!=n*n//4 or len(set(self.holes))!=len(self.holes):raise ValueError('wrong holecount/duplicates')
        if any(not(0<=r<n and 0<=c<n) for r,c in self.holes):raise ValueError('hole outside sourcegrid')
        all_cells=[cell for a in range(4) for cell in self.rotated(a)]
        if len(set(all_cells))!=n*n:raise ValueError('fourrotations must cover allcells once')
    def rotated(self,k):
        n=self.side;cells=list(self.holes)
        for _ in range(k%4):cells=[(c,n-1-r) for r,c in cells]
        return tuple(sorted(cells))
    def permutation(self,start=0,direction=1):
        if direction not in [-1,1]:raise ValueError('rotation direction must be -1 or +1')
        return tuple(r*self.side+c for turn in range(4) for r,c in self.rotated(start+direction*turn))
    def encrypt(self,plain,start=0,direction=1):
        m=self.side**2
        if len(plain)%m:raise ValueError('explicitpaddingrequired')
        route=self.permutation(start,direction);out=[]
        for begin in range(0,len(plain),m):
            block=['']*m
            for i,j in enumerate(route):block[j]=plain[begin+i]
            out.append(''.join(block))
        return ''.join(out)
    def decrypt(self,cipher,start=0,direction=1):
        m=self.side**2
        if len(cipher)%m:raise ValueError('explicitpartialblockhypothesisrequired')
        route=self.permutation(start,direction)
        return ''.join(cipher[begin+j] for begin in range(0,len(cipher),m) for j in route)
