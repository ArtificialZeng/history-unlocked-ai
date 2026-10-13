/**
 * Independent read-only relational verifier.
 * Does not import the kernel, reconstruct an answer by sorting ciphertext,
 * write files, use a language score, or alter any input.
 */
function isRecord(value) {
  return value !== null && typeof value === 'object' && !Array.isArray(value);
}
function keysExactly(value, keys) {
  return Object.keys(value).length === keys.length &&
    keys.every(key => Object.prototype.hasOwnProperty.call(value, key));
}
function validInteger(value) {
  return typeof value === 'number' && Number.isSafeInteger(value);
}

/**
 * Check that a separately supplied candidate and optional occurrence certificate
 * agree with every literal alphabet/ciphertext occurrence.
 */
export function verifyPair(alphabet, ciphertext, candidateTokens, suppliedCertificate) {
  const issues = [];
  const add = (code, details = {}) => issues.push({code, ...details});
  const finish = certificate => ({ok: issues.length === 0, issues, certificate});

  if (!Array.isArray(alphabet)) {
    add('alphabet_type');
    return finish([]);
  }
  for (let row = 0; row < alphabet.length; row += 1) {
    const entry = alphabet[row];
    if (!isRecord(entry)) { add('alphabet_entry_type', {row}); continue; }
    if (!keysExactly(entry, ['cell_id','token'])) add('alphabet_entry_fields', {row});
    if (typeof entry.cell_id !== 'string') add('cell_id_type', {row});
    else if (entry.cell_id.length === 0) add('empty_cell_id', {row});
    if (typeof entry.token !== 'string') add('token_type', {row});
    else if (entry.token.length === 0) add('empty_token', {row});
    for (let earlier = 0; earlier < row; earlier += 1) {
      const prior = alphabet[earlier];
      if (!isRecord(prior)) continue;
      if (entry.cell_id === prior.cell_id) add('duplicate_cell_id', {rows: [earlier,row]});
      if (entry.token === prior.token) add('duplicate_token_label', {rows: [earlier,row]});
    }
  }
  if (issues.length > 0) return finish([]);
  if (!isRecord(ciphertext)) { add('ciphertext_type'); return finish([]); }
  if (!keysExactly(ciphertext, ['length','groups'])) {
    add('ciphertext_fields');
    return finish([]);
  }
  if (!validInteger(ciphertext.length) || ciphertext.length < 0) {
    add('invalid_length');
    return finish([]);
  }
  if (!Array.isArray(ciphertext.groups)) {
    add('groups_type');
    return finish([]);
  }

  const observed = [];
  for (let groupNumber = 0; groupNumber < ciphertext.groups.length; groupNumber += 1) {
    const group = ciphertext.groups[groupNumber];
    if (!isRecord(group)) { add('group_type', {groupNumber}); continue; }
    if (!keysExactly(group, ['cell_id','indices'])) add('group_fields', {groupNumber});
    if (typeof group.cell_id !== 'string') add('cell_id_type', {groupNumber});
    else if (group.cell_id.length === 0) add('empty_cell_id', {groupNumber});
    if (!alphabet.some(row => row.cell_id === group.cell_id)) {
      add('unknown_cell', {groupNumber, cell_id: group.cell_id});
    }
    for (let earlier = 0; earlier < groupNumber; earlier += 1) {
      const previous = ciphertext.groups[earlier];
      if (isRecord(previous) && previous.cell_id === group.cell_id) {
        add('duplicate_group_cell', {groups: [earlier,groupNumber]});
      }
    }
    if (!Array.isArray(group.indices)) { add('indices_type', {groupNumber}); continue; }
    for (let offset = 0; offset < group.indices.length; offset += 1) {
      const position = group.indices[offset];
      if (!validInteger(position)) { add('noninteger_index', {groupNumber,offset}); continue; }
      if (position === 0) { add('zero_index', {groupNumber,offset}); continue; }
      if (position < 0) { add('negative_index', {groupNumber,offset}); continue; }
      if (position > ciphertext.length) { add('out_of_range_index', {groupNumber,offset}); continue; }
      observed.push({position,cell_id:group.cell_id});
    }
  }
  if (observed.length !== ciphertext.length) {
    add('occurrence_count_mismatch', {expected: ciphertext.length, actual: observed.length});
  }
  for (let first = 0; first < observed.length; first += 1) {
    for (let second = first + 1; second < observed.length; second += 1) {
      if (observed[first].position === observed[second].position) {
        add('duplicate_position', {position: observed[first].position});
      }
    }
  }
  if (!Array.isArray(candidateTokens)) {
    add('tokens_type');
    return finish([]);
  }
  if (candidateTokens.length !== ciphertext.length) {
    add('candidate_length_mismatch', {expected: ciphertext.length, actual: candidateTokens.length});
  }

  // Construct this certificate from the candidate tokens and alphabet relation,
  // then check each row against the original ciphertext memberships.
  const certificate = [];
  for (let offset = 0; offset < candidateTokens.length; offset += 1) {
    const token = candidateTokens[offset];
    const position = offset + 1;
    if (typeof token !== 'string') { add('token_type', {position}); continue; }
    if (token.length === 0) { add('empty_token', {position}); continue; }
    const matchingAlphabetRows = alphabet.filter(row => row.token === token);
    if (matchingAlphabetRows.length !== 1) {
      add('unknown_token_label', {position,token});
      continue;
    }
    const cell_id = matchingAlphabetRows[0].cell_id;
    certificate.push({position,cell_id,token});
    const memberships = observed.filter(row => row.position === position);
    if (memberships.length !== 1) {
      add('position_membership_count', {position,actual: memberships.length});
    } else if (memberships[0].cell_id !== cell_id) {
      add('cell_token_disagreement', {position,expected_cell_id:cell_id,actual_cell_id:memberships[0].cell_id});
    }
  }

  if (suppliedCertificate !== undefined) {
    if (!Array.isArray(suppliedCertificate)) add('certificate_type');
    else {
      if (suppliedCertificate.length !== ciphertext.length) add('certificate_length_mismatch');
      for (let rowNumber = 0; rowNumber < suppliedCertificate.length; rowNumber += 1) {
        const row = suppliedCertificate[rowNumber];
        if (!isRecord(row) || !keysExactly(row, ['position','cell_id','token'])) {
          add('certificate_fields', {rowNumber});
          continue;
        }
        if (!validInteger(row.position) || row.position <= 0 || row.position > ciphertext.length) {
          add('certificate_position', {rowNumber});
        }
        for (let earlier = 0; earlier < rowNumber; earlier += 1) {
          if (isRecord(suppliedCertificate[earlier]) && suppliedCertificate[earlier].position === row.position) {
            add('duplicate_certificate_position', {rowNumber,position:row.position});
          }
        }
        if (!certificate.some(expected => expected.position === row.position &&
            expected.cell_id === row.cell_id && expected.token === row.token)) {
          add('certificate_disagreement', {rowNumber});
        }
      }
    }
  }
  return finish(certificate);
}
