# 🤝 Contributing to Arbitrage Nexus

Thank you for your interest in contributing to Arbitrage Nexus! We welcome contributions from developers of all skill levels. This document provides guidelines and information for contributors.

## 📋 Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [How to Contribute](#how-to-contribute)
- [Development Workflow](#development-workflow)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)
- [Security](#security)
- [Community](#community)

## 📜 Code of Conduct

This project follows our [Code of Conduct](CODE_OF_CONDUCT.md). By participating, you agree to uphold this code. Please report any unacceptable behavior to the maintainers.

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have:
- Python 3.9 or higher
- Docker and Docker Compose
- Git
- A GitHub account

### Quick Setup

1. **Fork the repository** on GitHub
2. **Clone your fork**:
   ```bash
   git clone https://github.com/YOUR_USERNAME/claude-super-easy-bot.git
   cd claude-super-easy-bot
   ```

3. **Set up the development environment**:
   ```bash
   # Create virtual environment
   python -m venv venv
   source venv/bin/activate  # Linux/Mac
   # or: venv\Scripts\activate  # Windows

   # Install dependencies
   pip install -r requirements.txt
   pip install -r requirements-dev.txt  # if available

   # Set up pre-commit hooks
   pip install pre-commit
   pre-commit install
   ```

4. **Set up the database**:
   ```bash
   # Start database services
   docker-compose -f docker-compose.db.yml up -d

   # Run migrations
   alembic upgrade head
   ```

## 🛠️ Development Setup

### Environment Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure your environment variables (use testnet endpoints for development):
   ```bash
   # Set DRY_RUN_MODE=true for safe development
   DRY_RUN_MODE=true

   # Use testnet RPC endpoints
   ETHEREUM_RPC=https://eth-goerli.g.alchemy.com/v2/YOUR_KEY
   POLYGON_RPC=https://polygon-mumbai.g.alchemy.com/v2/YOUR_KEY
   ```

### Running the Application

```bash
# Start the backend engine
python arbitrage_backend.py

# In another terminal, start the API server
python api_server.py

# Access the dashboard at http://localhost:8000
```

## 💡 How to Contribute

### Types of Contributions

We welcome various types of contributions:

- 🐛 **Bug fixes** - Fix existing issues
- ✨ **New features** - Add new functionality
- 📚 **Documentation** - Improve docs or add examples
- 🧪 **Tests** - Add or improve test coverage
- 🔒 **Security** - Security improvements
- 🎨 **UI/UX** - Frontend improvements
- 🏗️ **Infrastructure** - DevOps and deployment improvements

### Finding Issues to Work On

1. Check the [GitHub Issues](https://github.com/Cyptopimpinainteazy/claude-super-easy-bot/issues) page
2. Look for issues labeled `good first issue` or `help wanted`
3. Comment on the issue to indicate you're working on it
4. Wait for maintainer approval before starting work

## 🔄 Development Workflow

### 1. Create a Feature Branch

```bash
# Create and switch to a new branch
git checkout -b feature/your-feature-name

# Or for bug fixes
git checkout -b fix/issue-number-description
```

### 2. Make Your Changes

- Write clear, focused commits
- Follow the coding standards
- Add tests for new functionality
- Update documentation as needed

### 3. Test Your Changes

```bash
# Run the test suite
pytest tests/ -v

# Run with coverage
pytest --cov=./ --cov-report=html

# Check code formatting
black --check .
flake8 .

# Type checking
mypy .
```

### 4. Commit Your Changes

```bash
# Stage your changes
git add .

# Commit with a clear message
git commit -m "feat: add new arbitrage strategy

- Add support for triangular arbitrage
- Improve profit calculation accuracy
- Add comprehensive tests

Closes #123"
```

### 5. Push and Create Pull Request

```bash
# Push your branch
git push origin feature/your-feature-name

# Create a pull request on GitHub
```

## 📝 Coding Standards

### Python Code Style

We follow [PEP 8](https://pep8.org/) with some modifications:

- **Line length**: 127 characters (configured in setup.cfg)
- **Imports**: Grouped and sorted
- **Docstrings**: Google style
- **Type hints**: Required for new code

### Code Formatting

We use automated formatting tools:

```bash
# Format code
black .

# Sort imports
isort .

# Check style
flake8 .

# Type checking
mypy .
```

### Commit Message Convention

We follow [Conventional Commits](https://conventionalcommits.org/):

```
type(scope): description

[optional body]

[optional footer]
```

Types:
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation
- `style`: Code style changes
- `refactor`: Code refactoring
- `test`: Testing
- `chore`: Maintenance

Examples:
```
feat: add multi-chain arbitrage scanning
fix: resolve gas estimation overflow
docs: update API documentation
```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run specific test file
pytest tests/test_arbitrage.py

# Run with verbose output
pytest -v

# Run with coverage
pytest --cov=./ --cov-report=html
```

### Writing Tests

- Use `pytest` framework
- Place tests in `tests/` directory
- Name test files `test_*.py`
- Use descriptive test names
- Test both success and failure cases

Example:
```python
def test_arbitrage_calculation():
    """Test arbitrage profit calculation."""
    # Arrange
    opportunity = ArbitrageOpportunity(...)

    # Act
    profit = calculate_profit(opportunity)

    # Assert
    assert profit > 0
    assert profit == expected_profit
```

### Test Coverage

Aim for high test coverage:
- **Minimum**: 80% overall coverage
- **Critical paths**: 90%+ coverage
- **New features**: 100% coverage

## 📚 Documentation

### Code Documentation

- Add docstrings to all public functions/classes
- Use type hints for parameters and return values
- Keep comments up-to-date with code changes

### API Documentation

- Update API docs for any endpoint changes
- Add examples for new endpoints
- Document breaking changes clearly

### User Documentation

- Update README.md for new features
- Add examples and tutorials
- Keep setup instructions current

## 🔒 Security

### Security Considerations

- Never commit private keys or secrets
- Use environment variables for sensitive data
- Follow the principle of least privilege
- Report security issues privately

### Security Testing

```bash
# Run security scans
bandit -r .

# Check dependencies
safety check

# Run Trivy vulnerability scan
trivy fs .
```

## 🌐 Community

### Communication

- **GitHub Issues**: Bug reports and feature requests
- **GitHub Discussions**: General questions and discussions
- **Pull Request Comments**: Code review discussions

### Getting Help

- Check existing issues and documentation first
- Use GitHub Discussions for questions
- Join our community channels (when available)

### Recognition

Contributors are recognized in:
- GitHub's contributor insights
- Release notes
- Special mentions in documentation

## 🙏 Recognition

We appreciate all contributions, big and small! Contributors may be featured in:

- **Release Notes**: Major contributors mentioned
- **Contributors File**: All contributors listed
- **Hall of Fame**: Outstanding contributions highlighted

## 📞 Contact

- **Issues**: [GitHub Issues](https://github.com/Cyptopimpinainteazy/claude-super-easy-bot/issues)
- **Discussions**: [GitHub Discussions](https://github.com/Cyptopimpinainteazy/claude-super-easy-bot/discussions)
- **Security**: security@arbitragenexus.com

---

Thank you for contributing to Arbitrage Nexus! 🚀
