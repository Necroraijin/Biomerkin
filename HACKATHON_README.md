# 🧬 Biomerkin - AWS AI Agent Hackathon Submission

## Quick Start (5 minutes)

### 1. Download Sample Data
```bash
python scripts/download_sample_data.py
```

### 2. Test the System
```bash
python scripts/test_hackathon.py
```

### 3. Install Enhanced Features (Optional)
```bash
# Install AWS Strands Agents for advanced multi-agent communication
python scripts/install_strands.py
```

### 4. Run Analysis
```bash
# Standard analysis
biomerkin analyze sample_data/BRCA1.fasta

# Enhanced analysis with Strands Agents
biomerkin analyze sample_data/BRCA1.fasta --enhanced

# One-click impressive demo
python scripts/one_click_demo.py

# Or use the web interface
npm start  # in frontend directory
```

## 🎯 What This Does

Biomerkin is a **multi-agent AI system** that:

1. **GenomicsAgent**: Analyzes DNA sequences for genes and mutations
2. **ProteomicsAgent**: Predicts protein structure and function  
3. **LiteratureAgent**: Searches PubMed and summarizes findings using **Amazon Bedrock**
4. **DrugAgent**: Identifies potential drug candidates
5. **DecisionAgent**: Generates medical reports using **AI reasoning**

## 🏆 Hackathon Compliance

✅ **Amazon Bedrock**: Used for literature analysis and decision-making  
✅ **AWS Lambda**: 5 serverless agent functions  
✅ **Autonomous Agents**: Work independently and collaboratively  
✅ **External APIs**: PubMed, PDB, STRING database integration  
✅ **Real-world Impact**: Accelerates genomic medicine research

## 🚀 Enhanced Features (NEW!)

✅ **AWS Strands Agents**: Advanced multi-agent orchestration  
✅ **Agent-to-Agent Communication**: Real-time messaging and handoffs  
✅ **Swarm Intelligence**: Collaborative analysis across agents  
✅ **Graph Workflows**: Complex orchestration with conditional branching  
✅ **One-Click Demo**: Impressive pre-loaded results for presentations  
✅ **Enhanced CLI**: New commands for advanced features  

## 🚀 Demo Data

- **BRCA1**: Breast cancer gene (perfect for medical analysis)
- **COVID-19**: SARS-CoV-2 genome (relevant and well-studied)  
- **TP53**: Tumor suppressor gene (great for drug discovery)

## 📊 Expected Results

Each analysis produces:
- Gene identification and mutation analysis
- Protein structure predictions
- Literature review with AI summarization
- Drug candidate recommendations
- Comprehensive medical report

## 🔗 Links

- **Live Demo**: [Deploy with CDK]
- **Source Code**: This repository
- **Architecture**: See HACKATHON_SUBMISSION.md

---

*Built for AWS AI Agent Global Hackathon 2025*
