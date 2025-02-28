# services/behavior_analysis_service.py
import json
import boto3
import cv2
from dotenv import load_dotenv
import cv2
import os
load_dotenv()

class BehaviorAnalyzer:
    def __init__(self):
        self.client = boto3.client('bedrock-runtime',aws_access_key_id=os.getenv('BEDROCK_AWS_ACCESS_KEY_ID'),
            aws_secret_access_key=os.getenv('BEDROCK_AWS_SECRET_ACCESS_KEY'),
            region_name=os.getenv('AWS_REGION', 'us-east-1'))
        
        self.model_id = "us.meta.llama3-2-90b-instruct-v1:0"
        
    def analyze(self, frame):
        """Analyze dog behavior and return structured response"""
        try:
            # Convert frame to PNG bytes
            _, buffer = cv2.imencode('.png', frame)
            image_bytes = buffer.tobytes()
            
            # Create structured prompt
            prompt = """Analyze this dog image and classify its posture/action strictly as one of: 
                      barking, eating, drinking, sleeping, standing, or other. 
                      Return JSON format: {"classification": "<label>", "reason": "<short reason in 100 chars>"}"""
            
            response = self.client.converse(
                modelId=self.model_id,
                messages=[{
                    "role": "user",
                    "content": [
                        {"image": {"format": "png", "source": {"bytes": image_bytes}}},
                        {"text": prompt}
                    ]
                }]
            )
            
            # Extract and validate response
            response_text = response['output']['message']['content'][0]['text']
            print(response_text)
            return self._parse_response(response_text)
            
        except Exception as e:
            return {"classification": "error", "reason": str(e)[:100]}

    def _parse_response(self, response_text):
        """Validate and parse the model response"""
        try:
            # Extract JSON from possible markdown
            #json_str = response_text.split("```json")[1].split("```")[0].strip()
            result = json.loads(response_text)
            self.latest_classification=result["classification"]
            
            # Validate structure
            valid_classes = ["barking", "eating", "drinking", "sleeping", "standing", "other"]
            if result.get("classification") in valid_classes:
                return result
            return {"classification": "other", "reason": "Invalid model response"}
        except:
            return {"classification": "other", "reason": "Response parsing failed"}
        


    def close(self):
        """Close AWS connection"""
        self.client.close()