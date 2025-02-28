# services/aws_dynamodb_service.py
import os
import boto3
import uuid
from datetime import datetime
from botocore.exceptions import ClientError
from dotenv import load_dotenv
import cv2

load_dotenv()

class DynamoDBHandler:
    def __init__(self):
        self.s3 = boto3.client(
            's3',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        self.dynamodb = boto3.resource(
            'dynamodb',
            aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1')
        )
        
        self.s3_bucket_name = "dog-analysis-frames-v1"
        self.table_name = "DogBehaviorResults"
        
        # Initialize resources
        self._initialize_s3_bucket()
        self.table = self._initialize_dynamodb_table()

    def _initialize_s3_bucket(self):
        """Create S3 bucket if it doesn't exist"""
        try:
            self.s3.head_bucket(Bucket=self.s3_bucket_name)
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                region = os.getenv('AWS_REGION', 'us-east-1')
                
                # If the region is us-east-1, do not include CreateBucketConfiguration
                if region == 'us-east-1':
                    self.s3.create_bucket(Bucket=self.s3_bucket_name)
                else:
                    self.s3.create_bucket(
                        Bucket=self.s3_bucket_name,
                        CreateBucketConfiguration={'LocationConstraint': region}
                    )


    def _initialize_dynamodb_table(self):
        """Create DynamoDB table if it doesn't exist"""
        try:
            table = self.dynamodb.Table(self.table_name)
            table.load()
            return table
        except ClientError as e:
            if e.response['Error']['Code'] == 'ResourceNotFoundException':
                return self._create_dynamodb_table()
            raise

    def _create_dynamodb_table(self):
        """Create DynamoDB table with proper schema"""
        table = self.dynamodb.create_table(
            TableName=self.table_name,
            KeySchema=[
                {'AttributeName': 'frame_id', 'KeyType': 'HASH'}
            ],
            AttributeDefinitions=[
                {'AttributeName': 'frame_id', 'AttributeType': 'S'}
            ],
            ProvisionedThroughput={
                'ReadCapacityUnits': 5,
                'WriteCapacityUnits': 5
            }
        )
        table.wait_until_exists()
        return table

    def store_result(self, frame, result):
        """Store frame in S3 and result in DynamoDB"""
        try:
            # Convert BGR to RGB before encoding
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            # Generate unique S3 object name
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            s3_key = f"frames/{timestamp}-{uuid.uuid4().hex}.png"
            
            # Upload frame to S3
            self.s3.put_object(
                Bucket=self.s3_bucket_name,
                Key=s3_key,
                Body=cv2.imencode('.png', frame_rgb)[1].tobytes(),
                ContentType='image/png'
            )
            
            # Create DynamoDB item
            item = {
                'frame_id': str(uuid.uuid4()),
                's3_url': f"s3://{self.s3_bucket_name}/{s3_key}",
                'classification': result['classification'],
                'reason': result['reason'],
                'timestamp': datetime.now().isoformat(),
                'metadata': {
                    'source': 'live-stream',
                    'processing_time': datetime.now().isoformat()
                }
            }
            
            self.table.put_item(Item=item)
            return True
        except Exception as e:
            self.log_error({
                'error_type': 'StorageError',
                'message': str(e)
            })
            return False

    def log_error(self, error_data):
        """Log errors to DynamoDB"""
        try:
            self.table.put_item(
                Item={
                    'frame_id': str(uuid.uuid4()),
                    'error_type': error_data['error_type'],
                    'message': error_data['message'][:500],
                    'timestamp': datetime.now().isoformat(),
                    'metadata': {'type': 'error'}
                }
            )
        except Exception as e:
            print(f"Critical error logging failure: {str(e)}")

    def disconnect(self):
        """Clean up resources"""
        pass