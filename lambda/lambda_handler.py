# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
# SPDX-License-Identifier: MIT-0

import boto3
import os
import json

def aws_ec2(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    ec2ArnTemplate = 'arn:aws:ec2:@region@:@account@:instance/@instanceId@'
    volumeArnTemplate = 'arn:aws:ec2:@region@:@account@:volume/@volumeId@'
    snapshotArnTemplate = 'arn:aws:ec2:@region@:@account@:snapshot/@snapshotId@'
    imageArnTemplate = 'arn:aws:ec2:@region@:@account@:image/@imageId@'
    ec2_resource = boto3.resource('ec2')
    if event['detail']['eventName'] == 'RunInstances':
        print("tagging for new EC2...")
        for item in event['detail']['responseElements']['instancesSet']['items']:
            _instanceId = item['instanceId']
            arnList.append(ec2ArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@instanceId@', _instanceId))

            _instance = ec2_resource.Instance(_instanceId)
            for volume in _instance.volumes.all():
                arnList.append(volumeArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@volumeId@', volume.id))

    elif event['detail']['eventName'] == 'CreateVolume':
        print("tagging for new EBS...")
        _volumeId = event['detail']['responseElements']['volumeId']
        arnList.append(volumeArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@volumeId@', _volumeId))
        
    elif event['detail']['eventName'] == 'CreateInternetGateway':
        print("tagging for new IGW...")
        
    elif event['detail']['eventName'] == 'CreateNatGateway':
        print("tagging for new Nat Gateway...")
        
    elif event['detail']['eventName'] == 'AllocateAddress':
        print("tagging for new EIP...")
        arnList.append(event['detail']['responseElements']['allocationId'])
        
    elif event['detail']['eventName'] == 'CreateVpcEndpoint':
        print("tagging for new VPC Endpoint...")
        
    elif event['detail']['eventName'] == 'CreateTransitGateway':
        print("tagging for new Transit Gateway...")
    
    elif event['detail']['eventName'] == 'CreateSnapshot':
        print("tagging for new EBS Snapshot...")
        _snapshotId = event['detail']['responseElements']['snapshotId']
        arnList.append(snapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotId@', _snapshotId))
    
    elif event['detail']['eventName'] == 'CopySnapshot':
        print("tagging for copied EBS Snapshot...")
        _snapshotId = event['detail']['responseElements']['snapshotId']
        arnList.append(snapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotId@', _snapshotId))
    
    elif event['detail']['eventName'] == 'CreateImage':
        print("tagging for new EC2 AMI...")
        _imageId = event['detail']['responseElements']['imageId']
        arnList.append(imageArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@imageId@', _imageId))
        
        # Also tag snapshots created as part of the AMI
        if 'blockDeviceMapping' in event['detail']['responseElements']:
            for device in event['detail']['responseElements']['blockDeviceMapping']:
                if 'ebs' in device and 'snapshotId' in device['ebs']:
                    _snapshotId = device['ebs']['snapshotId']
                    arnList.append(snapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotId@', _snapshotId))

    return arnList
    
def aws_elasticloadbalancing(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateLoadBalancer':
        print("tagging for new LoadBalancer...")
        lbs = event['detail']['responseElements']
        for lb in lbs['loadBalancers']:
            arnList.append(lb['loadBalancerArn'])
        return arnList

def aws_rds(event):
    arnList = []
    # Check if this is a DocumentDB event (DocumentDB uses the RDS API)
    isDocumentDB = False
    if 'engine' in event['detail']['responseElements'] and event['detail']['responseElements']['engine'] == 'docdb':
        isDocumentDB = True
        print("Detected DocumentDB event through RDS API")
    
    if event['detail']['eventName'] == 'CreateDBInstance':
        if isDocumentDB:
            print("tagging for new DocumentDB instance...")
            # Get the instance identifier
            db_instance_id = event['detail']['responseElements']['dBInstanceIdentifier']
            
            # Wait for the instance to be available
            try:
                waiter = boto3.client('docdb').get_waiter('db_instance_available')
                waiter.wait(
                    DBInstanceIdentifier=db_instance_id,
                    WaiterConfig={
                        'Delay': 30,
                        'MaxAttempts': 20
                    }
                )
            except Exception as e:
                print(f"Warning: Waiter for DocumentDB instance failed: {e}")
                # Continue with tagging even if waiter fails
                
            arnList.append(event['detail']['responseElements']['dBInstanceArn'])
        else:
            print("tagging for new RDS...")
            #db_instance_id = event['detail']['requestParameters']['dBInstanceIdentifier']
            #waiter = boto3.client('rds').get_waiter('db_instance_available')
            #waiter.wait(
            #    DBInstanceIdentifier = db_instance_id
            #)
            arnList.append(event['detail']['responseElements']['dBInstanceArn'])
        return arnList
    elif event['detail']['eventName'] == 'CreateDBCluster':
        if isDocumentDB:
            print("tagging for new DocumentDB cluster...")
        else:
            print("tagging for new Aurora cluster...")
        arnList.append(event['detail']['responseElements']['dBClusterArn'])
        return arnList
    elif event['detail']['eventName'] == 'CreateDBSnapshot':
        print("tagging for new RDS snapshot...")
        arnList.append(event['detail']['responseElements']['dBSnapshotArn'])
        return arnList
    elif event['detail']['eventName'] == 'CopyDBSnapshot':
        print("tagging for copied RDS snapshot...")
        arnList.append(event['detail']['responseElements']['dBSnapshotArn'])
        return arnList
    elif event['detail']['eventName'] == 'CreateDBClusterSnapshot':
        if isDocumentDB:
            print("tagging for new DocumentDB cluster snapshot...")
        else:
            print("tagging for new RDS cluster snapshot...")
        
        # Use proper key name as seen in the event
        arnList.append(event['detail']['responseElements']['dBClusterSnapshotArn'])
        return arnList
    elif event['detail']['eventName'] == 'CopyDBClusterSnapshot':
        if isDocumentDB:
            print("tagging for copied DocumentDB cluster snapshot...")
        else:
            print("tagging for copied RDS cluster snapshot...")
        arnList.append(event['detail']['responseElements']['dBClusterSnapshotArn'])
        return arnList
    
    return arnList  # Return empty list if no matching event name

# This function handles direct DocumentDB events if AWS changes their API in the future
# Currently, DocumentDB events are routed through the RDS API
def aws_docdb(event):
    print("Direct DocumentDB event received")
    arnList = []
    _account = event['account']
    _region = event['region']
    
    if event['detail']['eventName'] == 'CreateDBInstance':
        print("tagging for new DocumentDB instance (direct API)...")
        db_instance_id = event['detail']['responseElements']['dBInstanceIdentifier']
        
        # Wait for the instance to be available
        try:
            waiter = boto3.client('docdb').get_waiter('db_instance_available')
            waiter.wait(
                DBInstanceIdentifier=db_instance_id,
                WaiterConfig={
                    'Delay': 30,
                    'MaxAttempts': 20
                }
            )
        except Exception as e:
            print(f"Warning: Waiter for DocumentDB instance failed: {e}")
            # Continue with tagging even if waiter fails
            
        # If ARN is directly available in the response
        if 'dBInstanceArn' in event['detail']['responseElements']:
            arnList.append(event['detail']['responseElements']['dBInstanceArn'])
        else:
            # Construct the ARN if not available
            docdbInstanceArnTemplate = 'arn:aws:rds:@region@:@account@:db:@instanceId@'
            arnList.append(docdbInstanceArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@instanceId@', db_instance_id))
        return arnList
    
    elif event['detail']['eventName'] == 'CreateDBCluster':
        print("tagging for new DocumentDB cluster (direct API)...")
        if 'dBClusterArn' in event['detail']['responseElements']:
            arnList.append(event['detail']['responseElements']['dBClusterArn'])
        else:
            # Construct the ARN if not available
            cluster_id = event['detail']['responseElements']['dBClusterIdentifier']
            docdbClusterArnTemplate = 'arn:aws:rds:@region@:@account@:cluster:@clusterId@'
            arnList.append(docdbClusterArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@clusterId@', cluster_id))
        return arnList
        
    elif event['detail']['eventName'] == 'CreateDBClusterSnapshot':
        print("tagging for new DocumentDB cluster snapshot (direct API)...")
        arnList.append(event['detail']['responseElements']['dBClusterSnapshotArn'])
        return arnList
        
    elif event['detail']['eventName'] == 'CopyDBClusterSnapshot':
        print("tagging for copied DocumentDB cluster snapshot (direct API)...")
        arnList.append(event['detail']['responseElements']['dBClusterSnapshotArn'])
        return arnList
        
    return arnList

def aws_s3(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateBucket':
        print("tagging for new S3...")
        _bkcuetName = event['detail']['requestParameters']['bucketName']
        arnList.append('arn:aws:s3:::' + _bkcuetName)
        return arnList
        
def aws_lambda(event):
    arnList = []
    _exist1 = event['detail']['responseElements']
    _exist2 = event['detail']['eventName'] == 'CreateFunction20150331'
    if  _exist1!= None and _exist2:
        function_name = event['detail']['responseElements']['functionName']
        print('Functin name is :', function_name)
        arnList.append(event['detail']['responseElements']['functionArn'])
        return arnList

def aws_dynamodb(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateTable':
        table_name = event['detail']['responseElements']['tableDescription']['tableName']
        waiter = boto3.client('dynamodb').get_waiter('table_exists')
        waiter.wait(
            TableName=table_name,
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )
        arnList.append(event['detail']['responseElements']['tableDescription']['tableArn'])
        return arnList
        
def aws_kms(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateKey':
        arnList.append(event['detail']['responseElements']['keyMetadata']['arn'])
        return arnList

def aws_sns(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    snsArnTemplate = 'arn:aws:sns:@region@:@account@:@topicName@'
    if event['detail']['eventName'] == 'CreateTopic':
        print("tagging for new SNS...")
        _topicName = event['detail']['requestParameters']['name']
        arnList.append(snsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@topicName@', _topicName))
        return arnList
        
def aws_sqs(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    sqsArnTemplate = 'arn:aws:sqs:@region@:@account@:@queueName@'
    if event['detail']['eventName'] == 'CreateQueue':
        print("tagging for new SQS...")
        _queueName = event['detail']['requestParameters']['queueName']
        arnList.append(sqsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@queueName@', _queueName))
        return arnList
        
def aws_elasticfilesystem(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    efsArnTemplate = 'arn:aws:elasticfilesystem:@region@:@account@:file-system/@fileSystemId@'
    if event['detail']['eventName'] == 'CreateMountTarget':
        print("tagging for new efs...")
        _efsId = event['detail']['responseElements']['fileSystemId']
        arnList.append(efsArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@fileSystemId@', _efsId))
        return arnList
        
def aws_es(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateDomain':
        print("tagging for new open search...")
        arnList.append(event['detail']['responseElements']['domainStatus']['aRN'])
        return arnList

def aws_emr(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    
    # EMR on EC2
    if event['detail']['eventName'] == 'RunJobFlow':
        print("tagging for new EMR on EC2 cluster...")
        cluster_id = event['detail']['responseElements']['jobFlowId']
        emr_arn = f'arn:aws:elasticmapreduce:{_region}:{_account}:cluster/{cluster_id}'
        arnList.append(emr_arn)
        
    return arnList

def aws_emr_serverless(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    
    if event['detail']['eventName'] == 'CreateApplication':
        print("tagging for new EMR Serverless application...")
        app_id = event['detail']['responseElements']['applicationId']
        app_arn = f'arn:aws:emr-serverless:{_region}:{_account}:/applications/{app_id}'
        arnList.append(app_arn)
        
    return arnList

def aws_emr_containers(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    
    if event['detail']['eventName'] == 'CreateVirtualCluster':
        print("tagging for new EMR on EKS virtual cluster...")
        vc_id = event['detail']['responseElements']['id']
        vc_arn = f'arn:aws:emr-containers:{_region}:{_account}:/virtualclusters/{vc_id}'
        arnList.append(vc_arn)
        
    return arnList

def aws_batch(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    
    # ARN templates for Batch resources
    jobQueueArnTemplate = f'arn:aws:batch:{_region}:{_account}:job-queue/'
    computeEnvArnTemplate = f'arn:aws:batch:{_region}:{_account}:compute-environment/'
    jobDefArnTemplate = f'arn:aws:batch:{_region}:{_account}:job-definition/'
    jobArnTemplate = f'arn:aws:batch:{_region}:{_account}:job/'
    
    if event['detail']['eventName'] == 'CreateJobQueue':
        print("tagging for new Batch job queue...")
        print(f"Full CreateJobQueue event: {event}")
        if 'jobQueueArn' in event['detail']['responseElements']:
            queue_arn = event['detail']['responseElements']['jobQueueArn']
            print(f"Adding job queue ARN to tag list: {queue_arn}")
            arnList.append(queue_arn)
        else:
            # Construct ARN if not available in response
            job_queue_name = event['detail']['responseElements']['jobQueueName']
            queue_arn = jobQueueArnTemplate + job_queue_name
            print(f"Adding constructed job queue ARN to tag list: {queue_arn}")
            arnList.append(queue_arn)
            
    elif event['detail']['eventName'] == 'CreateComputeEnvironment':
        print("tagging for new Batch compute environment...")
        print(f"Full CreateComputeEnvironment event: {event}")
        if 'computeEnvironmentArn' in event['detail']['responseElements']:
            env_arn = event['detail']['responseElements']['computeEnvironmentArn']
            print(f"Adding compute environment ARN to tag list: {env_arn}")
            arnList.append(env_arn)
        else:
            # Construct ARN if not available in response
            compute_env_name = event['detail']['responseElements']['computeEnvironmentName']
            env_arn = computeEnvArnTemplate + compute_env_name
            print(f"Adding constructed compute environment ARN to tag list: {env_arn}")
            arnList.append(env_arn)
            
            # If this is an EC2 compute environment, we might need to tag the Auto Scaling Group too
            # This requires additional API calls to find the ASG
            if 'computeResources' in event['detail']['requestParameters'] and event['detail']['requestParameters']['computeResources'].get('type') == 'EC2':
                try:
                    # Wait a bit for the compute environment to be created
                    import time
                    time.sleep(5)
                    
                    # Get the compute environment details to find the ASG
                    batch_client = boto3.client('batch')
                    response = batch_client.describe_compute_environments(
                        computeEnvironments=[compute_env_name]
                    )
                    
                    if response['computeEnvironments'] and 'computeResources' in response['computeEnvironments'][0]:
                        compute_resources = response['computeEnvironments'][0]['computeResources']
                        if 'autoScalingGroupArn' in compute_resources:
                            asg_arn = compute_resources['autoScalingGroupArn']
                            print(f"Also tagging Auto Scaling Group for Batch compute environment: {asg_arn}")
                            arnList.append(asg_arn)
                except Exception as e:
                    print(f"Warning: Failed to get Auto Scaling Group for Batch compute environment: {e}")
            
    elif event['detail']['eventName'] == 'RegisterJobDefinition':
        print("tagging for new Batch job definition...")
        print(f"Full RegisterJobDefinition event: {event}")
        if 'jobDefinitionArn' in event['detail']['responseElements']:
            job_def_arn = event['detail']['responseElements']['jobDefinitionArn']
            print(f"Adding job definition ARN to tag list: {job_def_arn}")
            arnList.append(job_def_arn)
        else:
            # Construct ARN if not available in response
            job_def_name = event['detail']['responseElements']['jobDefinitionName']
            job_def_revision = event['detail']['responseElements']['revision']
            job_def_arn = f"{jobDefArnTemplate}{job_def_name}:{job_def_revision}"
            print(f"Adding constructed job definition ARN to tag list: {job_def_arn}")
            arnList.append(job_def_arn)
            
    elif event['detail']['eventName'] == 'SubmitJob':
        print("tagging for new Batch job...")
        print(f"Full SubmitJob event: {event}")
        
        # Tag the job itself
        if 'jobArn' in event['detail']['responseElements']:
            job_arn = event['detail']['responseElements']['jobArn']
            print(f"Adding job ARN to tag list: {job_arn}")
            arnList.append(job_arn)
        elif 'jobId' in event['detail']['responseElements'] and 'jobName' in event['detail']['responseElements']:
            # Construct ARN if not available in response
            job_id = event['detail']['responseElements']['jobId']
            job_arn = f"{jobArnTemplate}{job_id}"
            print(f"Adding constructed job ARN to tag list: {job_arn}")
            arnList.append(job_arn)
            
        # We might also want to tag the underlying resources (ECS tasks) but this requires
        # additional API calls and the tasks might not be created yet
        try:
            # Get job details to find the associated ECS task
            job_id = event['detail']['responseElements']['jobId']
            batch_client = boto3.client('batch')
            
            # Wait a bit for the job to start
            import time
            time.sleep(5)
            
            job_response = batch_client.describe_jobs(jobs=[job_id])
            print(f"Job response: {job_response}")
            
            if job_response['jobs'] and 'container' in job_response['jobs'][0]:
                container = job_response['jobs'][0]['container']
                if 'taskArn' in container:
                    task_arn = container['taskArn']
                    print(f"Also tagging ECS task for Batch job: {task_arn}")
                    arnList.append(task_arn)
        except Exception as e:
            print(f"Warning: Failed to get ECS task for Batch job: {e}")
    
    print(f"Batch ARNs to tag: {arnList}")
    return arnList

def aws_kafka(event):
    arnList = []
    if event['detail']['eventName'] == 'CreateClusterV2':
        print("tagging for new MSK cluster...")
        arnList.append(event['detail']['responseElements']['clusterArn'])
        return arnList
    return arnList

def aws_ecs(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    
    # ARN templates for ECS resources
    taskArnTemplate = f'arn:aws:ecs:{_region}:{_account}:task/'
    serviceArnTemplate = f'arn:aws:ecs:{_region}:{_account}:service/'
    
    if event['detail']['eventName'] == 'CreateCluster':
        print("tagging for new ECS cluster...")
        arnList.append(event['detail']['responseElements']['cluster']['clusterArn'])
        
    elif event['detail']['eventName'] == 'RunTask':
        print("tagging for new ECS task (including Fargate tasks)...")
        print(f"Full RunTask event: {event}")
        
        # Check if this is a Fargate task
        is_fargate = False
        if 'launchType' in event['detail']['requestParameters'] and event['detail']['requestParameters']['launchType'] == 'FARGATE':
            is_fargate = True
            print("Detected explicit Fargate task in requestParameters")
        elif 'capacityProviderStrategy' in event['detail']['requestParameters']:
            for provider in event['detail']['requestParameters']['capacityProviderStrategy']:
                if provider.get('capacityProvider') == 'FARGATE':
                    is_fargate = True
                    print("Detected Fargate task via capacityProviderStrategy")
                    break
        
        # Get task ARNs from the response
        if 'tasks' in event['detail']['responseElements']:
            print(f"Found {len(event['detail']['responseElements']['tasks'])} tasks in response")
            for task in event['detail']['responseElements']['tasks']:
                if 'taskArn' in task:
                    task_arn = task['taskArn']
                    print(f"Adding task ARN to tag list: {task_arn}")
                    arnList.append(task_arn)
                    
                    # Check if this task has containers with their own ARNs
                    if 'containers' in task:
                        for container in task['containers']:
                            if 'containerArn' in container:
                                container_arn = container['containerArn']
                                print(f"Adding container ARN to tag list: {container_arn}")
                                arnList.append(container_arn)
                    
                    # For Fargate tasks, we might want to tag additional resources
                    if is_fargate or ('launchType' in task and task['launchType'] == 'FARGATE'):
                        print(f"Confirmed Fargate task: {task_arn}")
                        # ENIs and other resources are created asynchronously, so we might need to wait
                        # This would require a more complex solution with Step Functions or a separate Lambda
                        pass
                else:
                    print("Task missing taskArn field")
        else:
            print("No tasks found in responseElements")
            print(f"ResponseElements keys: {event['detail']['responseElements'].keys()}")
        
    elif event['detail']['eventName'] == 'CreateService':
        print("tagging for new ECS service...")
        if 'service' in event['detail']['responseElements'] and 'serviceArn' in event['detail']['responseElements']['service']:
            arnList.append(event['detail']['responseElements']['service']['serviceArn'])
            
            # Check if this is a Fargate service
            if 'launchType' in event['detail']['responseElements']['service'] and event['detail']['responseElements']['service']['launchType'] == 'FARGATE':
                print("Detected Fargate service")
                # For Fargate services, tasks will be created asynchronously
                # We would need a more complex solution to tag those
        
    elif event['detail']['eventName'] == 'StartTask':
        print("tagging for started ECS task...")
        if 'tasks' in event['detail']['responseElements']:
            for task in event['detail']['responseElements']['tasks']:
                if 'taskArn' in task:
                    task_arn = task['taskArn']
                    print(f"Adding task ARN to tag list: {task_arn}")
                    arnList.append(task_arn)
    
    print(f"ECS ARNs to tag: {arnList}")
    return arnList

def aws_elasticache(event):
    arnList = []
    _account = event['account']
    _region = event['region']
    ecArnTemplate = 'arn:aws:elasticache:@region@:@account@:cluster:@ecId@'
    snapshotArnTemplate = 'arn:aws:elasticache:@region@:@account@:snapshot:@snapshotName@'

    if event['detail']['eventName'] == 'CreateReplicationGroup' or event['detail']['eventName'] == 'ModifyReplicationGroupShardConfiguration':
        print("tagging for new ElastiCache cluster...")
        _replicationGroupId = event['detail']['requestParameters']['replicationGroupId']
        waiter = boto3.client('elasticache').get_waiter('replication_group_available')
        waiter.wait(
            ReplicationGroupId = _replicationGroupId,
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )
        _clusters = event['detail']['responseElements']['memberClusters']
        for _ec in _clusters:
            arnList.append(ecArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@ecId@', _ec))

    elif event['detail']['eventName'] == 'CreateCacheCluster':
        print("tagging for new ElastiCache node...")
        _cacheClusterId = event['detail']['responseElements']['cacheClusterId']
        waiter = boto3.client('elasticache').get_waiter('cache_cluster_available')
        waiter.wait(
            CacheClusterId = _cacheClusterId,
            WaiterConfig={
                'Delay': 123,
                'MaxAttempts': 123
            }
        )
        arnList.append(event['detail']['responseElements']['aRN'])
        
    elif event['detail']['eventName'] == 'CreateSnapshot':
        print("tagging for new ElastiCache snapshot...")
        if 'snapshotName' in event['detail']['requestParameters']:
            _snapshotName = event['detail']['requestParameters']['snapshotName']
            arnList.append(snapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotName@', _snapshotName))
        
    elif event['detail']['eventName'] == 'CopySnapshot':
        print("tagging for copied ElastiCache snapshot...")
        if 'targetSnapshotName' in event['detail']['requestParameters']:
            _snapshotName = event['detail']['requestParameters']['targetSnapshotName']
            arnList.append(snapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotName@', _snapshotName))
            
    # For Redis OSS and Valkey backup operations
    elif event['detail']['eventName'] == 'CreateServerlessCache':
        print("tagging for new Serverless ElastiCache (Redis OSS/Valkey)...")
        if 'serverlessCacheName' in event['detail']['responseElements']:
            _cacheName = event['detail']['responseElements']['serverlessCacheName']
            # Using the standard ARN format for serverless cache
            serverlessCacheArnTemplate = 'arn:aws:elasticache:@region@:@account@:serverlesscache:@cacheName@'
            arnList.append(serverlessCacheArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@cacheName@', _cacheName))
    
    elif event['detail']['eventName'] == 'CreateSnapshot' and 'serverlessCacheName' in event['detail']['requestParameters']:
        print("tagging for new ElastiCache Serverless snapshot...")
        if 'snapshotName' in event['detail']['requestParameters']:
            _snapshotName = event['detail']['requestParameters']['snapshotName']
            # Using a specific ARN format for serverless cache snapshots
            serverlessSnapshotArnTemplate = 'arn:aws:elasticache:@region@:@account@:serverlesssnapshot:@snapshotName@'
            arnList.append(serverlessSnapshotArnTemplate.replace('@region@', _region).replace('@account@', _account).replace('@snapshotName@', _snapshotName))

    return arnList
    
def get_identity(event):
    print("getting user Identity...")
    _userId = event['detail']['userIdentity']['arn'].split('/')[-1]
    
    if event['detail']['userIdentity']['type'] == 'AssumedRole':
        _roleId = event['detail']['userIdentity']['arn'].split('/')[-2]
        return _userId, _roleId
    return _userId

def main(event, context):
    print(f"input event is: {event}")
    print("new source is ", event['source'])
    _method = event['source'].replace('.', "_").replace('-', "_")

    # Special handling for Batch events that come through ECS
    if event['source'] == 'aws.ecs' and 'userIdentity' in event['detail'] and 'invokedBy' in event['detail']['userIdentity'] and event['detail']['userIdentity']['invokedBy'] == 'batch.amazonaws.com':
        print("Detected Batch event through ECS API")
        # Process both as ECS and Batch
        ecsARNs = aws_ecs(event)
        batchARNs = []
        
        # Extract Batch information from ECS event
        if 'tags' in event['detail']['requestParameters']:
            batch_tags = {tag['key']: tag['value'] for tag in event['detail']['requestParameters']['tags'] if tag['key'].startswith('aws:batch:')}
            if batch_tags:
                print(f"Found Batch tags in ECS event: {batch_tags}")
                
                # Try to construct Batch ARNs from tags
                if 'aws:batch:job-queue' in batch_tags:
                    queue_name = batch_tags['aws:batch:job-queue']
                    queue_arn = f"arn:aws:batch:{event['region']}:{event['account']}:job-queue/{queue_name}"
                    print(f"Adding job queue ARN to tag list: {queue_arn}")
                    batchARNs.append(queue_arn)
                
                if 'aws:batch:compute-environment' in batch_tags:
                    env_name = batch_tags['aws:batch:compute-environment']
                    env_arn = f"arn:aws:batch:{event['region']}:{event['account']}:compute-environment/{env_name}"
                    print(f"Adding compute environment ARN to tag list: {env_arn}")
                    batchARNs.append(env_arn)
                
                if 'aws:batch:job-definition' in batch_tags:
                    job_def = batch_tags['aws:batch:job-definition']
                    job_def_arn = f"arn:aws:batch:{event['region']}:{event['account']}:job-definition/{job_def}"
                    print(f"Adding job definition ARN to tag list: {job_def_arn}")
                    batchARNs.append(job_def_arn)
        
        resARNs = ecsARNs + batchARNs
    else:
        # Normal processing
        resARNs = globals()[_method](event)
    
    print("resource arn is: ", resARNs)

    if not resARNs:
        print("No resources to tag, exiting")
        return {
            'statusCode': 200,
            'body': json.dumps('No resources to tag for ' + event['source'])
        }

    _res_tags = json.loads(os.environ['tags'])
    _identity_recording = os.environ['identityRecording']

    if _identity_recording == 'true':
        if event['detail']['userIdentity']['type'] == 'AssumedRole':
            _userId, _roleId = get_identity(event)
            _res_tags['roleId'] = _roleId
        else:
            _userId = get_identity(event)
        
        _res_tags['userId'] = _userId
    
    print(f"Applying tags: {_res_tags}")
    
    # Try to tag each resource individually to avoid failing the entire batch
    for arn in resARNs:
        try:
            print(f"Tagging resource: {arn}")
            boto3.client('resourcegroupstaggingapi').tag_resources(
                ResourceARNList=[arn],
                Tags=_res_tags
            )
            print(f"Successfully tagged: {arn}")
        except Exception as e:
            print(f"Error tagging resource {arn}: {e}")
    
    return {
        'statusCode': 200,
        'body': json.dumps('Finished tagging with ' + event['source'])
    }
