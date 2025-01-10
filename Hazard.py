from ultralytics import YOLO
import cv2
import pyttsx3  
import time
import psutil

# Text-to-speech
engine = pyttsx3.init()
engine.setProperty('rate', 200)  # Speed of speech
engine.setProperty('volume', 1.0)  

# Load YOLO model
model = YOLO('yolov8n.pt')

def log_metrics(detections, start_time):
    #latency
    end_time = time.time()
    latency = end_time - start_time  
    #memory usage (in MB)
    process = psutil.Process()
    memory_info = process.memory_info()
    memory_usage = memory_info.rss / (1024 * 1024)  #byte to mb
    # Log metrics
    print(f"Latency: {latency:.4f} seconds")
    print(f"Memory Usage: {memory_usage:.2f} MB")


def calculate_distance(bbox_height, frame_height, actual_height=1.7):
    focal_length = 700  
    if bbox_height > 0:
        distance = (actual_height * focal_length) / (bbox_height / frame_height)
        return distance  
    return float('inf') 

def filter_detections(detections):
    filtered = []
    for detection in detections:
        class_id = int(detection[5])  
        class_name = model.names[class_id]  
        filtered.append(detection)  
    return filtered


last_feedback_time = 0  # Store the last feedback time

def give_audio_feedback(detections, frame_height):
    global last_feedback_time
    current_time = time.time()

    #feedback every 0.5 seconds
    if current_time - last_feedback_time < 0.5:
        return

    if not detections:
        return

    for detection in detections:
        confidence = detection[4] * 100  #accuracy
        class_id = int(detection[5]) 
        class_name = model.names[class_id]  
        bbox_height = detection[3] - detection[1] 

        #distance
        distance = calculate_distance(bbox_height, frame_height)

        feedback_fast = ""
        feedback = ""
        
        # Warnings for different objects
        if confidence > 80 and distance < 4000:  
            if class_name == "person":
                if distance > 1700 and distance <= 4000:
                    feedback = f"Caution! Person ahead"
                    #print(feedback)
                    engine.say(feedback)
                    engine.runAndWait()
                elif distance <= 1700:
                    feedback_fast = f"Alert! Person very close"
                    print(feedback_fast)
                    engine.say(feedback_fast)
                    engine.runAndWait()
            else:
                if distance > 1700 and distance <= 4000:
                    feedback = f"Warning! {class_name} ahead"
                    print(feedback)
                    engine.say(feedback)
                    engine.runAndWait()
                elif distance <= 1700:
                    feedback_fast = f" danger! {class_name} {class_name}{class_name}{class_name}{class_name}"
                    print(feedback_fast)
                    engine.say(feedback_fast)
                    engine.runAndWait()
    print(f"Bounding box height: {bbox_height}")
    print(f"Frame height: {frame_height}")
    print("Distance is ", distance)
    
    last_feedback_time = current_time
    


# Real-Time Detection
def detect_from_camera():
    cap = cv2.VideoCapture(0)  #0 is system camera

    if not cap.isOpened():
        print("Error: Unable to access the camera.")
        return

    while True:
        ret, frame = cap.read()
        if not ret:
            print("Error: Unable to read the camera feed.")
            break

        
        frame_height = frame.shape[0]

        # Run YOLOv8 inference
        results = model.predict(frame)
        # Filter detections
        filtered_detections = filter_detections(results[0].boxes.data.tolist())
        # Provide audio feedback for hazards
        give_audio_feedback(filtered_detections, frame_height)
        start_time = time.time()
        log_metrics(filtered_detections, start_time)

        # Annotate frame with detections
        annotated_frame = results[0].plot()

        # Display the annotated frame
        cv2.imshow("YOLOv8 Real-Time Detection", annotated_frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

# Run the detection
detect_from_camera()
