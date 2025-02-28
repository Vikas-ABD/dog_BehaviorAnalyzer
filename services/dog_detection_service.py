from ultralytics import YOLO
import torch

class DogDetector:
    def __init__(self):
        """Initialize YOLOv12 model for dog detection."""
        self.model = YOLO('models/yolo12s.pt')  # Load YOLOv12 model

    def detect(self, frame):
        """
        Detect dogs in the given frame using YOLOv12.
        
        Args:
            frame (numpy.ndarray): Input frame (BGR format).
        
        Returns:
            bool: True if a dog is detected, False otherwise.
        """
        results = self.model.predict(frame, device="cpu", verbose=False, conf=0.33)
        class_ids = results[0].boxes.cls.cpu().numpy()  # Extract class IDs
        return any(id == 16 for id in class_ids)  # COCO class 16 is 'dog'

    def cleanup(self):
        """Clean up resources (e.g., release model from memory)."""
        #del self.model
        if torch.cuda.is_available():
            torch.cuda.empty_cache()