"""Independent even-square turning-grille codec and known-key controls.

Public holes are one-indexed row-major positions. A quarter-turn clockwise maps
zero-indexed (row, column) to (column, side - 1 - row). At each orientation, holes
are visited in row-major order. Encryption writes consecutive payload characters
to this four-orientation visit order, then reads the square row-major. Decryption
reads the ciphertext square in the same visit order. Multiple squares are handled
independently. Text is preserved exactly: no filtering, casing or space removal.

This module was written before reading/importing the root grille implementation.
It contains no target input, historical target key or target interpretation.
"""
from __future__ import annotations
import argparse
import datetime
import hashlib
import json
import random
from pathlib import Path
from typing import Iterable


class GrilleError(ValueError):
    """Invalid grid, grille, convention or block extent."""


def _integer(value: object, label: str) -> int:
    if type(value) is not int:
        raise GrilleError(f'{label} must be an integer (not bool)')
    return value


def _side(side: int) -> int:
    _integer(side, 'side')
    if side <= 0 or side % 2:
        raise GrilleError('side must be positive and even')
    return side


def _clockwise_index0(side: int, index0: int) -> int:
    row, column = divmod(index0, side)
    return column * side + (side - 1 - row)


def rotate_clockwise(side: int, position_1indexed: int) -> int:
    """One clockwise quarter-turn of a one-indexed row-major cell."""
    _side(side)
    _integer(position_1indexed, 'position')
    if not 1 <= position_1indexed <= side * side:
        raise GrilleError('position outside square')
    return _clockwise_index0(side, position_1indexed - 1) + 1


def rotation_orbits(side: int) -> tuple[tuple[int, ...], ...]:
    """Partition all cells into four-element quarter-turn orbits, one-indexed."""
    _side(side)
    unassigned = set(range(side * side))
    orbits: list[tuple[int, ...]] = []
    while unassigned:
        first = min(unassigned)
        orbit = [first]
        for _ in range(3):
            orbit.append(_clockwise_index0(side, orbit[-1]))
        if len(set(orbit)) != 4 or _clockwise_index0(side, orbit[-1]) != first:
            raise GrilleError('even-square rotation orbit is not four cells')
        if not set(orbit) <= unassigned:
            raise GrilleError('rotation orbits overlap')
        unassigned.difference_update(orbit)
        orbits.append(tuple(cell + 1 for cell in orbit))
    return tuple(orbits)


def validate_grille(side: int, holes_1indexed: Iterable[int]) -> tuple[int, ...]:
    """Require one distinct in-bounds hole from every four-cell rotation orbit."""
    _side(side)
    try:
        holes = tuple(holes_1indexed)
    except TypeError as exc:
        raise GrilleError('holes must be an iterable of integer cells') from exc
    for hole in holes:
        _integer(hole, 'hole')
        if not 1 <= hole <= side * side:
            raise GrilleError('hole outside square')
    if len(set(holes)) != len(holes):
        raise GrilleError('duplicate hole')
    if len(holes) != side * side // 4:
        raise GrilleError('wrong number of holes for full four-turn coverage')
    visited: list[int] = []
    current = tuple(hole - 1 for hole in holes)
    for _ in range(4):
        visited.extend(current)
        current = tuple(_clockwise_index0(side, hole) for hole in current)
    if len(set(visited)) != side * side:
        raise GrilleError('rotation coverage overlaps or leaves cells missing')
    if set(visited) != set(range(side * side)):
        raise GrilleError('rotation coverage is not the full square')
    return tuple(sorted(holes))


def permutation(side: int, holes_1indexed: Iterable[int], *, start_turn: int = 0,
                direction: int = 1) -> tuple[int, ...]:
    """Zero-indexed square positions in payload order.

    start_turn 0,1,2,3 means initial clockwise angle 0,90,180,270 degrees.
    direction +1 means clockwise quarter-turns; -1 means counterclockwise.
    Every orientation is read row-major regardless of turning direction.
    """
    holes = validate_grille(side, holes_1indexed)
    _integer(start_turn, 'start_turn')
    _integer(direction, 'direction')
    if start_turn not in (0, 1, 2, 3):
        raise GrilleError('start_turn must be 0,1,2,3')
    if direction not in (-1, 1):
        raise GrilleError('direction must be -1 or +1')
    orientations: list[tuple[int, ...]] = []
    current = tuple(h - 1 for h in holes)
    for _ in range(4):
        orientations.append(tuple(sorted(current)))
        current = tuple(_clockwise_index0(side, h) for h in current)
    visit = tuple(cell for turn in range(4)
                  for cell in orientations[(start_turn + direction * turn) % 4])
    if sorted(visit) != list(range(side * side)):
        raise GrilleError('visit order is not a complete permutation')
    return visit


def _payload(text: str, block_size: int) -> None:
    if not isinstance(text, str):
        raise GrilleError('text must be a string')
    if len(text) % block_size:
        raise GrilleError('text extent must contain whole square blocks')


def encrypt(plaintext: str, side: int, holes_1indexed: Iterable[int], *,
            start_turn: int = 0, direction: int = 1) -> str:
    visit = permutation(side, holes_1indexed, start_turn=start_turn, direction=direction)
    block_size = side * side
    _payload(plaintext, block_size)
    output: list[str] = []
    for offset in range(0, len(plaintext), block_size):
        square = [''] * block_size
        for payload_index, square_index in enumerate(visit):
            square[square_index] = plaintext[offset + payload_index]
        output.extend(square)
    return ''.join(output)


def decrypt(ciphertext: str, side: int, holes_1indexed: Iterable[int], *,
            start_turn: int = 0, direction: int = 1) -> str:
    visit = permutation(side, holes_1indexed, start_turn=start_turn, direction=direction)
    block_size = side * side
    _payload(ciphertext, block_size)
    return ''.join(ciphertext[offset + square_index]
                   for offset in range(0, len(ciphertext), block_size)
                   for square_index in visit)


def _digest(value: object) -> str:
    raw = value if isinstance(value, str) else json.dumps(value, separators=(',', ':'))
    return hashlib.sha256(raw.encode('utf-8')).hexdigest()


def run_controls(seed: int = 85120261006) -> tuple[dict, list[dict]]:
    """100 distinct synthetic grilles, 800 orientation/direction controls."""
    rng = random.Random(seed)
    known_holes = (1, 8, 10, 12)
    known_plain = 'THETURNINGGRILLE'
    known_cipher = 'TILUNRGHGELTENIR'
    # Explicit primary-vector visitation derived from four drawn orientations.
    known_visit1 = (1,8,10,12,4,6,14,15,5,7,9,16,2,3,11,13)
    assert tuple(p + 1 for p in permutation(4, known_holes)) == known_visit1
    assert encrypt(known_plain, 4, known_holes) == known_cipher
    assert decrypt(known_cipher, 4, known_holes) == known_plain
    assert encrypt('', 4, known_holes) == decrypt('', 4, known_holes) == ''
    rejected: list[dict] = []
    def rejects(label: str, callback) -> None:
        try:
            callback()
        except GrilleError as exc:
            rejected.append({'label':label,'exception':type(exc).__name__,'reason':str(exc)})
        else:
            raise AssertionError('invalid control accepted: '+label)
    for bad in [0,-2,1,3,True,4.0,'4']:
        rejects('invalid_side_'+repr(bad),lambda bad=bad:rotation_orbits(bad))
    for bad in [-1,4,90,True,0.0,'0']:
        rejects('invalid_start_'+repr(bad),lambda bad=bad:permutation(4,known_holes,start_turn=bad))
    for bad in [0,2,True,1.0,'1']:
        rejects('invalid_direction_'+repr(bad),lambda bad=bad:permutation(4,known_holes,direction=bad))
    for bad in [None,[True,8,10,12],[1.0,8,10,12],['1',8,10,12]]:
        rejects('invalid_hole_type_'+repr(bad),lambda bad=bad:validate_grille(4,bad))
    rejects('non_string_encrypt',lambda:encrypt(b'0123456789abcdef',4,known_holes))
    rejects('non_string_decrypt',lambda:decrypt(b'0123456789abcdef',4,known_holes))
    fixtures: list[dict] = []; cases=0
    per_side: dict[str,dict] = {}
    for side,number in [(2,4),(4,24),(6,24),(8,24),(10,24)]:
        orbits = rotation_orbits(side)
        assert len(orbits) == side * side // 4
        assert len({cell for orbit in orbits for cell in orbit}) == side * side
        for cell in range(1,side*side+1):
            rotated = cell
            for _ in range(4):rotated=rotate_clockwise(side,rotated)
            assert rotated==cell
        # For 2x2 the complete valid key set is only four holes; enumerate it.
        keys = { (h,) for h in orbits[0] } if side==2 else set()
        while len(keys)<number:
            keys.add(tuple(sorted(rng.choice(orbit) for orbit in orbits)))
        side_cases=0
        for key in sorted(keys):
            assert validate_grille(side,key)==key
            plain=''.join(rng.choice('ABCDEFGHIJKLMNOPQRSTUVWXYZ') for _ in range(4*side*side))
            fixture={'side':side,'holes_1indexed':list(key),'blocks':4,'plaintext':plain,'controls':[]}
            for start in range(4):
                for direction in [-1,1]:
                    visit=permutation(side,key,start_turn=start,direction=direction)
                    assert len(visit)==side*side and len(set(visit))==side*side
                    cipher=encrypt(plain,side,key,start_turn=start,direction=direction)
                    decoded=decrypt(cipher,side,key,start_turn=start,direction=direction)
                    assert decoded==plain
                    assert encrypt(decoded,side,key,start_turn=start,direction=direction)==cipher
                    # Four-block result must equal independent per-block calls.
                    blockwise=''.join(encrypt(plain[o:o+side*side],side,key,start_turn=start,direction=direction) for o in range(0,len(plain),side*side))
                    assert blockwise==cipher
                    # Distinct symbols make all cell moves observable, beyond
                    # uppercase data that can accidentally repeat at a cell.
                    unique=''.join(chr(0x4000+j) for j in range(side*side))
                    coded=encrypt(unique,side,key,start_turn=start,direction=direction)
                    for j,cell0 in enumerate(visit):assert coded[cell0]==unique[j]
                    assert decrypt(coded,side,key,start_turn=start,direction=direction)==unique
                    fixture['controls'].append({'start_turn':start,'start_angle_degrees':90*start,'direction':direction,'permutation_1indexed':[x+1 for x in visit],'ciphertext_sha256':_digest(cipher),'roundtrip_pass':True,'block_independence_pass':True,'unique_symbol_placement_pass':True})
                    cases+=1;side_cases+=1
            fixtures.append(fixture)
            rejects(f'{side}_{key}_duplicate',lambda side=side,key=key:validate_grille(side,(*key,key[0])))
            rejects(f'{side}_{key}_below_bounds',lambda side=side,key=key:validate_grille(side,(0,*key[1:])))
            rejects(f'{side}_{key}_above_bounds',lambda side=side,key=key:validate_grille(side,(side*side+1,*key[1:])))
            rejects(f'{side}_{key}_missing_hole',lambda side=side,key=key:validate_grille(side,key[:-1]))
            rejects(f'{side}_{key}_partial_encrypt',lambda side=side,key=key,plain=plain:encrypt(plain[:-1],side,key))
            cipher0=encrypt(plain,side,key)
            rejects(f'{side}_{key}_partial_decrypt',lambda side=side,key=key,cipher0=cipher0:decrypt(cipher0[:-1],side,key))
            if side>2:
                collided=(key[0],rotate_clockwise(side,key[0]),*key[2:])
                assert len(collided)==len(key) and len(set(collided))==len(key)
                rejects(f'{side}_{key}_same_orbit_overlap',lambda side=side,collided=collided:validate_grille(side,collided))
        per_side[str(side)]={'distinct_grilles':len(keys),'orientation_direction_controls':side_cases,'orbits':len(orbits),'blocks_per_control':4,'all_pass':True}
    assert len(fixtures)==100 and cases==800
    assert len({(x['side'],tuple(x['holes_1indexed'])) for x in fixtures})==100
    result={'status':'PASS','seed':seed,'primary_known_vector':{'official_source':'https://www.cryptogram.org/downloads/aca.info/ciphers/Grille.pdf','holes_1indexed':list(known_holes),'plaintext':known_plain,'ciphertext':known_cipher,'visit_order_1indexed':list(known_visit1),'start_angle_degrees':0,'quarter_turn_direction':'clockwise','each_orientation_reading':'row-major','exact_forward_pass':True,'exact_decode_pass':True},'distinct_valid_grilles':100,'orientation_direction_controls':cases,'blocks_per_control':4,'per_side':per_side,'rejection_controls':len(rejected),'rejected_cases':rejected,'empty_payload_policy':'allowed as zero whole blocks; non-string and partial blocks rejected','new_known_control_method':'rotation-orbit construction plus primary vector, distinct cell-symbol placement and independent block calls','target_inputs':0,'root_code_read_or_imported_before_this_run':False,'limits':'Software and primary worked-example control only; no target source/key geometry or historical plaintext assessed.'}
    return result,fixtures


def main() -> None:
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--run-controls',action='store_true')
    parser.add_argument('--out-dir',type=Path)
    args=parser.parse_args()
    if not args.run_controls:parser.error('--run-controls is required')
    result,fixtures=run_controls()
    result['completed_at_utc']=datetime.datetime.now(datetime.timezone.utc).isoformat()
    result['independent_code_sha256']=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    if args.out_dir:
        args.out_dir.mkdir(parents=True,exist_ok=True)
        (args.out_dir/'INDEPENDENT_SOFTWARE_CONTROLS_v1.json').write_text(json.dumps(result,indent=2)+'\n')
        (args.out_dir/'INDEPENDENT_SYNTHETIC_FIXTURES_v1.json').write_text(json.dumps(fixtures,indent=2)+'\n')
    print(json.dumps({k:result[k] for k in ['status','distinct_valid_grilles','orientation_direction_controls','rejection_controls','target_inputs','independent_code_sha256']}))


if __name__=='__main__':main()
