# Build Guide

This project uses Hatch for local environments, test execution, and package builds.

The CLI is exposed as the installed `aws-route53-manager` command and as `python -m aws_route53_manager`. The project
does not keep a separate top-level wrapper script in the repository.

## Prerequisites

- Python 3.10 or newer
- `hatch` installed locally
- Git metadata available for the repository

Install Hatch if needed:

```bash
python3 -m pip install hatch
```

## Quick Start

Build both the source distribution and wheel:

```bash
hatch build
```

Run the test suite:

```bash
hatch test
```

Remove build artifacts:

```bash
hatch clean
```

## Build Commands

Build all configured targets:

```bash
hatch build
```

Build only the wheel:

```bash
hatch build -t wheel
```

Build only the source distribution:

```bash
hatch build -t sdist
```

Build artifacts are written to `dist/`.

## Cleaning

Remove generated build artifacts:

```bash
hatch clean
```

If you also want to remove unused Hatch environments:

```bash
hatch env prune
```

## Running Tests

The recommended command is:

```bash
hatch test
```

Hatch's `test` command uses its internal `hatch-test` environment and runs `pytest` by default. This repository's
tests are written with `unittest`, and `pytest` will discover and run them from `tests/`.

Useful variants:

```bash
hatch test --cover
hatch test tests/test_manager.py
hatch test -vv
```

This repository also defines a default environment script:

```bash
hatch run test
```

That script runs:

```bash
python -m unittest discover -s tests -v
```

Use `hatch test` when you want the standard Hatch test workflow. Use `hatch run test` when you want the repo's direct
`unittest` command.

## Versioning

Package versions are derived from Git tags through `hatch-vcs`, which delegates version calculation to
`setuptools-scm`.

Current configuration:

- Exact tag build: release version
- Commit after a tag: development version
- Dirty working tree: local dirty suffix added to the version

Examples:

- Tag `v1.2.3` checked out exactly: `1.2.3`
- Three commits after `v1.2.3`: `1.2.4.dev3+g<hash>`
- Dirty checkout after those commits: `1.2.4.dev3+g<hash>.dYYYYMMDD`
- Dirty checkout exactly on `v1.2.3`: `1.2.3+dYYYYMMDD`

## Tagging Releases

Create a release tag:

```bash
git tag v0.1.0
```

Push the tag:

```bash
git push origin v0.1.0
```

Then build:

```bash
hatch build
```

## Important Repository Note

This package lives inside a larger Git repository:

```text
/home/gdalziel/personal/github/repos/python-utils-infra
```

That means `hatch-vcs` reads tags from the parent repository, not just this package directory. Release tags therefore
apply to the repository as a whole.

## No-Tag Behaviour

This project does not define a fallback version. If there is no suitable Git tag, version detection is expected to
fail during build time.

Before the first real build intended for distribution, create an initial tag such as:

```bash
git tag v0.1.0
```

## Common Workflow

Run tests:

```bash
hatch test
```

Clean previous artifacts:

```bash
hatch clean
```

Build distributions:

```bash
hatch build
```
