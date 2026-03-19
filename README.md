# aws-route53-manager

`aws-route53-manager` is a small command-line utility to simplify creating, updating, and deleting Route 53 DNS records.

It currently supports single-record changes for `A`, `AAAA`, and `CNAME` records and uses your normal AWS
credentials from the boto3 credential chain.

The implementation lives under `aws_route53_manager/` and is exposed both as an installed console command and as
`python -m aws_route53_manager`.

## What It Does

- Validates and normalises the record name before making an AWS call.
- Lists hosted zones in the current AWS account and chooses the longest matching zone name.
- Submits a single `CREATE`, `DELETE`, or `UPSERT` change request to Route 53.
- Exits with a non-zero status if validation, malformed AWS responses, or AWS operations fail.

## Requirements

- Python 3.10 or newer
- An AWS identity with Route 53 permissions
- `boto3`
- `loguru`

All commands below assume `python3` resolves to Python 3.10 or newer.

Install the package with:

```bash
python3 -m pip install .
```

Build source and wheel distributions with Hatch:

```bash
hatch build
```

Create a local development environment with Hatch and run the test suite:

```bash
hatch run test
```

If you prefer `pip`, install a local development environment with:

```bash
python3 -m pip install -e '.[dev]'
```

## License

This project is licensed under the GNU General Public License, version 3 or any later version (`GPL-3.0-or-later`).
See [LICENSE](LICENSE).

## Versioning

Build versions come from Git tags through `hatch-vcs`.

- Tag releases with a normal version tag such as `v1.2.3`.
- Building from that exact tag resolves to `1.2.3`.
- Building from later commits resolves to a development version such as `1.2.4.dev3+g<hash>`.
- Building from a dirty working tree adds an unclean local suffix, for example `+g<hash>.dYYYYMMDD`.

This repository currently has no Git tags, so add an initial version tag before expecting stable release numbering from Hatch.

## AWS Permissions

The script needs permission to:

- `route53:ListHostedZonesByName`
- `route53:ChangeResourceRecordSets`

It uses the standard boto3 credential chain, so `AWS_PROFILE`, environment variables, IAM roles, and shared config files all work.

## Usage

After installation, the package exposes the `aws-route53-manager` console script. You can also run it directly from a
checkout with `python -m aws_route53_manager`.

```text
aws-route53-manager [-h] [--action {CREATE,DELETE,UPSERT}] [--ttl TTL]
                   [--record-type {A,AAAA,CNAME}]
                   [--log-level {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}]
                   [--log-timestamps]
                   record value
```

Equivalent module invocation:

```bash
python -m aws_route53_manager app.example.com 203.0.113.10
```

### Options

```text
positional arguments:
  record                Fully-qualified record name, for example app.example.com.
  value                 Record value. Use an IPv4 address for A records, an IPv6 address for AAAA
                        records, or a DNS name for CNAME records.

options:
  -h, --help            show this help message and exit
  --action {CREATE,DELETE,UPSERT}
                        Change action to submit, default: CREATE.
  --ttl TTL             DNS record TTL in seconds, default: 300.
  --record-type {A,AAAA,CNAME}, --type {A,AAAA,CNAME}
                        DNS record type, default: A.
  --log-level {TRACE,DEBUG,INFO,SUCCESS,WARNING,ERROR,CRITICAL}
                        Console log verbosity, default: INFO.
  --log-timestamps      Include timestamps in console log output.
```

**Default Values:**

- **Action:** `CREATE`
- **TTL:** `300`
- **Record Type:** `A`
- **Log Level:** `INFO`
- **Timestamps:** disabled

## Examples

Create an `A` record:

```bash
aws-route53-manager app.example.com 203.0.113.10
```

Create an `AAAA` record:

```bash
aws-route53-manager ipv6.example.com 2001:db8::10 --record-type AAAA
```

Upsert a `CNAME` record:

```bash
aws-route53-manager api.example.com lb-123456.eu-west-1.elb.amazonaws.com --record-type CNAME --action UPSERT
```

Create an ACM validation record:

```bash
aws-route53-manager _abcde.example.com _token.acm-validations.aws --record-type CNAME --action UPSERT
```

Create a wildcard record:

```bash
aws-route53-manager '*.example.com' 203.0.113.20
```

Delete a record:

```bash
aws-route53-manager old.example.com 203.0.113.10 --action DELETE
```

## Testing

Run the unit test suite with:

```bash
python3 -m unittest discover -s tests -v
```

## How Hosted Zone Selection Works

The script does not require a hosted zone ID. It lists hosted zones in your account and picks the most specific matching zone name.

For example, if your account contains both `example.com` and `dev.example.com`, then:

- `api.example.com` uses the `example.com` zone
- `api.dev.example.com` uses the `dev.example.com` zone

This makes the script safer for accounts that use delegated subdomains.

## Notes

- The codebase targets Python 3.10+ and uses structural pattern matching and native union annotations.
- Package metadata, runtime dependencies, a console entry point, and tool configuration live in `pyproject.toml`.
- The project uses Hatchling with `hatch-vcs`, so package versions are derived from Git tags instead of a hard-coded value.
- The package metadata declares `GPL-3.0-or-later` and ships the full license text in `LICENSE`.
- Console logs are optimised for interactive CLI use: no timestamps by default, normal output on `stdout`, and warnings/errors on `stderr`.
- Record names are normalised to lowercase and a trailing `.` is removed if present.
- `A` record values must be valid IPv4 addresses.
- `AAAA` record values must be valid IPv6 addresses.
- `CNAME` values are validated as fully-qualified DNS names.
- Invalid AWS SDK response shapes raise explicit internal errors instead of being silently ignored.
- Console output is emitted through `loguru`.
- This tool changes one record at a time.
