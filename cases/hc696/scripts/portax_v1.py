"""PORTAX, independently authored from the primary ACA one-page description.

Source: https://www.cryptogram.org/downloads/aca.info/ciphers/Portax.pdf
The slide is the A2 column (0..12) aligned below fixed A. Key letters
AB, CD, ..., YZ select identical slides. Inputs are exact uppercase ASCII
letters; no spaces, punctuation, unknown symbols, or padding are removed.

Horizontal rows are paired consecutively. A full pair of rows has length
2 * period. The final incomplete pair of rows has equal shorter rows;
its columns use the initial key positions. All transformations are
self-reciprocal. Odd-length plaintext padding must be explicitly requested.
"""

from collections.abc import Sequence
from typing import Union

ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ"
Key = Union[str, Sequence[int]]


def _number(value: int, upper: int, name: str) -> int:
    if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value < upper:
        raise ValueError(f"{name} must be an integer in 0..{upper - 1}")
    return value


def _text(text: str) -> str:
    if not isinstance(text, str) or any(char not in ALPHABET for char in text):
        raise ValueError("text must consist of exact uppercase ASCII letters A-Z")
    return text


def effective_key(key: Key) -> tuple[int, ...]:
    """Return documented slides: A/B -> 0, C/D -> 1, ..., Y/Z -> 12."""
    if isinstance(key, str):
        _text(key)
        slides = tuple((ord(char) - 65) // 2 for char in key)
    else:
        slides = tuple(_number(value, 13, "slide") for value in key)
    if not slides:
        raise ValueError("key must have at least one letter or slide")
    return slides


def transform_pair(top: int, bottom: int, slide: int) -> tuple[int, int]:
    """Transform one vertical pair; letters are indices A=0 through Z=25.

    Top is in A1 (fixed A-M or sliding N-Z); bottom is in A2, whose
    paired rows are ACE...Y and BDF...Z. Take the rectangle's other two
    corners, or the other two letters on a common vertical line.
    This same operation encrypts and decrypts.
    """
    _number(top, 26, "top")
    _number(bottom, 26, "bottom")
    _number(slide, 13, "slide")
    top_column = top if top < 13 else (top - 13 - slide) % 13
    bottom_column = (bottom // 2 - slide) % 13
    if top_column == bottom_column:
        new_top = 13 + (top_column + slide) % 13 if top < 13 else top_column
        return new_top, bottom ^ 1
    new_top = bottom_column if top < 13 else 13 + (bottom_column + slide) % 13
    new_bottom = 2 * ((top_column + slide) % 13) + bottom % 2
    return new_top, new_bottom


def pair_letters(top: str, bottom: str, key_letter: str) -> tuple[str, str]:
    """Convenience wrapper for one A-Z letter per argument."""
    for letter in (top, bottom, key_letter):
        if len(_text(letter)) != 1:
            raise ValueError("one letter per argument is required")
    first, second = transform_pair(ord(top) - 65, ord(bottom) - 65, effective_key(key_letter)[0])
    return ALPHABET[first], ALPHABET[second]


def packing_pairs(length: int, period: int) -> tuple[tuple[int, int, int], ...]:
    """Return (top_index, bottom_index, key_index) for published row packing.

    Indices are zero-based. Full blocks contain two rows of `period`
    letters; a final short block is split into equally short rows.
    An odd length is rejected because it cannot form vertical pairs.
    """
    if not isinstance(length, int) or isinstance(length, bool) or length < 0 or length % 2:
        raise ValueError("length must be a nonnegative even integer")
    if not isinstance(period, int) or isinstance(period, bool) or period < 1:
        raise ValueError("period must be a positive integer")
    result = []
    for start in range(0, length, 2 * period):
        row_length = min(2 * period, length - start) // 2
        result.extend((start + column, start + row_length + column, column)
                      for column in range(row_length))
    return tuple(result)


def transform_values(values: Sequence[int], key: Key) -> tuple[int, ...]:
    """Transform all paired horizontal rows of exact numeric input."""
    slides = effective_key(key)
    output = [_number(value, 26, "letter") for value in values]
    for top, bottom, column in packing_pairs(len(output), len(slides)):
        output[top], output[bottom] = transform_pair(output[top], output[bottom], slides[column])
    return tuple(output)


def transform_block(text: str, key: Key) -> str:
    """Transform one full or incomplete two-row block (at most 2*period)."""
    _text(text)
    slides = effective_key(key)
    if len(text) > 2 * len(slides):
        raise ValueError("block is longer than two keyword-width rows")
    return "".join(ALPHABET[value] for value in transform_values([ord(c) - 65 for c in text], slides))


def transform(text: str, key: Key) -> str:
    """Transform a complete even-length text; exact input length retained."""
    _text(text)
    return "".join(ALPHABET[value] for value in transform_values([ord(c) - 65 for c in text], key))


def encrypt(text: str, key: Key, *, pad_odd: bool = False, pad_char: str = "X") -> str:
    """Encrypt exact letters, optionally append one declared odd-length pad."""
    _text(text)
    if len(_text(pad_char)) != 1:
        raise ValueError("pad_char must be one uppercase A-Z letter")
    if len(text) % 2 and pad_odd:
        text += pad_char
    return transform(text, key)


def decrypt(text: str, key: Key) -> str:
    """Decrypt exact letters; any historical padding remains in the result."""
    return transform(text, key)


# The table is useful for finite search, but generated entirely by this rule.
# PAIR_TABLE[slide][top][bottom] is a tuple (new_top, new_bottom).
PAIR_TABLE = tuple(tuple(tuple(transform_pair(top, bottom, slide)
                              for bottom in range(26))
                        for top in range(26))
                   for slide in range(13))
