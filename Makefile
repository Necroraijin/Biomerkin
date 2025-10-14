# Biomerkin Multi-Agent System - Deployment Automation
# Makefile for common deployment and management tasks

.PHONY: help install test build deploy validate backup rollback clean

# Default target
help:
	@echo "Biomerkin Deployment Automation"
	@echo "================================"
	@echo ""
	@echo "Available targets:"
	@echo "  install     - Install dependencies and setup environment"
	@echo "  test        - Run all tests"
	@echo "  security    - Run security scans"
	@echo "  build       - Build and package Lambda functions"
	@echo "  deploy-dev  - Deploy to development environment"
	@echo "  deploy-staging - Deploy to staging environment"
	@echo "  deploy-prod - Deploy to production environment"
	@echo "  validate    - Validate deployment"
	@echo "  backup      - Create backup"
	@echo "  rollback    - Rollback deployment"
	@echo "  clean       - Clean build artifacts"
	@echo ""
	@echo "Environment Management:"
	@echo "  env-create  - Create new environment"
	@echo "  env-list    - List all environments"
	@echo "  env-validate - Validate environment"
	@echo ""
	@echo "Usage examples:"
	@echo "  make deploy-dev"
	@echo "  make validate ENV=staging"
	@echo "  make backup ENV=prod"

# Variables
ENV ?= dev
REGION ?= us-east-1
PYTHON ?= python3
PIP ?= pip3

# Installation and setup
install:
	@echo "Installing dependencies..."
	$(PIP) install --upgrade pip
	$(PIP) install -r requirements.txt
	$(PIP) install -r infrastructure/requirements.txt
	npm install -g aws-cdk
	@echo "Dependencies installed successfully"

install-dev:
	@echo "Installing development dependencies..."
	$(PIP) install pytest pytest-cov pytest-mock bandit safety
	@echo "Development dependencies installed"

# Testing
test:
	@echo "Running unit tests..."
	$(PYTHON) -m pytest tests/ -v --cov=biomerkin --cov-report=term-missing

test-integration:
	@echo "Running integration tests..."
	$(PYTHON) -m pytest tests/test_*_integration.py -v

test-all: test test-integration

# Security scanning
security:
	@echo "Running security scans..."
	bandit -r biomerkin/ -f json -o bandit-report.json || true
	safety check --json --output safety-report.json || true
	@echo "Security scan completed. Check bandit-report.json and safety-report.json"

# Build and package
build:
	@echo "Building Lambda packages..."
	$(PYTHON) scripts/package_lambdas.py
	@echo "Build completed"

cdk-synth:
	@echo "Synthesizing CDK templates..."
	cd infrastructure && cdk synth --all
	@echo "CDK synthesis completed"

# Deployment targets
deploy-dev:
	@echo "Deploying to development environment..."
	$(PYTHON) scripts/deploy.py dev --region $(REGION)

deploy-staging:
	@echo "Deploying to staging environment..."
	$(PYTHON) scripts/deploy.py staging --region $(REGION)

deploy-prod:
	@echo "Deploying to production environment..."
	$(PYTHON) scripts/deploy.py prod --region $(REGION)

deploy:
	@echo "Deploying to $(ENV) environment..."
	$(PYTHON) scripts/deploy.py $(ENV) --region $(REGION)

# Validation
validate:
	@echo "Validating $(ENV) environment..."
	$(PYTHON) scripts/validate_deployment.py $(ENV) --region $(REGION)

validate-dev:
	@echo "Validating development environment..."
	$(PYTHON) scripts/validate_deployment.py dev --region $(REGION)

validate-staging:
	@echo "Validating staging environment..."
	$(PYTHON) scripts/validate_deployment.py staging --region $(REGION)

validate-prod:
	@echo "Validating production environment..."
	$(PYTHON) scripts/validate_deployment.py prod --region $(REGION)

# Environment management
env-create:
	@echo "Creating $(ENV) environment..."
	$(PYTHON) scripts/environment_manager.py create $(ENV) --region $(REGION)

env-list:
	@echo "Listing all environments..."
	$(PYTHON) scripts/environment_manager.py list --region $(REGION)

env-validate:
	@echo "Validating $(ENV) environment configuration..."
	$(PYTHON) scripts/environment_manager.py validate $(ENV) --region $(REGION)

env-delete:
	@echo "Deleting $(ENV) environment..."
	$(PYTHON) scripts/environment_manager.py delete $(ENV) --region $(REGION)

# Backup and recovery
backup:
	@echo "Creating backup for $(ENV) environment..."
	$(PYTHON) scripts/disaster_recovery.py backup $(ENV) --region $(REGION)

backup-list:
	@echo "Listing backups for $(ENV) environment..."
	$(PYTHON) scripts/disaster_recovery.py list $(ENV) --region $(REGION)

rollback:
	@echo "Rolling back $(ENV) environment..."
	@echo "Available backups:"
	@$(PYTHON) scripts/disaster_recovery.py list $(ENV) --region $(REGION)
	@echo "Use: make rollback-to TIMESTAMP=<timestamp>"

rollback-to:
	@echo "Rolling back $(ENV) to $(TIMESTAMP)..."
	$(PYTHON) scripts/disaster_recovery.py rollback $(ENV) $(TIMESTAMP) --region $(REGION)

# CDK specific commands
cdk-bootstrap:
	@echo "Bootstrapping CDK..."
	cd infrastructure && cdk bootstrap --region $(REGION)

cdk-deploy:
	@echo "Deploying with CDK..."
	cd infrastructure && cdk deploy --all --require-approval never

cdk-destroy:
	@echo "Destroying CDK stacks..."
	cd infrastructure && cdk destroy --all --force

# Pipeline management
pipeline-create:
	@echo "Creating CI/CD pipeline..."
	cd infrastructure && cdk deploy BiomerkinPipeline --require-approval never

pipeline-status:
	@echo "Checking pipeline status..."
	aws codepipeline get-pipeline-state --name biomerkin-cicd-pipeline --region $(REGION)

# Monitoring and logs
logs:
	@echo "Tailing logs for $(ENV) environment..."
	aws logs tail /aws/lambda/biomerkin-orchestrator-$(ENV) --follow --region $(REGION)

logs-function:
	@echo "Tailing logs for function $(FUNCTION) in $(ENV)..."
	aws logs tail /aws/lambda/biomerkin-$(FUNCTION)-$(ENV) --follow --region $(REGION)

metrics:
	@echo "Getting metrics for $(ENV) environment..."
	aws cloudwatch get-metric-statistics \
		--namespace AWS/Lambda \
		--metric-name Invocations \
		--dimensions Name=FunctionName,Value=biomerkin-orchestrator-$(ENV) \
		--start-time $(shell date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
		--end-time $(shell date -u +%Y-%m-%dT%H:%M:%S) \
		--period 300 \
		--statistics Sum \
		--region $(REGION)

# Cleanup
clean:
	@echo "Cleaning build artifacts..."
	rm -rf dist/
	rm -rf infrastructure/cdk.out/
	rm -rf .pytest_cache/
	rm -rf htmlcov/
	rm -f coverage.xml
	rm -f bandit-report.json
	rm -f safety-report.json
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete
	@echo "Cleanup completed"

clean-all: clean
	@echo "Deep cleaning..."
	rm -rf node_modules/
	rm -rf venv/
	rm -rf .venv/

# Development helpers
format:
	@echo "Formatting code..."
	black biomerkin/ tests/ scripts/ infrastructure/
	isort biomerkin/ tests/ scripts/ infrastructure/

lint:
	@echo "Linting code..."
	flake8 biomerkin/ tests/ scripts/ infrastructure/
	pylint biomerkin/ tests/ scripts/ infrastructure/

type-check:
	@echo "Type checking..."
	mypy biomerkin/ scripts/ infrastructure/

quality: format lint type-check security

# Quick deployment workflow
quick-deploy: test build deploy validate

# Full deployment workflow
full-deploy: install test security build deploy validate

# Emergency procedures
emergency-deploy:
	@echo "Emergency deployment to $(ENV)..."
	$(PYTHON) scripts/deploy.py $(ENV) --skip-tests --skip-validation --region $(REGION)

emergency-rollback:
	@echo "Emergency rollback for $(ENV)..."
	@echo "This will rollback to the most recent backup"
	@echo "Available backups:"
	@$(PYTHON) scripts/disaster_recovery.py list $(ENV) --region $(REGION) | head -5
	@echo "Confirm by running: make rollback-to ENV=$(ENV) TIMESTAMP=<latest-timestamp>"

# Health checks
health-check:
	@echo "Running health check for $(ENV)..."
	$(PYTHON) scripts/validate_deployment.py $(ENV) --region $(REGION)

# Documentation
docs:
	@echo "Available documentation:"
	@echo "  docs/deployment_automation.md - Deployment guide"
	@echo "  docs/deployment_guide.md - General deployment info"
	@echo "  README.md - Project overview"

# Version information
version:
	@echo "Biomerkin Multi-Agent System"
	@echo "Python: $(shell $(PYTHON) --version)"
	@echo "CDK: $(shell cdk --version)"
	@echo "AWS CLI: $(shell aws --version)"
	@echo "Region: $(REGION)"
	@echo "Environment: $(ENV)"