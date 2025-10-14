# Biomerkin Multi-Agent Bioinformatics System

Biomerkin is a cloud-native multi-agent bioinformatics system built on AWS infrastructure that orchestrates specialized agents to analyze DNA sequences, predict protein structures, research literature, identify drug candidates, and generate comprehensive medical reports.

## Features

- **GenomicsAgent**: DNA sequence analysis using Biopython
- **ProteomicsAgent**: Protein structure and function analysis via PDB API
- **LiteratureAgent**: Scientific literature research and AI-powered summarization
- **DrugAgent**: Drug discovery and clinical trial information
- **DecisionAgent**: Comprehensive medical report generation
- **AWS Integration**: Leverages Lambda, Bedrock, S3, and DynamoDB
- **Scalable Architecture**: Serverless, event-driven processing

## Project Structure

```
biomerkin/
├── agents/          # Specialized analysis agents
├── models/          # Data models and structures
├── services/        # External API integrations
├── utils/           # Utilities and common functionality
└── __init__.py
```

## Installation

```bash
# Clone the repository
git clone https://github.com/biomerkin/biomerkin-multi-agent-system.git
cd biomerkin-multi-agent-system

# Install dependencies
pip install -r requirements.txt

# Install the package
pip install -e .
```

## Configuration

Create a configuration file or set environment variables:

```python
from biomerkin.utils import create_sample_config

# Create a sample configuration file
create_sample_config('./biomerkin_config.json')
```

Required environment variables:
- `AWS_REGION`: AWS region for services
- `PUBMED_EMAIL`: Email for PubMed API access
- `BEDROCK_MODEL_ID`: Amazon Bedrock model identifier
- `S3_BUCKET_NAME`: S3 bucket for data storage
- `DYNAMODB_TABLE_NAME`: DynamoDB table for workflow state

## Usage

```python
from biomerkin.models import WorkflowState, GenomicsResults
from biomerkin.utils import get_config

# Load configuration
config = get_config()

# Create and run analysis workflow
# (Implementation details in subsequent tasks)
```

## Data Models

The system includes comprehensive data models for:

- **Genomics**: Genes, mutations, protein sequences
- **Proteomics**: Protein structures, functional annotations, domains
- **Literature**: Articles, study summaries, research insights
- **Drug Discovery**: Drug candidates, clinical trials, interactions
- **Medical Reports**: Risk assessments, treatment recommendations

## Development

```bash
# Install development dependencies
pip install -e ".[dev]"

# Run tests
pytest

# Format code
black biomerkin/

# Type checking
mypy biomerkin/
```

## Architecture

The system follows a multi-agent architecture with:

1. **Orchestration Layer**: Manages workflow execution
2. **Agent Layer**: Specialized analysis agents
3. **Compute Layer**: AWS Lambda functions
4. **AI Layer**: Amazon Bedrock for LLM capabilities
5. **Storage Layer**: S3 and DynamoDB
6. **External APIs**: PubMed, PDB, DrugBank, ClinicalTrials.gov

## License

MIT License - see LICENSE file for details.

## Contributing

Please read CONTRIBUTING.md for details on our code of conduct and the process for submitting pull requests.

## AWS Hackathon

This project is developed for the AWS Agent Hackathon, demonstrating the power of multi-agent systems in bioinformatics and healthcare applications.