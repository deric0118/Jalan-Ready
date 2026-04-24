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
        Processes an image and returns the highest confidence defect for the Context Packet.
        """
        # --- MOCK MODE FOR HACKATHON DEV ---
        if self.use_mock:
            return {
                "yolo_label": "Alligator Cracking",
                "confidence": 0.88,
                "vision_note": "Severe base layer failure detected (MOCK DATA)."
            }

        # --- REAL YOLOv8 ONNX INFERENCE ---
        results = self.model(image_path)
        
        # Check if nothing was detected
        if len(results[0].boxes) == 0:
            return {
                "yolo_label": "Clear Road",
                "confidence": 1.0,
                "vision_note": "No infrastructure defects detected in frame."
            }

        # Extract the highest confidence detection
        # Sort boxes by confidence to ensure we get the primary defect
        boxes = sorted(results[0].boxes, key=lambda x: x.conf, reverse=True)
        top_box = boxes[0]
        
        label_name = self.model.names[int(top_box.cls)]
        confidence = float(top_box.conf)

        return {
            "yolo_label": label_name,
            "confidence": round(confidence, 2),
            "vision_note": f"Visual defect confirmed: {label_name}"
        }

# --- Quick Local Test ---
if __name__ == "__main__":
    vision = VisionService()
    # Pass a dummy path; it will return the mock data if weights aren't loaded
    print(vision.analyze_image(r"C:\Users\njxnj\Downloads\Telegram Desktop\test_road.jpg"))