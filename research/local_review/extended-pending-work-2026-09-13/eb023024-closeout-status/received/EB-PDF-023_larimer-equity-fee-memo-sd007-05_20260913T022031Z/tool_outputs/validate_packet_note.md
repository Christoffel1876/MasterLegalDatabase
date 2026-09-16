# validate_packet / hash verification — EB-PDF-023
command: PYTHONDONTWRITEBYTECODE=1 python3 -B 04-verification/validate_packet.py
result: FAILED — ModuleNotFoundError: No module named 'jsonschema'
fallback: manual SHA-256 of MANIFEST.json vs MANIFEST_SHA256.txt + per-file hashes for larimer-equity paths and workdir original/candidate
manifest_opaque_match: True
larimer_payload_files_verified_ok: 26
larimer_fails: []
