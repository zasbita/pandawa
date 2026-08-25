---
name: "security-audit"
description: "Infrastructure-first security audit: secrets scanning, dependency supply chain, OWASP Top 10 web checks, STRIDE threat model per trust boundary. Findings ranked by exploitability x impact."
phase: review
source: gstack
aliases: ["gstack:cso", "security review", "threat model"]
---

# Security Audit Gate

Structured security audit of the repo and its attack surface. Evidence-based: every
finding cites file:line and an exploitation path, or it is speculation (mark as such).

## Pass 1 — Secrets archaeology

- Scan history and working tree for API keys, tokens, passwords, private keys (`git log -p` on suspicious paths, entropy scan on tracked files).
- Check `.env*` files are gitignored; look for committed config with credentials; check CI logs/scripts for echoed secrets.
- Any secret ever committed = rotate immediately; removal from HEAD is not enough.

## Pass 2 — Dependency supply chain

- Inventory lockfiles; flag packages with no provenance/SIAs, typosquat-prone names, deprecated/unmaintained deps handling network/auth input.
- Verify install scripts in dependencies are expected (postinstall surprises).
- Pin versions; flag floating tags in CI (`action@main`).

## Pass 3 — OWASP Top 10 (web/API surface)

For each applicable category cite evidence or mark N/A with reason:

1. Broken access control (IDOR, missing authorization on mutation endpoints)
2. Cryptographic failures (plaintext secrets at rest, weak hashing)
3. Injection (SQL/command/template/XSS — cross-ref code-review gate Pass 1)
4. Insecure design (missing rate limits on auth flows, no replay protection)
5. Security misconfiguration (debug on in prod configs, permissive CORS, default creds)
6. Vulnerable components (cross-ref Pass 2)
7. Auth failures (session fixation, missing expiry, weak reset flows)
8. Software/data integrity failures (unsigned artifacts, unverified webhooks)
9. Logging/monitoring failures (auth events unlogged, logs contain secrets)
10. SSRF (user-controlled URL fetches without allowlist)

## Pass 4 — STRIDE per trust boundary

Enumerate trust boundaries (client↔server, server↔DB, agent↔tool, user-input→LLM).
Per boundary, one line each for: Spoofing, Tampering, Repudiation, Info disclosure,
Denial of service, Elevation of privilege. Agent pipelines get extra attention:
prompt-injection surface where external text reaches LLM prompts, and tool
permissions that are allow-all instead of scoped.

## Output

```
Security Audit: N findings (X critical, Y high, Z medium/info)

[CRITICAL] file:line — issue. Exploit path. Fix.
...
N/A with reason: categories checked and not applicable.
```

Rank by exploitability × impact. Criticals get a remediation order. Never paste
discovered secrets into reports — reference their location instead.
