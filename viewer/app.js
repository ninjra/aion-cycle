/* Local-only read-only artifact viewer. No network, no verification. */
function summarize(value) {
  if (!value || typeof value !== 'object' || Array.isArray(value)) return value;
  const keys = [
    'schema_version', 'proof_passed', 'failed_checks', 'cycle_root',
    'transcript_root', 'proof_root', 'receipt_hash', 'receipt_sha256',
    'toolchain_receipt_hash', 'generation_trace_receipt_hash'
  ];
  const out = {};
  for (const key of keys) {
    if (Object.prototype.hasOwnProperty.call(value, key)) out[key] = value[key];
  }
  out.available_top_level_keys = Object.keys(value).sort();
  return out;
}

document.getElementById('render').addEventListener('click', () => {
  const input = document.getElementById('input').value;
  const output = document.getElementById('output');
  try {
    const parsed = JSON.parse(input);
    output.textContent = JSON.stringify(summarize(parsed), null, 2);
  } catch (err) {
    output.textContent = 'Invalid JSON: ' + err.message;
  }
});
