# Bounded legacy LFS availability check — September 16, 2026

Two ordinary unauthenticated Git LFS batch metadata requests queried the six known legacy object IDs in the public Christoffel1876 fork and GEODE77 upstream. Both endpoints returned HTTP 200 with a per-object 404 for every requested object and no download actions. No payload bytes were downloaded and no canonical file was hydrated or changed.

The sanitized receipts record exact request/response digests, times, sizes and object identities. They contain no credentials or signed download URLs. The original small metadata responses remain in the local session handoff; they are not embedded here. These results establish only that those endpoints did not offer these objects to these requests. They do not establish absence from other backups or authenticated private storage. The six pointer files remain unresolved.
