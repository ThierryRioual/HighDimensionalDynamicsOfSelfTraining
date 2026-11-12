# Historical audits and revision records

These documents retain the scope and findings of the versions they audited.
They are not certifications of the current working tree.

- `AUDIT-Fable.md`: original full Fable audit, preserved without content changes.
- `DRAFT_MATHEMATICAL_AUDIT_2026-11-04.md`: dated mathematical correspondence audit.
- `mean_field_convention_refactor.md`: convention conversion and numerical evidence.
- `manuscript_revision_f59_f83.md`: applied manuscript revisions and their validation.
- `repository_reorganization_2026-11-11.md`: directory migration and verification.

Paths and line numbers inside dated reports refer to their historical layouts.
The current mapping is in [repository organization](../repository_organization.md).
The current numerical verification command is:

```sh
MPLBACKEND=Agg python scripts/check_mean_field_conventions.py
```

Run it from the repository root. It writes a new report under `outputs/verification/`
and leaves the captured regression fixtures unchanged.
