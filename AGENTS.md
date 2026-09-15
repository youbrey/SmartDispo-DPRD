# SmartDispo DPRD Development Rules

- Preserve the approved business workflows. Workflow definitions are server-driven and versioned.
- Android and SIPS communicate only through the API; never connect them directly to PostgreSQL.
- Authorization is enforced server-side from permissions and active task assignments.
- ADMIN does not imply SIGN, VERIFY, APPROVE, COORDINATE, or DISPOSITION.
- Substantive document changes create a new version; approvals bind to a version and SHA-256 hash.
- Workflow mutations are transactional and concurrency-checked.
- Audit records are append-only.
- Every schema change requires an Alembic migration.
- Keep backward compatibility and avoid duplicate models, services, and endpoints.
- Never hard-code current officeholder names. Resolve active role assignments.
- Never commit secrets or signing keys.
