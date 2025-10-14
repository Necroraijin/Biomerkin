#!/usr/bin/env node

const AWS = require('aws-sdk');
const fs = require('fs');
const path = require('path');
const mime = require('mime-types');
const { execSync } = require('child_process');

// Configuration
const config = {
  bucketName: process.env.S3_BUCKET_NAME || 'biomerkin-frontend',
  region: process.env.AWS_REGION || 'us-east-1',
  distributionId: process.env.CLOUDFRONT_DISTRIBUTION_ID,
  buildDir: path.join(__dirname, 'build'),
  profile: process.env.AWS_PROFILE,
};

// Initialize AWS SDK
if (config.profile) {
  AWS.config.credentials = new AWS.SharedIniFileCredentials({ profile: config.profile });
}
AWS.config.region = config.region;

const s3 = new AWS.S3();
const cloudfront = new AWS.CloudFront();

// Utility functions
const log = (message) => console.log(`[DEPLOY] ${message}`);
const error = (message) => console.error(`[ERROR] ${message}`);

// Build the React application
async function buildApp() {
  log('Building React application...');
  try {
    execSync('npm run build', { stdio: 'inherit', cwd: __dirname });
    log('Build completed successfully');
  } catch (err) {
    error('Build failed');
    throw err;
  }
}

// Get all files in build directory recursively
function getAllFiles(dir, fileList = []) {
  const files = fs.readdirSync(dir);
  
  files.forEach(file => {
    const filePath = path.join(dir, file);
    const stat = fs.statSync(filePath);
    
    if (stat.isDirectory()) {
      getAllFiles(filePath, fileList);
    } else {
      fileList.push(filePath);
    }
  });
  
  return fileList;
}

// Upload file to S3
async function uploadFile(filePath) {
  const relativePath = path.relative(config.buildDir, filePath);
  const key = relativePath.replace(/\\/g, '/'); // Convert Windows paths to Unix
  const contentType = mime.lookup(filePath) || 'application/octet-stream';
  const fileContent = fs.readFileSync(filePath);
  
  // Set cache control headers
  let cacheControl = 'public, max-age=31536000'; // 1 year for static assets
  if (key === 'index.html' || key.endsWith('.html')) {
    cacheControl = 'public, max-age=0, must-revalidate'; // No cache for HTML
  } else if (key.startsWith('static/')) {
    cacheControl = 'public, max-age=31536000, immutable'; // Immutable for hashed assets
  }
  
  const params = {
    Bucket: config.bucketName,
    Key: key,
    Body: fileContent,
    ContentType: contentType,
    CacheControl: cacheControl,
    ACL: 'public-read',
  };
  
  // Add compression for text files
  if (contentType.startsWith('text/') || 
      contentType.includes('javascript') || 
      contentType.includes('json') ||
      contentType.includes('css')) {
    params.ContentEncoding = 'gzip';
    // Note: In production, you'd want to actually gzip the content
  }
  
  try {
    await s3.upload(params).promise();
    log(`Uploaded: ${key}`);
  } catch (err) {
    error(`Failed to upload ${key}: ${err.message}`);
    throw err;
  }
}

// Upload all files to S3
async function uploadToS3() {
  log('Uploading files to S3...');
  
  // Check if bucket exists
  try {
    await s3.headBucket({ Bucket: config.bucketName }).promise();
  } catch (err) {
    if (err.statusCode === 404) {
      log(`Creating S3 bucket: ${config.bucketName}`);
      await s3.createBucket({
        Bucket: config.bucketName,
        CreateBucketConfiguration: {
          LocationConstraint: config.region !== 'us-east-1' ? config.region : undefined
        }
      }).promise();
      
      // Configure bucket for static website hosting
      await s3.putBucketWebsite({
        Bucket: config.bucketName,
        WebsiteConfiguration: {
          IndexDocument: { Suffix: 'index.html' },
          ErrorDocument: { Key: 'index.html' } // SPA routing
        }
      }).promise();
      
      // Set bucket policy for public read access
      const bucketPolicy = {
        Version: '2012-10-17',
        Statement: [{
          Sid: 'PublicReadGetObject',
          Effect: 'Allow',
          Principal: '*',
          Action: 's3:GetObject',
          Resource: `arn:aws:s3:::${config.bucketName}/*`
        }]
      };
      
      await s3.putBucketPolicy({
        Bucket: config.bucketName,
        Policy: JSON.stringify(bucketPolicy)
      }).promise();
    } else {
      throw err;
    }
  }
  
  const files = getAllFiles(config.buildDir);
  log(`Found ${files.length} files to upload`);
  
  // Upload files in parallel (with concurrency limit)
  const concurrency = 10;
  for (let i = 0; i < files.length; i += concurrency) {
    const batch = files.slice(i, i + concurrency);
    await Promise.all(batch.map(uploadFile));
  }
  
  log('All files uploaded successfully');
}

// Create CloudFront invalidation
async function invalidateCloudFront() {
  if (!config.distributionId) {
    log('No CloudFront distribution ID provided, skipping invalidation');
    return;
  }
  
  log('Creating CloudFront invalidation...');
  
  try {
    const params = {
      DistributionId: config.distributionId,
      InvalidationBatch: {
        CallerReference: Date.now().toString(),
        Paths: {
          Quantity: 1,
          Items: ['/*']
        }
      }
    };
    
    const result = await cloudfront.createInvalidation(params).promise();
    log(`Invalidation created: ${result.Invalidation.Id}`);
  } catch (err) {
    error(`Failed to create invalidation: ${err.message}`);
    throw err;
  }
}

// Setup CloudFront distribution (if needed)
async function setupCloudFront() {
  if (config.distributionId) {
    log('Using existing CloudFront distribution');
    return;
  }
  
  log('Setting up CloudFront distribution...');
  
  const params = {
    DistributionConfig: {
      CallerReference: Date.now().toString(),
      Comment: 'Biomerkin Frontend Distribution',
      DefaultCacheBehavior: {
        TargetOriginId: 'S3Origin',
        ViewerProtocolPolicy: 'redirect-to-https',
        TrustedSigners: {
          Enabled: false,
          Quantity: 0
        },
        ForwardedValues: {
          QueryString: false,
          Cookies: { Forward: 'none' }
        },
        MinTTL: 0,
        DefaultTTL: 86400,
        MaxTTL: 31536000
      },
      Origins: {
        Quantity: 1,
        Items: [{
          Id: 'S3Origin',
          DomainName: `${config.bucketName}.s3.amazonaws.com`,
          S3OriginConfig: {
            OriginAccessIdentity: ''
          }
        }]
      },
      Enabled: true,
      DefaultRootObject: 'index.html',
      CustomErrorResponses: {
        Quantity: 1,
        Items: [{
          ErrorCode: 404,
          ResponseCode: 200,
          ResponsePagePath: '/index.html',
          ErrorCachingMinTTL: 300
        }]
      },
      PriceClass: 'PriceClass_100'
    }
  };
  
  try {
    const result = await cloudfront.createDistribution(params).promise();
    log(`CloudFront distribution created: ${result.Distribution.Id}`);
    log(`Domain name: ${result.Distribution.DomainName}`);
    log('Note: It may take 15-20 minutes for the distribution to be fully deployed');
  } catch (err) {
    error(`Failed to create CloudFront distribution: ${err.message}`);
    throw err;
  }
}

// Main deployment function
async function deploy() {
  try {
    log('Starting deployment process...');
    
    await buildApp();
    await uploadToS3();
    await setupCloudFront();
    await invalidateCloudFront();
    
    log('Deployment completed successfully!');
    log(`Website URL: https://${config.bucketName}.s3-website-${config.region}.amazonaws.com`);
    
    if (config.distributionId) {
      log('CloudFront invalidation in progress...');
    }
    
  } catch (err) {
    error(`Deployment failed: ${err.message}`);
    process.exit(1);
  }
}

// Run deployment if called directly
if (require.main === module) {
  deploy();
}

module.exports = { deploy, buildApp, uploadToS3, invalidateCloudFront };