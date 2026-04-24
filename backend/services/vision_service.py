import os

try:
    from ultralytics import YOLO
    HAS_YOLO = True
except ImportError:
    HAS_YOLO = False

class VisionService:
    def __init__(self, model_weight_path="models/yolov8.onnx"):
        """
        Initializes the YOLOv8 model using the ONNX format. 
        Falls back to Mock mode if the ultralytics library or weights are missing.
        """
        self.model_weight_path = model_weight_path
        
        if HAS_YOLO and os.path.exists(model_weight_path):
            # Ultralytics natively supports loading .onnx files
            self.model = YOLO(model_weight_path, task='detect') 
            self.use_mock = False
            print(f"✅ Loaded YOLOv8 ONNX model from {model_weight_path}")
        else:
            print(f"⚠️ YOLO ONNX weights ({model_weight_path}) or ultralytics package not found. Running Vision in MOCK mode.")
            self.use_mock = True

    def analyze_image(self, image_path: str) -> dict:
        """
        Processes an image and returns all defects for the Context Packet.
        """
        # --- MOCK MODE FOR HACKATHON DEV ---
        if self.use_mock:
            return {
                "primary_label": "crack",
                "max_confidence": 0.88,
                "total_defects_found": 4,
                "vision_note": "Visual defects confirmed: 4x crack (MOCK DATA)."
            }

        # --- REAL YOLOv8 ONNX INFERENCE ---
        results = self.model(image_path)
        boxes = results[0].boxes
        
        # Check if nothing was detected
        if len(boxes) == 0:
            return {
                "primary_label": "Clear Road",
                "max_confidence": 1.0,
                "total_defects_found": 0,
                "vision_note": "No infrastructure defects detected in frame."
            }

        # Count all detections and find the highest confidence
        from collections import Counter
        label_counts = Counter()
        max_conf = 0.0
        primary_label = ""
        all_detections = []

        for box in boxes:
            label_name = self.model.names[int(box.cls)]
            conf = float(box.conf)
            
            label_counts[label_name] += 1
            all_detections.append({"label": label_name, "confidence": round(conf, 2)})
            
            # Track the highest confidence label to use as the primary category
            if conf > max_conf:
                max_conf = conf
                primary_label = label_name

        # Create a smart summary string for the Agent (e.g., "4x crack, 1x pothole")
        summary_parts = [f"{count}x {label}" for label, count in label_counts.items()]
        summary_str = ", ".join(summary_parts)

        return {
            "primary_label": primary_label,
            "max_confidence": round(max_conf, 2),
            "total_defects_found": len(boxes),
            "raw_detections": all_detections, # Optional: Full list if you need exact numbers later
            "vision_note": f"Visual defects confirmed: {summary_str}. Highest confidence: {round(max_conf, 2)}"
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    vision = VisionService()
    # Pass a dummy path; it will return the mock data if weights aren't loaded
    print(vision.analyze_image(r"C:\Users\njxnj\Downloads\Telegram Desktop\test_road.jpg"))