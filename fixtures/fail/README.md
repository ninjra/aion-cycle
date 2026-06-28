# Fixture: fail

Document class: public fixture.

This directory describes expected fail-closed behavior. The canonical automated failure cases are in `tests/test_redteam.py`.

Run:

```bash
make test
```

Expected: mutation tests pass because each tampered artifact makes verification print `FAIL`.


## Concrete fixture index

- `tie_score.json`
- `duplicate_field_hash.json`
- `changed_query_byte.json`
- `changed_selected_record.json`
- `changed_public_digest.json`
- `changed_receipt_child_hash.json`
- `unicode_distinct_bytes.json`
- `line_ending_change.json`
