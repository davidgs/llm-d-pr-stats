# Security Policy

## Scope

`llm-d-pr-stats` is a local command-line tool. It has no server component,
listens on no ports, and stores no credentials of its own — it shells out to
the [GitHub CLI](https://cli.github.com/) (`gh`) and relies entirely on
*your* existing `gh auth login` session for authentication. All API calls it
makes are **read-only** (`GET` requests against the GitHub Search API).

That said, this project still handles a GitHub token indirectly (via `gh`)
and processes data pulled from GitHub, so real security issues are still
possible — for example, a bug that logs a token, an unsafe way of building
shell commands, or a dependency vulnerability.

## Supported Versions

This is a single-branch tool with no formal release/version scheme yet.
Security fixes are made against the `main` branch; there are no older
versions receiving patches.

| Version | Supported |
| ------- | --------- |
| `main`  | ✅ |

## Reporting a Vulnerability

If you believe you've found a security issue (e.g. credential leakage,
command/argument injection via crafted `terms/*.json` content or CLI
arguments, path traversal in output file handling, etc.), please report it
**privately** rather than opening a public issue:

- Preferred: open a [private security advisory](https://github.com/davidgs/llm-d-pr-stats/security/advisories/new)
  on this repository (GitHub → Security → Advisories → "Report a
  vulnerability"). *(Update this link if the repo ends up hosted under a
  different owner/org.)*
- Alternative: email the maintainer directly (see the commit history / repo
  owner profile for contact info) with a description of the issue, steps to
  reproduce, and its potential impact.

Please include:

- A clear description of the vulnerability and its potential impact.
- Steps to reproduce (a minimal `terms/*.json` file or CLI invocation, if
  relevant).
- Any suggested remediation, if you have one.

### What to expect

- **Acknowledgment:** within a few days of your report.
- **Triage:** the maintainer will assess severity and confirm reproduction.
- **Fix & disclosure:** a fix will be prioritized based on severity. Where
  reasonable, credit will be given to the reporter in the fix's changelog/
  release notes, unless you prefer to remain anonymous.

Please avoid filing public GitHub issues for suspected vulnerabilities until
a fix has been released, to give users time to update.

## Good Practices for Users

- Use a token/`gh` session scoped to the minimum needed (public read access
  is sufficient for public orgs; you don't need `repo` write scopes to run
  this tool).
- Review any `terms/*.json` files you didn't author yourself before running
  the tool against them — they are treated as data (search terms), not
  code, but always inspect third-party config before running tools against
  your credentials.
- Keep `gh` itself up to date (`gh --version` / `gh upgrade` where
  available) since this tool depends on it for all authentication and API
  access.
