## Guide to Resource Tagging Automation
This is a Lambda function that automatically tags newly created AWS resources. It is triggered by EventBridge events from CloudTrail logs.

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
✅ **Tag Verification** - Validates tags were applied successfully with detailed logging
✅ **Multi-Service Support** - 20+ AWS services supported out of the box
✅ **Flexible Deployment** - Deploy via AWS CDK or CloudFormation
✅ **Error Resilient** - Individual resource failures won't stop batch tagging

### Important Notes
- This solution only tags **newly created** resources (not existing ones)
- For existing resources, use [AWS Tag Editor Console](https://console.aws.amazon.com/resource-groups/tag-editor/find-resources)
- For CloudFormation deployment, see [cloudformation/README.md](cloudformation/README.md)


### Recent Updates & Bug Fixes
**Latest improvements:**
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
1. **Verify Lambda function is created:**
```bash
$ aws lambda get-function --function-name resource-tagging-automation-function
```

2. **Test with a CloudWatch Log Group** (easiest to test):
```bash
# Create a test log group
$ aws logs create-log-group --log-group-name /aws/test/auto-tagging

# Check the tags (should see your predefined tags + userId/roleId)
$ aws logs list-tags-log-group --log-group-name /aws/test/auto-tagging
```

3. **Monitor Lambda execution logs:**
```bash
# View Lambda logs in real-time
$ aws logs tail /aws/lambda/resource-tagging-automation-function --follow

# Look for these messages:
# - "tagging for new CloudWatch Log Group..."
# - "Successfully tagged..."
# - "Verification successful - All tags applied correctly"
```

4. **Test with other resources:**
```bash
# Create an EC2 instance
$ aws ec2 run-instances --image-id ami-xxxxx --instance-type t2.micro

# Create an S3 bucket
$ aws s3 mb s3://my-test-bucket-with-auto-tags

# Create a DynamoDB table
$ aws dynamodb create-table --table-name TestTable ...
```

All newly created resources should be automatically tagged within seconds.


### To clean up afterwards:
Notice this operation will destroy the Lambda function and all other resources created by CDK.

```
$ cdk destroy
```

### Tag Verification (New Feature)
The solution now automatically verifies that tags were applied successfully after each tagging operation.

**What it does:**
- Immediately after tagging, queries the resource to confirm tags are present
- Logs verification results for debugging
- Warns if any tags failed to apply

**Example log output:**
```
Tagging resource: arn:aws:logs:us-west-2:123456789012:log-group:/aws/test
Using CloudWatch Logs API for log group: /aws/test
Successfully tagged log group: /aws/test
Verification - Current tags on /aws/test: {'TagName1': 'TagValue1', 'userId': 'alice'}
✅ Verification successful - All tags applied correctly
```

**If tags fail:**
```
⚠️ WARNING: Some tags were not applied successfully: ['roleId']
```

This helps quickly identify permission issues or API limitations.

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

**Tags not appearing on resources?**
1. Check Lambda execution logs for errors:
   ```bash
   aws logs tail /aws/lambda/resource-tagging-automation-function --follow
   ```
2. Look for verification messages - if you see "WARNING: Some tags were not applied", there may be permission issues
3. Verify the Lambda function has the required IAM permissions (check IAM role policies)

**Lambda function errors?**
- **`KeyError: 'aws_xxx'`** - The service handler function is missing (should be fixed in latest version)
- **`TypeError: 'NoneType' object is not subscriptable`** - API call failed or was a DryRun (should be fixed)
- **Permission errors** - Update the Lambda execution role with additional permissions

**CloudWatch Logs tags not showing?**
- Ensure you're using the latest version (uses `logs.tag_log_group` API instead of generic tagging API)
- Check that `logs:TagLogGroup` and `logs:ListTagsLogGroup` permissions are present

**EventBridge rules not triggering?**
1. Verify CloudTrail is enabled and logging API calls
2. Check EventBridge rule is enabled in the console
3. Ensure event pattern matches your resource creation events

**Deployment issues?**
- If deployment fails mid-way, manually clean up via CloudFormation console
- Navigate to CloudFormation → Select stack → Delete
- Ensure your IAM user has sufficient permissions to create Lambda, EventBridge, and IAM resources

**Need more help?**
- Review Lambda CloudWatch Logs for detailed execution traces
- Check the verification output to see which tags were applied successfully
- File an issue at: https://github.com/aws-samples/resource-tagging-automation/issues


### Security
See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.


### License
This library is licensed under the MIT-0 License. See the LICENSE file.
