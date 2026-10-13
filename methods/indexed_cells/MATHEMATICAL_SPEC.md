# Fixed indexed-cell relation: specification and proof

This is a generic synthetic/software resource. No historical inscription, printed key, source image, historical reading, or authentic-language control was used. Its applicability to any eventual historical object remains a separate source question.

Let C be a finite set of opaque nonempty cell identifiers and let alpha: C -> T be an injective map to nonempty literal token strings. Tokens are atoms even when they contain several letters, combining marks, or non-Latin characters. No Unicode normalization, case conversion, accent removal, or splitting occurs. The registered alphabet may have any finite size; the covering control has 30 cells.

A ciphertext declares a nonnegative integer N explicitly and, for each represented cell c, a finite list I_c of integers. A missing cell group means an empty I_c. Groups and their internal lists carry no ordering information. The input representation requires at most one group per cell. Its admissibility condition is:

- every group cell belongs to C;
- every occurrence is an integer in {1,...,N};
- each i in {1,...,N} occurs in exactly one I_c, and occurs there exactly once.

For N=0 the message is the explicit empty token list, with no occurrences. This is the empty-domain convention, not a null-token or position-exception rule. Empty token strings, null tokens, repeated group identifiers, and extra schema fields are refused. Numeric inputs are restricted to exact JavaScript safe integers; values outside that representable range are refused rather than rounded.

For an admissible ciphertext, define p(i) as the unique cell whose I_c contains i. The decoder is
D_alpha(I) = [alpha(p(1)), ..., alpha(p(N))].
This list is unique: the partition condition forces p(i), and the fixed alphabet forces alpha(p(i)), separately at every position. Display order, alphabetical order, and the order of the ciphertext lists cannot change it. The procedure needs no vocabulary or semantic choice.

For an explicit list t=[t_1,...,t_N] in alpha(C)^N, define
E_alpha(t)_c = { i : t_i = alpha(c) }.
Injectivity gives each accepted token exactly one inverse cell. Therefore D_alpha(E_alpha(t))=t position by position. Conversely, E_alpha(D_alpha(I))_c=I_c as indexed sets for every c. This latter equality is relational equality: different group orders, list orders, and omission of empty groups do not imply byte-for-byte JSON equality. The encoder chooses the supplied alphabet order and increasing index order as a documented output convention.

An independently checked occurrence certificate has one row (i,c,t_i) for each i. A verifier checks (a) alphabet injection, (b) the entire partition, (c) candidate length and literal token-to-cell membership, and (d) each certificate row against the original group membership. The verifier constructs its rows from the candidate-token/alphabet relation and tests their memberships. It does not import the decoder or obtain tokens by sorting ciphertext.

The three fixed known-answer fixtures and their independently written occurrence rows were hashed before software implementation. Their gold answers were not encoder products. The finite enumeration checks every vector over one frozen three-token alphabet for N=0,...,5, all six cell-group orders, and the two registered internal index-list orders. It is a bounded software consistency check, including some redundant short-list variants, and is not empirical evidence for a historical reading or a universal test of every possible group ordering on arbitrary alphabets.

A historical use would additionally require independently established source applicability: that the observed source truly supplies the fixed injective literal cell map, the positions, the integer roles, the length, and the completeness/uniqueness condition. This software cannot establish those facts. It must not be forced onto an incompatible source.
