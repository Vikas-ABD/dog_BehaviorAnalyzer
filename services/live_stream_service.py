from services.behaviour_analysis_service import BehaviorAnalyzer
from services.dog_detection_service import DogDetector
from services.aws_dynamodb_service import DynamoDBHandler
import queue
import threading
import cv2
import time
from datetime import datetime

class VideoProcessor:
    def __init__(self):
        self.frame_queue = queue.Queue(maxsize=2)
        self.running = False
        self.video_thread = None
        self.processing_thread = None
        
        # Initialize services
        self.detector = DogDetector()
        self.analyzer = BehaviorAnalyzer()
        self.db = DynamoDBHandler()
        
        # State tracking
        self.frame_count = 0
        self.last_processed = None
        self.latest_frame = None
        self.classification= None
        self.lock = threading.Lock()

    def start_stream(self, source):
        """Start video capture and processing threads"""
        if not self.running:
            self.running = True
            self.video_thread = threading.Thread(
                target=self._capture_frames, 
                args=(source,),
                daemon=True
            )
            self.processing_thread = threading.Thread(
                target=self._process_frames,
                daemon=True
            )
            self.video_thread.start()
            self.processing_thread.start()

    def stop_stream(self):
        """Stop all threads and clean up resources"""
        self.running = False
        if self.video_thread:
            self.video_thread.join(timeout=2)
        if self.processing_thread:
            self.processing_thread.join(timeout=2)
        self.frame_queue.queue.clear()
        self.detector.cleanup()
        self.analyzer.close()
        self.db.disconnect()

    def _capture_frames(self, source):
        """Video capture thread function"""
        cap = cv2.VideoCapture(source)
        while self.running and cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            
            # Convert to RGB for display
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            
            # Update latest frame for display
            with self.lock:
                self.latest_frame = frame_rgb
            
            # Add every 15th frame to processing queue
            if self.frame_count % 15 == 0:
                if self.frame_queue.full():
                    try:
                        self.frame_queue.get_nowait()
                    except queue.Empty:
                        pass
                self.frame_queue.put(frame_rgb)
            
            self.frame_count += 1
            time.sleep(1/30)  # ~30 FPS
        
        cap.release()
        self.running = False

    def _process_frames(self):
        """Frame processing thread function"""
        while self.running:
            try:
                frame = self.frame_queue.get(timeout=1)
                dog_exit=self.detector.detect(frame)
                if dog_exit:
                    result = self.analyzer.analyze(frame)
                    print(">>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>>")
                    self.classification=result["classification"]
                    self.db.store_result(frame,result)
                self.last_processed = datetime.now()
            except queue.Empty:
                continue
            time.sleep(2)  # Process every 5 seconds

    def get_latest_frame(self):
        """Get the latest frame for display"""
        with self.lock:
            return self.latest_frame,self.classification