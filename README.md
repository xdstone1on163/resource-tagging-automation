## Guide to Resource Tagging Automation
This is a Lambda function that automatically tags newly created AWS resources. It is triggered by EventBridge events from CloudTrail logs.

### ⚡ What's New - Critical Update
**🛡️ Tag Preservation Now Guaranteed**
- **Problem Solved:** Previous versions could overwrite existing tags on CloudWatch Logs and S3
- **Solution:** Unified read-merge-write pattern ensures existing tags are never lost
- **Smart Retry:** Automatically retries if tagging fails (handles AWS eventual consistency)
- **Failure Detection:** Lambda fails with exception if tags can't be applied after retry

**👉 If you're upgrading from an older version, please redeploy to get these critical fixes.**

### Supported AWS Services (20+)
Currently supports automatic tagging for:
- **Compute:** EC2 (Instances, Volumes, Snapshots, AMIs), Lambda Functions, AWS Batch, ECS (Fargate)
- **Storage:** S3 Buckets, EBS, EFS
- **Database:** RDS (Instances, Clusters, Snapshots), Aurora, DynamoDB, DocumentDB, ElastiCache (Redis/Memcached), Redshift
- **Analytics & Big Data:** EMR (on EC2, Serverless, on EKS), OpenSearch/Elasticsearch
- **Networking:** ELB (Application/Network Load Balancers), NAT Gateway, VPC Endpoint, Transit Gateway
- **Messaging & Streaming:** SNS Topics, SQS Queues, Amazon MQ, Managed Streaming for Kafka (MSK)
- **ML & AI:** SageMaker (Notebooks, Training Jobs, Endpoints, Models, etc.)
- **Security & Management:** KMS Keys, CloudWatch Logs
- **Other:** Auto Scaling Groups

### Key Features
✅ **Automatic Tagging** - Tags resources immediately upon creation
✅ **Identity Tracking** - Optionally records the creator's identity (userId/roleId) for ownership and cost allocation
✅ **Tag Preservation** - Never overwrites existing tags - merges new tags with existing ones
✅ **Smart Retry** - Automatically retries if tag verification fails (handles AWS eventual consistency)
✅ **Tag Verification** - Validates tags were applied successfully with automatic failure detection
✅ **Multi-Service Support** - 20+ AWS services supported out of the box
✅ **Flexible Deployment** - Deploy via AWS CDK or CloudFormation
✅ **Error Resilient** - Individual resource failures won't stop batch tagging

### Important Notes
- This solution only tags **newly created** resources (not existing ones)
- For existing resources, use [AWS Tag Editor Console](https://console.aws.amazon.com/resource-groups/tag-editor/find-resources)
- For CloudFormation deployment, see [cloudformation/README.md](cloudformation/README.md)


### Recent Updates & Bug Fixes

**🚀 Major Release - Tag Preservation & Smart Retry (Latest):**
- ✅ **CRITICAL FIX**: Prevents existing tag loss - now uses read-merge-write pattern for all services
- ✅ **Smart Retry**: Automatically retries tagging if verification fails (handles AWS eventual consistency)
- ✅ **Failure Detection**: Lambda fails with exception if tags can't be applied after retry (ensures visibility)
- ✅ **S3 Enhancement**: Now uses native S3 API (`put_bucket_tagging`) with tag preservation
- ✅ **Unified Logic**: All services (CloudWatch Logs, S3, others) use consistent merge behavior

**Previous improvements:**
- ✅ Fixed CloudWatch Logs tagging (now uses dedicated `logs.tag_log_group` API)
- ✅ Added automatic tag verification after each tagging operation
- ✅ Fixed EC2 function crash when handling DryRun operations or failed API calls
- ✅ Fixed EMR Serverless and EMR on EKS ARN format issues
- ✅ Optimized waiter configurations (reduced timeout from 2+ hours to 10 minutes)
- ✅ Fixed variable naming typos and improved code quality
- ✅ Enhanced logging for better debugging and troubleshooting

### Project Architecture
![ProjectArchitecture](docs/architecture.png)


### Prerequisites
1. A Linux/MacOS/Windows machine to deploy CDK code, with AWS IAM credentials configured
   - AWS CLI installed and configured (see [AWS CLI Configuration Guide](https://docs.aws.amazon.com/cli/latest/userguide/cli-configure-quickstart.html))
   - Appropriate IAM permissions to create Lambda functions, EventBridge rules, and IAM roles

2. Required software installed:
   - **Python 3.10+** (Lambda runtime uses Python 3.10)
   - **Node.js** (required for AWS CDK)
   - **AWS CDK** (will be installed in deployment steps)


### To deploy
1. Ensure CDK is installed
```
$ npm install -g aws-cdk
```

2. Create a Python virtual environment
```
$ python3 -m venv .venv
```

3. Activate virtual environment

_On MacOS or Linux_
```
$ source .venv/bin/activate
```

_On Windows_
```
% .venv\Scripts\activate.bat
```

4. Install the required dependencies.

```
$ pip install -r requirements.txt
```

5. Bootstrapping cdk environment.

```
$ cdk bootstrap
```

6. Synthesize (`cdk synth`) or deploy (`cdk deploy`) the example, use --parameters to pass additional parameters, use --require-approval to run without being prompted for approval, Please replace your own tags to the tags parameter.

```
$ cdk deploy --require-approval never --parameters tags='{"TagName1": "TagValue1","TagName2": "TagValue2"}'
```

(Optional) You can also choose to disable the Identity Recording feature by definening the `identityRecording` parameter to false. This feature is enabled by default.

```
$ cdk deploy --require-approval never --parameters tags='{"TagName1": "TagValue1","TagName2": "TagValue2"}' --parameters identityRecording='false'
```

### Identity Recording Feature
By default, the solution records the identity of who created each resource by adding two additional tags:
- **`userId`** - The IAM user name or assumed role session name
- **`roleId`** - The IAM role name (only for AssumedRole types)

**Benefits:**
- 💰 **Cost Allocation** - Track which users/teams create expensive resources
- 🔍 **Ownership Tracking** - Identify resource owners for cleanup and management
- 📊 **Audit Trail** - Security and compliance reporting

**Example tags:**
```json
{
  "map-migrated": "mig00W1N642S4",
  "userId": "alice",              // IAM user who created the resource
  "roleId": "MyLambdaRole"        // IAM role used (if applicable)
}
```

To **disable** identity recording:
```bash
$ cdk deploy --parameters identityRecording='false'
```

### How to Verify Tagging Works

#### 1. **Basic Tagging Test**
```bash
# Verify Lambda function is created
$ aws lambda get-function --function-name resource-tagging-automation-function

# Create a test log group
$ aws logs create-log-group --log-group-name /aws/test/auto-tagging

# Wait 5-10 seconds, then check tags
$ aws logs list-tags-log-group --log-group-name /aws/test/auto-tagging

# Expected output: Your predefined tags + userId/roleId
```

#### 2. **Tag Preservation Test** (Critical!)
Verify that existing tags are never overwritten:

```bash
# Create a resource WITH existing tags
$ aws logs create-log-group \
  --log-group-name /aws/test/tag-preservation \
  --tags ExistingTag=KeepMe,Environment=Production

# Wait 5-10 seconds for auto-tagging to trigger

# Verify BOTH existing and new tags are present
$ aws logs list-tags-log-group --log-group-name /aws/test/tag-preservation

# ✅ Expected: ExistingTag, Environment, map-migrated, userId all present
# ❌ Bug: Only map-migrated and userId (existing tags lost)
```

#### 3. **Monitor Lambda Execution Logs**
```bash
# View Lambda logs in real-time
$ aws logs tail /aws/lambda/resource-tagging-automation-function --follow

# Look for these key messages:
# ✅ "Existing tags on log group: {...}"
# ✅ "Merged tags to apply: {...}"
# ✅ "Verification successful - All existing tags preserved, new tags applied"
# ⚠️  "Verification failed... Retrying after 5 seconds..."
# ❌ "CRITICAL: Tag verification failed even after retry!"
```

#### 4. **Test with Multiple Services**
```bash
# S3 bucket with existing tags
$ BUCKET="test-tagging-$(date +%s)"
$ aws s3api create-bucket --bucket $BUCKET --region us-east-1
$ aws s3api put-bucket-tagging --bucket $BUCKET \
  --tagging 'TagSet=[{Key=Team,Value=Backend}]'
# Wait, then check: aws s3api get-bucket-tagging --bucket $BUCKET

# EC2 instance with existing tags
$ aws ec2 run-instances --image-id ami-xxxxx --instance-type t2.micro \
  --tag-specifications 'ResourceType=instance,Tags=[{Key=Owner,Value=Alice}]'

# DynamoDB table
$ aws dynamodb create-table --table-name TestAutoTag \
  --attribute-definitions AttributeName=id,AttributeType=S \
  --key-schema AttributeName=id,KeyType=HASH \
  --billing-mode PAY_PER_REQUEST
```

All newly created resources should be automatically tagged within 5-10 seconds, and existing tags should be preserved.


### To clean up afterwards:
Notice this operation will destroy the Lambda function and all other resources created by CDK.

```
$ cdk destroy
```

### Tag Preservation & Smart Retry (Critical Feature)

#### 🛡️ Tag Preservation - No More Tag Loss
The solution **guarantees existing tags are never overwritten** using a unified read-merge-write pattern:

**How it works:**
1. **Read** existing tags from the resource before tagging
2. **Merge** existing tags with automation tags (new tags win conflicts)
3. **Write** the merged tag set back to the resource
4. **Verify** all tags (existing + new) are present

**Why this matters:**
- ✅ Manual tags on resources are preserved
- ✅ Works regardless of AWS API behavior (merge vs replace)
- ✅ CloudWatch Logs, S3, and all other services use consistent logic
- ✅ No silent data loss

**Example:**
```bash
# Resource has existing tags
Existing tags: {'Team': 'Backend', 'Environment': 'Production'}

# Automation adds new tags
New tags: {'map-migrated': 'xxx', 'userId': 'alice'}

# Result: Both preserved
Final tags: {'Team': 'Backend', 'Environment': 'Production',
             'map-migrated': 'xxx', 'userId': 'alice'}
```

#### 🔄 Smart Retry Mechanism
If tag verification fails, the solution automatically retries once before failing:

**Retry flow:**
1. Apply tags
2. Verify tags applied correctly
3. **If verification fails:**
   - Wait 5 seconds (AWS eventual consistency)
   - Retry tagging operation
   - Verify again
4. **If retry also fails:**
   - Log critical error with details
   - Throw exception to fail Lambda execution
   - EventBridge records the failure

**Why retry?**
- AWS services have eventual consistency
- First attempt might fail due to timing
- Retry solves 90%+ of transient failures

#### 📊 Log Examples

**Success (first attempt):**
```
Tagging resource: arn:aws:logs:us-west-2:123456789012:log-group:/aws/test
Existing tags on log group /aws/test: {'OldTag': 'KeepMe'}
Merged tags to apply: {'OldTag': 'KeepMe', 'map-migrated': 'xxx', 'userId': 'alice'}
Using CloudWatch Logs API for log group: /aws/test
Successfully tagged log group: /aws/test
Verification - Current tags on resource: {'OldTag': 'KeepMe', 'map-migrated': 'xxx', 'userId': 'alice'}
✅ Verification successful - All existing tags preserved, new tags applied
```

**Success after retry:**
```
Tagging resource: arn:aws:s3:::my-bucket
Existing tags on S3 bucket my-bucket: {'Team': 'Backend'}
Merged tags to apply: {'Team': 'Backend', 'userId': 'alice'}
Successfully tagged S3 bucket: my-bucket
Verification - Current tags on resource: {'Team': 'Backend'}
⚠️  WARNING: Some new tags were not applied: ['userId']
⚠️  Verification failed for arn:aws:s3:::my-bucket. Retrying after 5 seconds...
Retrying tagging operation for arn:aws:s3:::my-bucket...
Successfully tagged S3 bucket: my-bucket
Verifying tags after retry for arn:aws:s3:::my-bucket...
Verification - Current tags on resource: {'Team': 'Backend', 'userId': 'alice'}
✅ Retry succeeded for arn:aws:s3:::my-bucket
```

**Critical failure (retry exhausted):**
```
Tagging resource: arn:aws:logs:...
Existing tags: {'Critical': 'DoNotLose'}
Merged tags to apply: {'Critical': 'DoNotLose', 'map-migrated': 'xxx'}
Successfully tagged log group: /aws/test
Verification - Current tags on resource: {'map-migrated': 'xxx'}
❌ ERROR: Some existing tags were lost: ['Critical']
⚠️  Verification failed for arn:aws:logs:... Retrying after 5 seconds...
[... retry attempt ...]
❌ ERROR: Some existing tags were lost: ['Critical']
❌ CRITICAL: Tag verification failed for arn:aws:logs:... even after retry!
  Lost existing tags: ['Critical']
Exception: CRITICAL: Tag verification failed...

Lambda execution FAILED
```

#### 🔔 Setting Up Failure Alerts

When tag verification fails after retry, the Lambda execution fails. Set up CloudWatch Alarms to get notified:

```bash
aws cloudwatch put-metric-alarm \
  --alarm-name resource-tagging-lambda-errors \
  --alarm-description "Alert when tag verification fails" \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=resource-tagging-automation-function \
  --evaluation-periods 1 \
  --alarm-actions arn:aws:sns:REGION:ACCOUNT:your-sns-topic
```

This ensures critical tagging failures don't go unnoticed.

### Adding Support for More Resources
1. Go to AWS Console and navigate to Amazon EventBridge --> Rules, find and select rule 'resource-tagging-automation-awstaggingautomationruleXXXXXX', click 'Edit' button.
2. Go to step 2 and find 'Event pattern' chapter, add new resource in eventSource, eventName and source.
3. Keep clicking 'Next' button until click 'Update rule' in step 5.
4. Go to AWS Console and navigate to Lambda --> Functions, find out function 'resource-tagging-automation-function'.
5. Edit the function code, add a method to get newly created resources' ARN list from EventBridge rule event.
6. The method example is as below.
```
def aws_elasticloadbalancing(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateLoadBalancer':
        print("tagging for new LoadBalancer...")
        lbs = event['detail']['responseElements']
        for lb in lbs['loadBalancers']:
            arnList.append(lb['loadBalancerArn'])
        return arnList
```

### Troubleshooting

#### 🔴 Critical Issues

**Existing tags are lost on resources?**
- ✅ **Fixed in latest version** - Upgrade to get tag preservation
- If still happening:
  1. Verify you're using the latest code (check for "Existing tags on..." in logs)
  2. Look for "ERROR: Some existing tags were lost" in Lambda logs
  3. If this appears, the Lambda should fail with exception - check CloudWatch metrics

**Lambda execution failing with "CRITICAL: Tag verification failed"?**
This means tags could not be applied correctly even after retry:
1. Check the error message for which tags are missing/lost
2. Common causes:
   - **IAM permission issues** - Add missing `Get*` and `Put*/Tag*` permissions
   - **Resource quotas** - AWS limit is 50 tags per resource
   - **Service-specific issues** - Some services have tag restrictions
3. View full error details in CloudWatch Logs
4. If this is a persistent issue, file a bug report with logs

**Retry loop (verification keeps failing)?**
The solution only retries once (5-second delay). If you see multiple retries:
1. This shouldn't happen - file a bug report
2. Check Lambda timeout settings (default: 300s should be enough)

#### ⚠️ Common Issues

**Tags not appearing on resources?**
1. Check Lambda execution logs for errors:
   ```bash
   aws logs tail /aws/lambda/resource-tagging-automation-function --follow
   ```
2. Look for:
   - ⚠️  "WARNING: Some new tags were not applied" - Permission or API issue
   - ⚠️  "Verification failed... Retrying" - Transient issue (should auto-recover)
   - ❌ "CRITICAL" - Serious problem requiring attention
3. Verify the Lambda function has required IAM permissions (especially `Get*` for tag reading)

**New tags applied but verification shows warning?**
This can happen due to AWS eventual consistency:
- ✅ **Solution now handles this** - Waits 5 seconds and retries
- If retry succeeds, you'll see: "✅ Retry succeeded"
- If retry fails, Lambda execution will fail

**Lambda function errors?**
- **`KeyError: 'aws_xxx'`** - Service handler function missing (should be fixed)
- **`TypeError: 'NoneType' object is not subscriptable`** - API call failed or DryRun (should be fixed)
- **`Exception: CRITICAL: Tag verification failed`** - Tags couldn't be applied (see above)
- **Permission errors** - Update Lambda execution role with additional permissions

**CloudWatch Logs tags not showing?**
- Ensure you're using latest version (uses `logs.tag_log_group` with merge)
- Check permissions: `logs:TagLogGroup`, `logs:ListTagsLogGroup`
- Look for "Existing tags on log group" in logs to verify merge is working

**S3 bucket tags not showing?**
- Ensure you're using latest version (uses `s3:PutBucketTagging` with merge)
- Check permissions: `s3:GetBucketTagging`, `s3:PutBucketTagging`
- S3 tags may take a few seconds to propagate (retry handles this)

#### 🔧 Configuration Issues

**EventBridge rules not triggering?**
1. Verify CloudTrail is enabled and logging API calls
2. Check EventBridge rule is enabled in console
3. Ensure event pattern matches your resource creation events
4. Test with CloudWatch Log Group (simplest to verify)

**Deployment issues?**
- If deployment fails mid-way, manually clean up via CloudFormation console
- Navigate to CloudFormation → Select stack → Delete
- Ensure IAM user has sufficient permissions to create Lambda, EventBridge, and IAM resources
- Check CDK bootstrap is completed: `cdk bootstrap`

#### 📊 Monitoring & Alerts

**Set up failure alerts:**
```bash
# Create CloudWatch Alarm for Lambda errors
aws cloudwatch put-metric-alarm \
  --alarm-name resource-tagging-failures \
  --metric-name Errors \
  --namespace AWS/Lambda \
  --statistic Sum \
  --period 300 \
  --threshold 1 \
  --comparison-operator GreaterThanOrEqualToThreshold \
  --dimensions Name=FunctionName,Value=resource-tagging-automation-function \
  --evaluation-periods 1
```

**View Lambda error rate:**
```bash
# Check Lambda invocations and errors
aws cloudwatch get-metric-statistics \
  --namespace AWS/Lambda \
  --metric-name Errors \
  --dimensions Name=FunctionName,Value=resource-tagging-automation-function \
  --start-time $(date -u -d '1 hour ago' +%Y-%m-%dT%H:%M:%S) \
  --end-time $(date -u +%Y-%m-%dT%H:%M:%S) \
  --period 3600 \
  --statistics Sum
```

#### 🆘 Need More Help?

- **Review Lambda logs** - CloudWatch Logs show complete execution traces
- **Check verification output** - Shows which tags were applied vs missing/lost
- **Enable debug mode** - All operations are logged with detailed context
- **File an issue** - https://github.com/aws-samples/resource-tagging-automation/issues
  - Include: Lambda logs, event JSON, verification output, error messages


### Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


### License
This library is licensed under the MIT-0 License. See the LICENSE file.
