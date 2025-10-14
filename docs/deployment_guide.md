# Biomerkin AWS Deployment Guide

## Overview

This guide provides step-by-step instructions for deploying the Biomerkin multi-agent bioinformatics system on AWS infrastructure with cost optimization features.

## Prerequisites

### AWS Account Setup
- AWS account with appropriate permissions
- AWS CLI configured with credentials
- Python 3.9+ installed
- Boto3 library installed (`pip install boto3`)

### Required Permissions
Your AWS user/role needs the following permissions:
- IAM: Create/manage roles and policies
- Lambda: Create/manage functions
- API Gateway: Create/manage REST APIs
- DynamoDB: Create/manage tables
- S3: Create/manage buckets
- CloudWatch: Create/manage logs, metrics, and alarms
- SNS: Create/manage topics and subscriptions
- Budgets: Create/manage budget alerts

## Deployment Steps

### 1. Clone and Prepare the Repository

```bash
git clone <repository-url>
cd biomerkin
pip install -r requirements.txt
```

### 2. Configure Deployment Parameters

Edit the deployment configuration or use command-line arguments:

```bash
# Basic deployment
python deploy/aws_deployment.py --region us-east-1 --email your-email@domain.com --budget 100

# Deployment with custom settings
python deploy/aws_deployment.py \
  --region us-west-2 \
  --email admin@yourcompany.com \
  --budget 250
```

### 3. Run the Deployment

The deployment script will automatically:
1. Create IAM roles and policies
2. Set up DynamoDB tables
3. Create S3 buckets with security configurations
4. Deploy Lambda functions
5. Configure API Gateway with CORS
6. Set up CloudWatch monitoring and alerts

### 4. Validate Deployment

```bash
# Validate existing deployment
python deploy/aws_deployment.py --validate-only
```

## Architecture Components

### Lambda Functions
- **biomerkin-orchestrator**: Workflow coordination
- **biomerkin-genomics**: DNA sequence analysis
- **biomerkin-proteomics**: Protein structure analysis
- **biomerkin-literature**: Literature research and summarization
- **biomerkin-drug**: Drug discovery and clinical trials
- **biomerkin-decision**: Report generation

### DynamoDB Tables
- **biomerkin-workflows**: Workflow state management
- **biomerkin-analysis-results**: Agent results storage
- **biomerkin-user-sessions**: User session management
- **biomerkin-audit-logs**: Audit trail logging

### S3 Buckets
- **biomerkin-data**: Input DNA sequences and intermediate data
- **biomerkin-results**: Processed results and reports
- **biomerkin-logs**: Access logs and audit trails
- **biomerkin-temp**: Temporary processing files

### API Gateway Endpoints

```
POST /workflows                    # Start new analysis
GET  /workflows/{id}              # Get workflow status
GET  /workflows/{id}/results      # Get analysis results
POST /analysis/genomics           # Direct genomics analysis
POST /analysis/proteomics         # Direct proteomics analysis
POST /analysis/literature         # Direct literature search
POST /analysis/drug               # Direct drug discovery
POST /analysis/decision           # Direct report generation
```

## Cost Optimization Features

### 1. Lambda Optimization
- Right-sized memory allocation per function
- Timeout optimization to prevent unnecessary charges
- Efficient code packaging to reduce cold start times

### 2. DynamoDB Optimization
- On-demand billing mode (pay per request)
- Global Secondary Indexes only where necessary
- Point-in-time recovery for critical tables only

### 3. S3 Optimization
- Lifecycle policies for automatic data archiving:
  - Standard → Standard-IA (30 days)
  - Standard-IA → Glacier (90 days)
  - Glacier → Deep Archive (365 days)
- Automatic cleanup of incomplete multipart uploads
- Server-side encryption with S3-managed keys (no additional cost)

### 4. CloudWatch Optimization
- Log retention policies (30 days default)
- Custom metrics only for critical business KPIs
- Efficient alarm configuration to minimize costs

### 5. Budget Monitoring
- Monthly budget alerts at 80% and 100% thresholds
- Service-specific cost tracking
- Automated notifications for cost anomalies

## Monitoring and Alerting

### CloudWatch Dashboard
Access the Biomerkin monitoring dashboard at:
```
https://console.aws.amazon.com/cloudwatch/home?region=us-east-1#dashboards:name=BiomerkinMonitoring
```

### Key Metrics Monitored
- Lambda function invocations, duration, and errors
- DynamoDB read/write capacity and throttling
- S3 storage usage and request metrics
- Custom workflow metrics (started, completed, failed)
- API Gateway request counts and latency

### Alert Conditions
- Lambda function errors > 5 in 10 minutes
- Lambda function duration > 30 seconds average
- DynamoDB throttling events
- Budget threshold breaches

## Security Features

### Data Protection
- All data encrypted in transit and at rest
- S3 buckets with public access blocked
- IAM roles with least-privilege access
- VPC endpoints for private communication (optional)

### Access Control
- Function-specific IAM roles
- API Gateway with optional authentication
- Audit logging for all data access
- Session management for user tracking

## Troubleshooting

### Common Issues

#### 1. IAM Permission Errors
```bash
# Check current user permissions
aws sts get-caller-identity
aws iam get-user
```

#### 2. Lambda Deployment Failures
- Check function size limits (250MB unzipped)
- Verify IAM role ARNs are correct
- Ensure all dependencies are included

#### 3. API Gateway CORS Issues
- Verify OPTIONS method is configured
- Check CORS headers in Lambda responses
- Test with browser developer tools

#### 4. DynamoDB Throttling
- Monitor read/write capacity metrics
- Consider switching to provisioned capacity for predictable workloads
- Implement exponential backoff in application code

### Log Analysis

#### Lambda Function Logs
```bash
# View recent logs
aws logs describe-log-groups --log-group-name-prefix "/aws/lambda/biomerkin"
aws logs get-log-events --log-group-name "/aws/lambda/biomerkin-orchestrator" --log-stream-name "latest"
```

#### API Gateway Logs
```bash
# Enable API Gateway logging
aws apigateway update-stage --rest-api-id <api-id> --stage-name prod --patch-ops op=replace,path=/accessLogSettings/destinationArn,value=<log-group-arn>
```

## Performance Optimization

### Lambda Performance
- Use connection pooling for database connections
- Implement caching for frequently accessed data
- Optimize memory allocation based on profiling results

### API Performance
- Enable API Gateway caching for GET endpoints
- Use CloudFront for static content delivery
- Implement request/response compression

### Database Performance
- Design efficient partition keys for DynamoDB
- Use batch operations where possible
- Monitor and optimize query patterns

## Maintenance

### Regular Tasks
1. Review CloudWatch metrics weekly
2. Update Lambda function code as needed
3. Monitor and optimize costs monthly
4. Review and rotate access keys quarterly
5. Update security policies annually

### Backup and Recovery
- DynamoDB point-in-time recovery enabled
- S3 versioning enabled for critical buckets
- Lambda function code stored in version control
- Infrastructure as Code for disaster recovery

## Cost Estimation and Optimization

### Detailed Monthly Cost Breakdown (1000 workflows/month)

#### Lambda Functions
- **Orchestrator**: $10.50 (1000 invocations, 5s avg, 1024MB)
- **Genomics Agent**: $22.75 (1000 invocations, 45s avg, 2048MB)
- **Proteomics Agent**: $16.20 (1000 invocations, 30s avg, 1536MB)
- **Literature Agent**: $12.85 (1000 invocations, 25s avg, 1024MB)
- **Drug Agent**: $10.30 (1000 invocations, 20s avg, 1024MB)
- **Decision Agent**: $18.05 (1000 invocations, 35s avg, 1024MB)
- **Total Lambda**: $90.65/month

#### DynamoDB (On-Demand)
- **Workflows Table**: $8.25 (5K reads, 2K writes, 0.5GB storage)
- **Results Table**: $12.40 (2K reads, 5K writes, 2GB storage)
- **Sessions Table**: $4.15 (3K reads, 1.5K writes, 0.2GB storage)
- **Audit Logs**: $6.80 (500 reads, 3K writes, 1GB storage)
- **Total DynamoDB**: $31.60/month

#### S3 Storage (with Lifecycle Policies)
- **Data Bucket**: $12.30 (10GB Standard, 25GB IA, 50GB Glacier)
- **Results Bucket**: $18.75 (5GB Standard, 40GB IA, 100GB Glacier)
- **Logs Bucket**: $2.15 (2GB Standard)
- **Total S3**: $33.20/month

#### Additional Services
- **API Gateway**: $5.25 (15K requests/month)
- **CloudWatch**: $8.90 (5GB logs, 20 metrics, 10 alarms)
- **SNS**: $1.50 (500 notifications)
- **Bedrock**: $15.75 (500K input tokens, 200K output tokens)
- **Total Other**: $31.40/month

### **Total Estimated Cost: $186.85/month**
### **Cost per Workflow: $0.187**

### Cost Optimization Features Built-In

#### 1. S3 Lifecycle Optimization
- **30 days**: Standard → Standard-IA (45% cost reduction)
- **90 days**: Standard-IA → Glacier (68% cost reduction)
- **365 days**: Glacier → Deep Archive (77% cost reduction)
- **7 years**: Automatic deletion for compliance

#### 2. Lambda Memory Optimization
- Right-sized memory allocation based on computational requirements
- Optimized timeouts to prevent unnecessary charges
- Efficient code packaging to reduce cold start times

#### 3. DynamoDB Cost Controls
- On-demand billing for unpredictable workloads
- Efficient query patterns and batch operations
- Point-in-time recovery only for critical tables
- TTL for temporary data cleanup

#### 4. CloudWatch Cost Management
- 30-day log retention for critical functions
- 14-day retention for standard functions
- Custom metrics focused on business KPIs
- Efficient alarm configuration

### Immediate Cost Reduction Strategies

#### Week 1: Quick Wins (15-25% savings)
1. **Lambda Memory Tuning**: Profile and adjust memory allocations
2. **S3 Lifecycle Activation**: Ensure all policies are active
3. **Log Retention Optimization**: Implement retention policies
4. **API Gateway Caching**: Enable for read-heavy endpoints

#### Month 1-3: Medium-term (20-40% savings)
1. **DynamoDB Analysis**: Consider provisioned capacity for predictable loads
2. **Bedrock Optimization**: Fine-tune prompts and model selection
3. **Batch Processing**: Group similar workflows for efficiency
4. **Lambda Layers**: Reduce deployment package sizes

#### Month 3+: Long-term (30-60% savings)
1. **Reserved Capacity**: For predictable workloads
2. **Multi-region Optimization**: Regional pricing differences
3. **Custom Models**: Replace external APIs where feasible
4. **Advanced Caching**: Redis/ElastiCache for complex scenarios

### Cost Monitoring and Alerts

#### Automated Budget Management
```python
budget_configuration = {
    'monthly_limit': 200.0,  # Configurable
    'alert_thresholds': [80, 100],  # 80% warning, 100% critical
    'service_breakdown': True,
    'anomaly_detection': True,
    'daily_reports': True
}
```

#### Key Cost Metrics
- **Cost per workflow**: Target $0.15-0.20
- **Processing efficiency**: Duration vs. cost optimization
- **Storage efficiency**: Lifecycle transition rates
- **API efficiency**: Caching hit rates vs. request costs

### Emergency Cost Controls

#### If Budget Exceeded
1. **Lambda Concurrency Limits**: Prevent runaway executions
2. **API Gateway Throttling**: Control request volumes
3. **S3 Request Limits**: Implement request quotas
4. **Bedrock Usage Caps**: Set monthly token limits

#### Cost Anomaly Response
1. **Automated Alerts**: Real-time notifications
2. **Resource Scaling**: Automatic scale-down procedures
3. **Service Isolation**: Isolate high-cost components
4. **Fallback Modes**: Reduced functionality options

## Support and Documentation

### AWS Documentation
- [Lambda Developer Guide](https://docs.aws.amazon.com/lambda/)
- [DynamoDB Developer Guide](https://docs.aws.amazon.com/dynamodb/)
- [API Gateway Developer Guide](https://docs.aws.amazon.com/apigateway/)
- [S3 User Guide](https://docs.aws.amazon.com/s3/)

### Biomerkin-Specific Resources
- API Documentation: `deploy/biomerkin_api_spec.json`
- Architecture Diagrams: `docs/architecture/`
- Code Documentation: Inline comments and docstrings

For additional support, please refer to the project repository or contact the development team.