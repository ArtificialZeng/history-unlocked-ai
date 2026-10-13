# Conservative catalogue metadata parsing

A failed parser must not become a claim that an archive has no open ciphers.
This portable, standard-library tool projects a recognized DECRYPT catalogue
table into exact IDs, observed detail links and a small set of metadata fields.
It preserves query-bearing links, distinguishes ciphertext-body language metadata
from cleartext language, and treats unsupported or conflicting rows as unknown.

The parser is copied byte-for-byte from the independently audited v3 code.
Its 14 original regression assertions are retained with a portable, synthetic
fixture. Six additional adversarial regression tests preserve the independent
audit's challenge cases. [Derivative provenance](PROVENANCE.json).

```sh
python3 -B research/catalogue_metadata/check_parser_controls.py
python3 -B -m unittest discover -s tests
```

Import `project(html, base_url)` from `parse_list_metadata.py` for a locally
retained HTML string. It makes no network requests and does not download images,
authenticate, infer keys or decode historical messages. `actual_result_count`
is an integer only for a recognized, fully parsed table or a properly bound
empty-result notice; otherwise it is `None`.

The result covers one page. It does not certify that a server enforced a filter,
cover pagination, establish current unsolved status, prove novelty or qualify
a case for cryptanalysis. Malformed or changed website markup may require a
separately reviewed update. These checks are software evidence, not solved cases.

Original project code and synthetic controls: copyright Zijian Zeng, 2026,
MIT under the repository licence.
