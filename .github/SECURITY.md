# Security policy

This application is intended for local use. Public deployment is not supported
by the current security and operating model.

Report a suspected vulnerability to the repository owner through an existing
private channel. Do not publish credentials, private research, database dumps,
or exploit details in a public issue. Include the affected revision, a minimal
reproduction using non-private inputs, and the observed impact.

The [threat model](../docs/security.md) records boundaries and
mitigations. The [limitation ledger](../docs/limitations.md#security-boundary)
records unresolved risks. Dependency and container scans are dated checks,
not guarantees of security.

Keep local environment files and backups out of Git. If a credential is exposed,
revoke or rotate it through its provider and review affected access. Removing
a value from the latest file does not remove earlier Git history.
