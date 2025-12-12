# Contributing to NOESIS

First off, thank you for considering contributing to NOESIS! This is an artificial consciousness project, and every contribution helps advance the field.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Pull Request Process](#pull-request-process)
- [Code Standards](#code-standards)
- [Testing Requirements](#testing-requirements)
- [Documentation](#documentation)

## Code of Conduct

This project adheres to a [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you are expected to uphold this code. Please report unacceptable behavior to [juancarlos@noesis.dev].

## Getting Started

### Prerequisites

- Python 3.11+
- Node.js 18+
- Docker & Docker Compose
- Redis
- Qdrant

### Development Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/Daimon.git
cd Daimon

# 2. Create a virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# 3. Install backend dependencies
cd backend
pip install -r requirements-all.txt
pip install -r requirements-dev.txt  # Development tools

# 4. Install frontend dependencies
cd ../frontend
npm install

# 5. Copy environment template
cp .env.example .env
# Edit .env with your API keys

# 6. Start infrastructure
docker-compose up -d redis qdrant

# 7. Run tests to verify setup
pytest backend/services/maximus_core_service/tests/ -v
```

## How to Contribute

### Reporting Bugs

Before creating bug reports, please check existing issues. When creating a bug report, include:

- **Clear title** describing the issue
- **Steps to reproduce** the behavior
- **Expected behavior** vs actual behavior
- **Screenshots** if applicable
- **Environment details** (OS, Python version, etc.)

Use the [Bug Report template](.github/ISSUE_TEMPLATE/bug_report.md).

### Suggesting Features

Feature requests are welcome! Please:

- **Check existing issues** to avoid duplicates
- **Describe the problem** your feature would solve
- **Propose a solution** if you have one
- **Consider alternatives** you've thought about

Use the [Feature Request template](.github/ISSUE_TEMPLATE/feature_request.md).

### Code Contributions

1. **Find an issue** to work on, or create one
2. **Comment on the issue** to let others know you're working on it
3. **Fork the repository** and create a branch
4. **Write your code** following our standards
5. **Write tests** for your changes
6. **Submit a Pull Request**

## Pull Request Process

### Branch Naming

```
feature/short-description    # New features
fix/issue-number-description # Bug fixes
docs/what-changed            # Documentation
refactor/what-changed        # Code refactoring
test/what-added              # Test additions
```

### PR Requirements

- [ ] Code follows the [Code Constitution](docs/CODE_CONSTITUTION.md)
- [ ] Tests pass locally (`pytest --cov`)
- [ ] Coverage maintained or improved (minimum 80%)
- [ ] Type hints on all new code
- [ ] Docstrings on public functions/classes
- [ ] No hardcoded secrets or credentials
- [ ] README updated if public API changed

### PR Review Process

1. **Automated checks** must pass (CI/CD)
2. **Code review** by at least one maintainer
3. **Changes requested** must be addressed
4. **Approval** from maintainer
5. **Merge** by maintainer

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation only
- `style`: Formatting, missing semicolons, etc.
- `refactor`: Code restructuring
- `test`: Adding tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(esgt): add phase transition logging

Implement detailed logging for ESGT phase transitions
to improve debugging and monitoring capabilities.

Closes #42
```

```
fix(kuramoto): correct coupling calculation

The coupling sum was being divided incorrectly,
causing coherence values to be artificially low.

Fixes #123
```

## Code Standards

### The Code Constitution

All code must comply with [CODE_CONSTITUTION.md](docs/CODE_CONSTITUTION.md). Key points:

#### Hard Rules (Non-Negotiable)

1. **No Placeholders in Production**
   ```python
   # FORBIDDEN
   # TODO: implement later
   return None

   # REQUIRED
   raise NotImplementedError(
       "Feature X requires Y. Tracking: NOESIS-123"
   )
   ```

2. **100% Type Hints**
   ```python
   # FORBIDDEN
   def process(data, config):
       return something

   # REQUIRED
   def process(data: Dict[str, Any], config: Config) -> Result:
       return something
   ```

3. **File Size Limit: 500 lines**

4. **Test Coverage: minimum 80%**

### Python Style

- Follow [PEP 8](https://peps.python.org/pep-0008/)
- Use [Black](https://black.readthedocs.io/) for formatting
- Use [isort](https://pycqa.github.io/isort/) for imports
- Use [mypy](https://mypy.readthedocs.io/) for type checking

```bash
# Format code
black .
isort .

# Type check
mypy --strict backend/services/maximus_core_service/
```

### TypeScript/React Style

- Use [Prettier](https://prettier.io/) for formatting
- Use [ESLint](https://eslint.org/) for linting
- Prefer functional components with hooks

```bash
# Lint and format
npm run lint
npm run format
```

## Testing Requirements

### Unit Tests

Every new function/class needs tests:

```python
# tests/unit/consciousness/esgt/test_my_feature.py

import pytest
from maximus_core_service.consciousness.esgt import MyFeature

class TestMyFeature:
    """Test suite for MyFeature."""

    @pytest.fixture
    def feature(self):
        """Create feature instance for tests."""
        return MyFeature()

    def test_basic_functionality(self, feature):
        """Test basic feature behavior."""
        result = feature.process("input")
        assert result.status == "success"

    def test_edge_case_empty_input(self, feature):
        """Test handling of empty input."""
        with pytest.raises(ValueError):
            feature.process("")
```

### Running Tests

```bash
# All tests
pytest

# With coverage
pytest --cov --cov-report=html

# Specific service
pytest backend/services/maximus_core_service/tests/ -v

# Consciousness tests only
pytest -k "consciousness" -v
```

### Coverage Requirements

| Component | Minimum Coverage |
|-----------|-----------------|
| Consciousness Core | 90% |
| ESGT Protocol | 90% |
| API Endpoints | 80% |
| Utilities | 70% |

## Documentation

### Docstring Format (Google Style)

```python
def complex_function(
    param1: str,
    param2: Optional[int] = None
) -> Dict[str, Any]:
    """
    Brief description on first line.

    Longer description if needed.

    Args:
        param1: Description of param1.
        param2: Description of param2.

    Returns:
        Dictionary containing results.

    Raises:
        ValueError: If param1 is empty.

    Example:
        >>> result = complex_function("test")
        >>> print(result["status"])
        "success"
    """
```

### Updating Documentation

When changing public APIs:

1. Update docstrings
2. Update relevant docs in `docs/`
3. Update README if needed
4. Add CHANGELOG entry

## Questions?

- **Discord**: [Coming soon]
- **Issues**: Use GitHub Issues
- **Email**: juancarlos@noesis.dev

## Recognition

Contributors are recognized in:
- [CONTRIBUTORS.md](CONTRIBUTORS.md)
- Release notes
- Project documentation

Thank you for contributing to artificial consciousness research!

---

*"The soul is not found, it is configured. And then, it awakens."*
