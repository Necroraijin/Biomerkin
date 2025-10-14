# 🚀 AWS Setup Guide for Beginners - Biomerkin Deployment

**Perfect for first-time AWS users!** This guide will walk you through everything step-by-step.

---

## 📋 **STEP 1: Create AWS Account (5 minutes)**

### 1.1 Sign Up for AWS
1. Go to [aws.amazon.com](https://aws.amazon.com)
2. Click **"Create an AWS Account"**
3. Enter your email and choose **"Personal"** account type
4. Fill in your information
5. **Add a credit card** (required, but we'll use free tier)
6. **Phone verification** - AWS will call you
7. Choose **"Basic Support Plan"** (free)

### 1.2 Important Notes
- ✅ **Free Tier**: Most services we'll use are free for 12 months
- ✅ **Cost Control**: We'll set up billing alerts
- ⚠️ **Credit Card**: Required but charges will be minimal ($5-20 max)

---

## 🔑 **STEP 2: Set Up AWS CLI (10 minutes)**

### 2.1 Install AWS CLI
```bash
# Download AWS CLI installer for Windows
# Go to: https://awscli.amazonaws.com/AWSCLIV2.msi
# Run the installer

# Verify installation
aws --version
```

### 2.2 Create Access Keys
1. **Log into AWS Console**: [console.aws.amazon.com](https://console.aws.amazon.com)
2. **Click your name** (top right) → **"Security credentials"**
3. **Scroll down** to "Access keys"
4. **Click "Create access key"**
5. **Choose "CLI"** → Check the box → **"Create"**
6. **IMPORTANT**: Copy both keys immediately!
   - Access Key ID: `AKIA...`
   - Secret Access Key: `wJalr...`

### 2.3 Configure AWS CLI
```bash
# Run this command and enter your keys
aws configure

# Enter when prompted:
AWS Access Key ID: [paste your access key]
AWS Secret Access Key: [paste your secret key]
Default region name: us-east-1
Default output format: json
```

### 2.4 Test Your Setup
```bash
# This should show your account info
aws sts get-caller-identity
```

---

## 🛡️ **STEP 3: Set Up Security & Billing (5 minutes)**

### 3.1 Enable Billing Alerts
1. **AWS Console** → Search **"Billing"**
2. **Billing Preferences** → Check **"Receive Billing Alerts"**
3. **Save preferences**

### 3.2 Create Budget Alert
1. **AWS Console** → Search **"Budgets"**
2. **Create budget** → **"Cost budget"**
3. **Budget name**: "Biomerkin-Hackathon"
4. **Amount**: $50 (safety limit)
5. **Alert threshold**: 80% ($40)
6. **Email**: Your email address
7. **Create budget**

---

## 🏗️ **STEP 4: Deploy Biomerkin to AWS (Automated)**

I'll create an automated deployment script that does everything for you!

### 4.1 Run the Deployment Script
```bash
# This will deploy everything automatically
python scripts/deploy_biomerkin_to_aws.py
```

### 4.2 What This Script Does
- ✅ Creates all AWS resources
- ✅ Deploys Lambda functions
- ✅ Sets up API Gateway
- ✅ Configures DynamoDB
- ✅ Deploys frontend to S3
- ✅ Sets up Bedrock access
- ✅ Configures monitoring

---

## 📱 **STEP 5: Test Your Deployment (5 minutes)**

### 5.1 Test the API
```bash
# Test if your API is working
python scripts/test_aws_deployment.py
```

### 5.2 Test the Frontend
The script will give you a URL like:
```
🌐 Frontend URL: https://biomerkin-demo.s3-website-us-east-1.amazonaws.com
```

### 5.3 Test Demo Scenarios
```bash
# Test all demo scenarios on AWS
python demo/judge_demo_runner.py --aws-mode
```

---

## 🎯 **STEP 6: Hackathon Demo Preparation**

### 6.1 Get Your Demo URLs
After deployment, you'll have:
- **Frontend URL**: For judges to interact with
- **API Endpoints**: For live demonstrations
- **CloudWatch Logs**: To show real-time processing

### 6.2 Demo Script for Judges
```
"Let me show you our live AWS deployment:

1. Frontend: [Open your S3 website URL]
2. Select BRCA1 demo scenario
3. Watch real-time agent collaboration
4. See AI-generated medical report
5. Show CloudWatch logs of agent processing"
```

---

## 🆘 **TROUBLESHOOTING GUIDE**

### Common Issues & Solutions

#### ❌ "Access Denied" Errors
**Solution**: Check your AWS credentials
```bash
aws sts get-caller-identity
# Should show your account info
```

#### ❌ "Region Not Supported" 
**Solution**: Use us-east-1 (most services available)
```bash
aws configure set region us-east-1
```

#### ❌ "Bedrock Not Available"
**Solution**: Request access to Bedrock
1. AWS Console → Search "Bedrock"
2. "Model access" → "Request access"
3. Select "Claude 3 Sonnet"
4. Submit request (usually approved in minutes)

#### ❌ Lambda Deployment Fails
**Solution**: Check file sizes and permissions
```bash
# Check if files are too large
ls -la lambda_functions/
# Should be under 50MB each
```

---

## 💰 **COST BREAKDOWN (Expected)**

| Service | Free Tier | Expected Cost |
|---------|-----------|---------------|
| **Lambda** | 1M requests/month | $0 |
| **API Gateway** | 1M requests/month | $0 |
| **DynamoDB** | 25GB storage | $0 |
| **S3** | 5GB storage | $0 |
| **Bedrock** | Limited free usage | $5-15 |
| **CloudWatch** | Basic monitoring | $0 |
| **Total** | | **$5-15/month** |

---

## 🎉 **SUCCESS CHECKLIST**

After deployment, you should have:
- [ ] ✅ AWS account created and configured
- [ ] ✅ AWS CLI working (`aws sts get-caller-identity`)
- [ ] ✅ Billing alerts set up
- [ ] ✅ All AWS resources deployed
- [ ] ✅ Frontend accessible via URL
- [ ] ✅ API endpoints responding
- [ ] ✅ Demo scenarios working
- [ ] ✅ CloudWatch logs showing activity

---

## 🚀 **NEXT: Run the Automated Deployment**

Ready to deploy? Let's create the automated deployment script that will handle everything for you!

The script will:
1. **Check your AWS setup**
2. **Create all resources**
3. **Deploy your code**
4. **Test everything**
5. **Give you demo URLs**

**Total time: 15-20 minutes for complete deployment!**

---

*Don't worry - I'll guide you through each step and create scripts that do the heavy lifting!*