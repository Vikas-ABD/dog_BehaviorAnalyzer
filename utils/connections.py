import boto3
from botocore.config import Config

class Connections:
    lambda_function_name = "your_lambda_function_name_here"
    
    @classmethod
    def lambda_client(cls):
        if not cls._lambda_client:
            cls._lambda_client = boto3.client(
                'lambda',
                config=Config(read_timeout=300, connect_timeout=300)
            )
        return cls._lambda_client