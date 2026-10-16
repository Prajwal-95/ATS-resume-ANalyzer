# Contributing to ATS Resume Score Checker

Thank you for your interest in contributing! This document provides guidelines for contributing to the project.

## Development Setup

1. Fork the repository
2. Clone your fork
3. Create a virtual environment and install dependencies
4. Set up your `.env` file from `.env.example`
5. Run database migrations

## Pull Request Process

1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass (`pytest` for backend, `npm run test` for frontend)
4. Ensure frontend build passes (`npm run build`)
5. Update documentation if needed
6. Submit a pull request

## Code Style

### Backend (Python)

- Follow PEP 8
- Use type hints where appropriate
- Write docstrings for public functions
- Keep functions focused and small

### Frontend (React/JSX)

- Use functional components with hooks
- Keep components focused and reusable
- Use Tailwind CSS for styling
- Follow existing naming conventions

## Testing

- Write tests for new features
- Ensure existing tests pass before submitting PR
- Backend: `pytest`
- Frontend: `npm run test`

## Commit Messages

Use clear, descriptive commit messages:

```
feat: add user profile endpoint
fix: resolve file upload race condition
docs: update API documentation
test: add rate limiting tests
```

## Reporting Issues

Please include:

- Steps to reproduce
- Expected behavior
- Actual behavior
- Environment details (OS, Python/Node versions)
- Relevant logs or error messages
