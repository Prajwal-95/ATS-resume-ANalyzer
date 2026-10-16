# Changelog

All notable changes to this project will be documented in this file.

## [1.0.0] - 2024-01-01

### Added

- Initial release
- Resume upload (PDF/DOCX) with text extraction
- ATS-style scoring engine with 6 categories (100 points total)
- Keyword matching with synonym detection
- Technical skills analysis (matched/missing/additional)
- Semantic job relevance using Sentence Transformers
- User authentication (register/login/JWT)
- Analysis history management
- Demo mode with sample data
- PDF report export
- Docker Compose configuration
- Rate limiting on sensitive endpoints
- Security headers middleware
- Health and readiness endpoints
- Alembic database migrations
- Comprehensive test coverage (backend + frontend)

### Security

- bcrypt password hashing
- JWT authentication with configurable expiration
- File type validation via magic bytes
- CORS restricted to configured origins
- User isolation enforced on all data access
- Rate limiting on auth and analysis endpoints

### Documentation

- Complete README with setup instructions
- API documentation
- Contributing guidelines
- Environment configuration examples
