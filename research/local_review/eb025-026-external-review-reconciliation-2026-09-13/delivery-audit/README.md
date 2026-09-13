# EB025–026 post-report custody audit

Read [AUDIT.md](AUDIT.md) for results and limits, and AUDIT.json for exact evidence bindings.
All source-content findings remain pending Atlas reconciliation. The original root QA and
both delivered report folders are unchanged. No UI execution was witnessed.

Run `python -B /path/to/popper-eb025-026-delivery-audit/verify_audit.py` on the complete copied
folder. The verifier is portable and read-only; it needs Pydantic 2, jsonschema and PyMuPDF.
The closed inventory includes all retained report bytes, source/candidate copies and selected
packet metadata. Exact original paths and observed mtimes are custody history, not files opened
by the verifier or proof of acquisition/review timing.
