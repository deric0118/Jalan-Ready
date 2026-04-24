import cv2
from ultralytics import YOLO

MODEL_PATH = "models/yolov8_road_damage.onnx"
TEST_IMAGE = r"C:\Users\njxnj\Downloads\Telegram Desktop\test_road.jpg"

# Class names (must match your training order)
CLASS_NAMES = {0: "pothole", 1: "crack", 2: "manhole"}

def get_position_description(center_x, center_y, img_w, img_h):
    """Return a string describing the relative position of the damage."""
    # Horizontal position
    if center_x < img_w * 0.33:
        h_pos = "left"
    elif center_x < img_w * 0.67:
        h_pos = "center"
    else:
        h_pos = "right"

    # Vertical position
    if center_y < img_h * 0.33:
        v_pos = "upper"
    elif center_y < img_h * 0.67:
        v_pos = "middle"
    else:
        v_pos = "lower"

    return f"{v_pos}-{h_pos}"

# Load image to get dimensions
img = cv2.imread(TEST_IMAGE)
if img is None:
    print("Error: Could not read image.")
    exit()
img_height, img_width = img.shape[:2]

model = YOLO(MODEL_PATH)
results = model(TEST_IMAGE)

# Print and visualize detections
for r in results:
    boxes = r.boxes
    if boxes is None:
        print("No detections.")
        continue

    print(f"Detected {len(boxes)} objects:")
    for box in boxes:
        cls = int(box.cls)
        conf = float(box.conf)
        xyxy = box.xyxy[0].tolist()
        x1, y1, x2, y2 = map(int, xyxy)

        # Calculate center of the bounding box
        center_x = (x1 + x2) / 2
        center_y = (y1 + y2) / 2

        # Get human‑readable position
        position = get_position_description(center_x, center_y, img_width, img_height)

        print(f"  {CLASS_NAMES[cls]} ({conf:.2f}) — {position} area")

        # Draw rectangle and label on image
        cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f"{CLASS_NAMES[cls]} {conf:.2f}"
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

# Show the image with bounding boxes
cv2.imshow("Road Damage Detection", img)
cv2.waitKey(0)
cv2.destroyAllWindows()

# Optionally save the result
# cv2.imwrite("detected_output.jpg", img)

print("✅ Visualisation complete!")