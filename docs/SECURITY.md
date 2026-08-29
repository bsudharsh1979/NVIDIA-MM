# Security

Threats addressed in this pass:

- Prompt injection from course PDFs: treated as retrieved **data**, not system instructions
- Malicious notebook code: never executed; dangerous cells flagged
- Secret exposure: `.env` gitignored; Settings does not echo keys
- Path traversal: ingest walks `COURSE_MATERIALS_DIR` only
- XSS: course markdown shown in `pre`/text, not `dangerouslySetInnerHTML`
- SSRF: importer does not fetch learner URLs
- API abuse: demo provider is local; budget field exists for keyed providers

Run `pip-audit` in CI when you add a lockfile. No secrets in the repo.
