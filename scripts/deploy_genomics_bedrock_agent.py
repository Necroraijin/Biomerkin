#!/usr/bin/env python3
"""
Deployment script for GenomicsAgent Bedrock Agent.
This script deploys the enhanced autonomous GenomicsAgent with Bedrock Agent capabilities.
"""

import boto3
import json
import logging
import time
import sys
import os
from typing import Dict, Any
from datetime import datetime

# Add the project root to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from lambda_functions.bedrock_genomics_agent_config import Geno