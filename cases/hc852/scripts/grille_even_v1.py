"""Literal even-square turning-grille codec; no cleaning, scoring or padding."""
def _order(side, mode):
    if mode == "row-major":
        return [(r,c) for r in range(side) for c in range(side)]
    if mode == "column-major":
        return [(r,c) for c in range(side) for r in range(side)]
    raise ValueError("unsupported scan/order")

def rotate(cell, side, turns):
    r,c=cell
    for _ in range(turns % 4):
        r,c=c,side-1-r
    return r,c

def route(side, holes, start=0, direction=1, hole_scan="row-major"):
    if type(side) is not int or side < 2 or side % 2:
        raise ValueError("positive even side required")
    if type(start) is not int or start not in range(4) or direction not in (-1,1):
        raise ValueError("invalid orientation")
    holes=list(holes)
    if len(holes) != side*side//4 or len(set(holes)) != len(holes):
        raise ValueError("wrong/duplicate cut census")
    for cell in holes:
        if len(cell)!=2 or any(type(v) is not int or not 0 <= v < side for v in cell):
            raise ValueError("cut outside grid")
    ranks={cell:i for i,cell in enumerate(_order(side,hole_scan))}
    visits=[]
    for k in range(4):
        cells=[rotate(cell,side,start+direction*k) for cell in holes]
        visits.extend(sorted(cells,key=ranks.__getitem__))
    if len(set(visits)) != side*side:
        raise ValueError("rotation overlap/uncovered cells")
    return tuple(visits)

def encrypt(plaintext, *,side,holes,start=0,direction=1,hole_scan="row-major",cipher_order="row-major"):
    visits=route(side,holes,start,direction,hole_scan)
    order=_order(side,cipher_order)
    n=side*side
    if not isinstance(plaintext,str) or not plaintext or len(plaintext)%n:
        raise ValueError("positive full-block literal required")
    output=[]
    for off in range(0,len(plaintext),n):
        cells=dict(zip(visits,plaintext[off:off+n]))
        output.extend(cells[cell] for cell in order)
    return "".join(output)

def decrypt(ciphertext, *,side,holes,start=0,direction=1,hole_scan="row-major",cipher_order="row-major"):
    visits=route(side,holes,start,direction,hole_scan)
    order=_order(side,cipher_order)
    n=side*side
    if not isinstance(ciphertext,str) or not ciphertext or len(ciphertext)%n:
        raise ValueError("positive full-block literal required")
    output=[]
    for off in range(0,len(ciphertext),n):
        cells=dict(zip(order,ciphertext[off:off+n]))
        output.extend(cells[cell] for cell in visits)
    return "".join(output)
