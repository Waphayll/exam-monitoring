# app/cv_processor.py
import cv2
import numpy as np
from datetime import datetime
from typing import List, Dict, Tuple
import base64

class BehaviorDetector:
    """
    Wrapper for your PT algorithm.
    Replace the detect_behaviors() method with your actual model inference.
    """
    
    def __init__(self):
        # Load your PT model here
        # Example: self.model = torch.load('models/pt_model.pth')
        # Or: self.detector = YourCustomDetector()
        print("Initializing PT behavior detection model...")
        self.initialized = True
    
    def decode_image(self, base64_string: str) -> np.ndarray:
        """Convert base64 image to OpenCV format"""
        try:
            # Remove data:image/jpeg;base64, prefix if present
            if ',' in base64_string:
                base64_string = base64_string.split(',')[1]
            
            img_data = base64.b64decode(base64_string)
            nparr = np.frombuffer(img_data, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            return img
        except Exception as e:
            raise ValueError(f"Failed to decode image: {e}")
    
    def detect_behaviors(self, frame: np.ndarray) -> List[Dict]:
        """
        Main detection method - REPLACE THIS WITH YOUR PT ALGORITHM
        
        Args:
            frame: OpenCV image (BGR format)
        
        Returns:
            List of detected behaviors, each containing:
            - behavior_label: str (e.g., "phone_detected", "looking_away")
            - confidence: float (0-1)
            - severity: str ("low", "medium", "high", "critical")
            - bbox: dict with x, y, w, h (optional)
            - extra_data: dict (optional, any additional info)
        """
        
        # ============================================
        # REPLACE THIS SECTION WITH YOUR PT ALGORITHM
        # ============================================
        
        behaviors = []
        
        # Example 1: Face detection (placeholder for real behavior detection)
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        face_cascade = cv2.CascadeClassifier(cv2.data.haarcascades + 'haarcascade_frontalface_default.xml')
        faces = face_cascade.detectMultiScale(gray, 1.3, 5)
        
        if len(faces) == 0:
            behaviors.append({
                "behavior_label": "no_face_detected",
                "confidence": 0.95,
                "severity": "high",
                "bbox": None,
                "extra_data": {"face_count": 0}
            })
        elif len(faces) > 1:
            behaviors.append({
                "behavior_label": "multiple_faces",
                "confidence": 0.90,
                "severity": "critical",
                "bbox": None,
                "extra_data": {"face_count": len(faces)}
            })
        
        # Example 2: Motion detection (placeholder)
        # In real implementation, you'd compare with previous frame
        # and detect excessive movement, looking away, etc.
        
        # Example 3: Phone/object detection
        # Your actual PT model would detect phones, papers, etc.
        # behaviors.append({
        #     "behavior_label": "phone_detected",
        #     "confidence": 0.87,
        #     "severity": "critical",
        #     "bbox": {"x": 100, "y": 150, "w": 50, "h": 80},
        #     "extra_data": {"object_type": "smartphone"}
        # })
        
        # ============================================
        # YOUR PT ALGORITHM INTEGRATION GOES ABOVE
        # ============================================
        
        return behaviors
    
    def process_frame(self, base64_image: str, camera_id: int) -> Dict:
        """
        Process a single frame and return detected behaviors
        """
        try:
            # Decode image
            frame = self.decode_image(base64_image)
            
            if frame is None:
                return {
                    "success": False,
                    "error": "Failed to decode image"
                }
            
            # Run detection
            behaviors = self.detect_behaviors(frame)
            
            # Add timestamp
            timestamp = datetime.now().isoformat()
            
            return {
                "success": True,
                "camera_id": camera_id,
                "timestamp": timestamp,
                "frame_shape": frame.shape,
                "behaviors": behaviors,
                "behavior_count": len(behaviors)
            }
            
        except Exception as e:
            return {
                "success": False,
                "error": str(e)
            }

# Global detector instance
detector = BehaviorDetector()
