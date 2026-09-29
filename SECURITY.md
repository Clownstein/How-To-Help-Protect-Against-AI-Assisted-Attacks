# Security Policy

## Supported versions

Security fixes are made on the default branch. Generated rule files and the plugin catalog are supported only for the catalog revision in that branch. An older checkout is not updated in place.

| Version | Supported |
| --- | --- |
| Default branch, including plugin 1.0.0 | :white_check_mark: |
| Any older snapshot or generated copy | :x: |

## Reporting a vulnerability

Report security issues through GitHub private vulnerability reporting on this repository: open the Security tab, choose "Report a vulnerability," and submit a private advisory. Do not open a public issue, pull request, or discussion for an unfixed vulnerability.

Please include:

- A short description of the impact and who can trigger it
- The affected path, such as a plugin, generator, or generated rule file
- Steps or a minimal example that reproduces the problem
- The commit you tested, if you know it

You should receive an acknowledgment within 7 days. If the report is accepted, a follow-up within 14 days will say what will change and a target for the fix. A fix is prepared on a private branch when the repository settings allow it, then released on the default branch with an advisory. If the report is declined, the reply will say why, including when the behavior is an accepted limitation of name-based or user-agent controls.

Please give the maintainers a chance to publish a fix before you disclose the details publicly.
