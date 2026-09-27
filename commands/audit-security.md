---
description: "Runs a defensive security audit on the specified project or code section, covering authentication, authorization, input validation, secrets, sensitive data, dependencies, and OWASP and LGPD risks. Use when the user asks for a security audit, a security review, a vulnerability check, exposed secrets, access control or LGPD compliance; do not use for offensive testing."
---

Run a defensive security audit on the specified project or code section.

Use:
- security-reviewer
- secure-coding-checklist

Analyze:
1. Authentication.
2. Authorization.
3. Access control.
4. Input validation.
5. Sensitive data.
6. Logs.
7. Secrets.
8. Configuration.
9. Dependencies.
10. Uploads.
11. Database.
12. Information exposure.
13. OWASP risks and basic LGPD.

Deliver:
- Findings by severity.
- Evidence.
- Impact.
- Recommended fix.
- Priority.

Do not run offensive tests.
Do not run destructive commands.
Do not change code without an explicit request.

User arguments:
$ARGUMENTS
