/**
 * Generic fixed injective indexed-cell kernel. JSON-shaped input only.
 * No normalization, language model, source observation, or raw-string tokenizer.
 */
export class IndexedCellValidationError extends Error {
  constructor(code, details = {}) {
    super(code);
    this.name = 'IndexedCellValidationError';
    this.code = code;
    this.details = details;
  }
}
function refuse(code, details) {
  throw new IndexedCellValidationError(code, details);
}
function record(value, code, path) {
  if (value === null || typeof value !== 'object' || Array.isArray(value)) {
    refuse(code, {path});
  }
}
function exactFields(value, fields, code, path) {
  const keys = Object.keys(value);
  if (keys.length !== fields.length || fields.some(key => !Object.hasOwn(value, key))) {
    refuse(code, {path, expected: fields, actual: keys});
  }
}
function literalCell(value, path) {
  if (typeof value !== 'string') refuse('cell_id_type', {path});
  if (value.length === 0) refuse('empty_cell_id', {path});
}
function literalToken(value, path) {
  if (typeof value !== 'string') refuse('token_type', {path});
  if (value.length === 0) refuse('empty_token', {path});
}
function alphabetMaps(alphabet) {
  if (!Array.isArray(alphabet)) refuse('alphabet_type', {path: 'alphabet'});
  const cellToToken = new Map();
  const tokenToCell = new Map();
  for (let row = 0; row < alphabet.length; row += 1) {
    const entry = alphabet[row];
    const path = 'alphabet[' + row + ']';
    record(entry, 'alphabet_entry_type', path);
    exactFields(entry, ['cell_id', 'token'], 'alphabet_entry_fields', path);
    literalCell(entry.cell_id, path + '.cell_id');
    literalToken(entry.token, path + '.token');
    if (cellToToken.has(entry.cell_id)) refuse('duplicate_cell_id', {path, cell_id: entry.cell_id});
    if (tokenToCell.has(entry.token)) refuse('duplicate_token_label', {path, token: entry.token});
    cellToToken.set(entry.cell_id, entry.token);
    tokenToCell.set(entry.token, entry.cell_id);
  }
  return {cellToToken, tokenToCell};
}
function gaps(positions, length) {
  const sorted = [...positions].sort((left, right) => left - right);
  const missing = [];
  let next = 1;
  for (const position of sorted) {
    if (position > next) missing.push([next, position - 1]);
    next = position + 1;
  }
  if (next <= length) missing.push([next, length]);
  return missing;
}

/** Return a token array; never concatenate or tokenize literal strings. */
export function decode(alphabet, ciphertext) {
  const {cellToToken} = alphabetMaps(alphabet);
  record(ciphertext, 'ciphertext_type', 'ciphertext');
  exactFields(ciphertext, ['length', 'groups'], 'ciphertext_fields', 'ciphertext');
  const length = ciphertext.length;
  if (typeof length !== 'number' || !Number.isSafeInteger(length) || length < 0) {
    refuse('invalid_length', {path: 'ciphertext.length', value: length});
  }
  if (!Array.isArray(ciphertext.groups)) refuse('groups_type', {path: 'ciphertext.groups'});
  const seenCells = new Set();
  const positions = new Map();
  for (let groupIndex = 0; groupIndex < ciphertext.groups.length; groupIndex += 1) {
    const group = ciphertext.groups[groupIndex];
    const path = 'ciphertext.groups[' + groupIndex + ']';
    record(group, 'group_type', path);
    exactFields(group, ['cell_id', 'indices'], 'group_fields', path);
    literalCell(group.cell_id, path + '.cell_id');
    if (!cellToToken.has(group.cell_id)) refuse('unknown_cell', {path, cell_id: group.cell_id});
    if (seenCells.has(group.cell_id)) refuse('duplicate_group_cell', {path, cell_id: group.cell_id});
    seenCells.add(group.cell_id);
    if (!Array.isArray(group.indices)) refuse('indices_type', {path: path + '.indices'});
    for (let offset = 0; offset < group.indices.length; offset += 1) {
      const position = group.indices[offset];
      const indexPath = path + '.indices[' + offset + ']';
      if (typeof position !== 'number' || !Number.isSafeInteger(position)) {
        refuse('noninteger_index', {path: indexPath, value: position});
      }
      if (position === 0) refuse('zero_index', {path: indexPath});
      if (position < 0) refuse('negative_index', {path: indexPath, value: position});
      if (position > length) refuse('out_of_range_index', {path: indexPath, value: position, length});
      if (positions.has(position)) {
        refuse('duplicate_index', {path: indexPath, position, first_cell_id: positions.get(position).cell_id, second_cell_id: group.cell_id});
      }
      positions.set(position, {cell_id: group.cell_id, token: cellToToken.get(group.cell_id)});
    }
  }
  if (positions.size !== length) {
    refuse('missing_indices', {missing_count: length - positions.size, missing_ranges: gaps(positions.keys(), length)});
  }
  return [...positions.entries()].sort((left, right) => left[0] - right[0]).map(entry => entry[1].token);
}

/** Encode an explicit array of atomic literal tokens. Emit cells in given alphabet order. */
export function encode(alphabet, tokens) {
  const {tokenToCell} = alphabetMaps(alphabet);
  if (!Array.isArray(tokens)) refuse('tokens_type', {path: 'tokens'});
  const groups = alphabet.map(entry => ({cell_id: entry.cell_id, indices: []}));
  const cellToGroup = new Map(groups.map(group => [group.cell_id, group]));
  for (let offset = 0; offset < tokens.length; offset += 1) {
    const token = tokens[offset];
    const path = 'tokens[' + offset + ']';
    literalToken(token, path);
    if (!tokenToCell.has(token)) refuse('unknown_token_label', {path, token});
    cellToGroup.get(tokenToCell.get(token)).indices.push(offset + 1);
  }
  return {length: tokens.length, groups};
}
