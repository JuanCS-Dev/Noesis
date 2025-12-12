# Security Policy

## Supported Versions

| Version | Supported          |
| ------- | ------------------ |
| 1.x.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability

We take the security of NOESIS seriously. If you believe you have found a security vulnerability, please report it to us as described below.

### How to Report

**Please do not report security vulnerabilities through public GitHub issues.**

Instead, please report them via email to:

**security@noesis.dev** (or juancarlos@noesis.dev)

Please include the following information:

- **Type of issue** (e.g., buffer overflow, SQL injection, cross-site scripting, etc.)
- **Full paths** of source file(s) related to the issue
- **Location** of the affected source code (tag/branch/commit or direct URL)
- **Step-by-step instructions** to reproduce the issue
- **Proof-of-concept or exploit code** (if possible)
- **Impact** of the issue, including how an attacker might exploit it

### What to Expect

- **Acknowledgment**: We will acknowledge your email within 48 hours
- **Assessment**: We will assess the vulnerability within 7 days
- **Updates**: We will keep you informed of our progress
- **Resolution**: We aim to resolve critical issues within 30 days
- **Credit**: We will credit you in our security advisories (unless you prefer anonymity)

### Preferred Languages

We prefer all communications to be in English or Portuguese.

## Security Measures

### Data Protection

- **No persistent storage of sensitive user data** without encryption
- **API keys and secrets** are never committed to the repository
- **Environment variables** are used for all configuration
- **.env files** are gitignored

### Authentication & Authorization

- **JWT tokens** with short expiration for API authentication
- **Role-based access control** for administrative functions
- **Rate limiting** on all public endpoints

### Consciousness System Safety

NOESIS implements multiple safety layers:

1. **Kill Switch**: Emergency shutdown capability
2. **Threshold Monitor**: Anomaly detection for consciousness metrics
3. **Ethical Tribunal**: All actions pass through VERITAS, SOPHIA, DIKÉ judges
4. **HITL Override**: Human-in-the-loop can override any decision

### Code Security

- **Static analysis** with bandit and safety
- **Dependency scanning** for known vulnerabilities
- **Type checking** with mypy to prevent runtime errors
- **Input validation** on all external inputs

## Security Best Practices for Contributors

### Never Commit

- API keys or tokens
- Passwords or secrets
- Private keys (.pem, .key)
- .env files (use .env.example as template)
- Credentials of any kind

### Always Do

- Use environment variables for configuration
- Validate and sanitize all inputs
- Use parameterized queries (no SQL injection)
- Follow the principle of least privilege
- Log security-relevant events

### Code Review Checklist

- [ ] No hardcoded credentials
- [ ] Input validation present
- [ ] Error messages don't leak sensitive info
- [ ] Authentication/authorization checked
- [ ] Logging doesn't include sensitive data

## Vulnerability Disclosure Policy

We follow a coordinated disclosure process:

1. **Report received** and acknowledged
2. **Vulnerability confirmed** and severity assessed
3. **Fix developed** and tested
4. **Fix deployed** to production
5. **Public disclosure** (typically 90 days after report, or sooner if fix is deployed)

## Security Updates

Security updates are released as:

- **Critical**: Immediate patch release
- **High**: Within 7 days
- **Medium**: Within 30 days
- **Low**: Next regular release

Subscribe to our security advisories by watching this repository.

## Contact

- **Security issues**: security@noesis.dev
- **General inquiries**: juancarlos@noesis.dev
- **GitHub Security Advisories**: [Repository Security Tab](https://github.com/JuanCS-Dev/Daimon/security)

## Acknowledgments

We thank the following individuals for responsibly disclosing security issues:

*No reports yet - be the first!*

---

Thank you for helping keep NOESIS and its users safe!
