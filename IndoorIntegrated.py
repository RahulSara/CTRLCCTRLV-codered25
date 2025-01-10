import pyttsx3
import speech_recognition as sr
from ultralytics import YOLO
import cv2
import numpy as np
from typing import Dict, List, Tuple
import time
import psutil


class RoomAndHazardClassifier:
    def __init__(self):
        # Initialize text-to-speech engine
        self.speaker = pyttsx3.init()
        
        # Load the YOLOv8 model
        self.model = YOLO('yolov8x.pt')
        
        # Define room classification rules based on objects
        self.room_rules = {
            'bedroom': ['bed', 'wardrobe', 'chair'],
            'bathroom': ['toilet', 'sink', 'bathtub', 'shower'],
            'kitchen': ['refrigerator', 'oven', 'sink', 'microwave', 'dining table'],
            'living_room': ['couch', 'tv', 'chair', 'sofa'],
            'dining_room': ['dining table', 'chair'],
            'office': ['desk', 'chair', 'laptop', 'monitor']
        }
        
        # Predefined layout (positions and dimensions of rooms in the house)
        self.house_layout = {
            'living_room': {'coords': (0, 0), 'dimensions': (4, 5)},  # x, y, width, height
            'kitchen': {'coords': (5, 0), 'dimensions': (3, 4)},
            'bedroom': {'coords': (0, 6), 'dimensions': (4, 4)},
            'bathroom': {'coords': (5, 5), 'dimensions': (2, 3)},
            'dining_room': {'coords': (8, 0), 'dimensions': (3, 4)},
            'office': {'coords': (8, 5), 'dimensions': (3, 4)}
        }
        
    def detect_objects(self, image: np.ndarray) -> List[Dict]:
        """
        Detect objects in the image using YOLOv8
        """
        results = self.model(image)
        detections = []
        
        for result in results[0].boxes.data:
            x1, y1, x2, y2, conf, cls = result
            class_name = self.model.names[int(cls)]
            
            detections.append({
                'class': class_name,
                'confidence': float(conf),
                'bbox': (int(x1), int(y1), int(x2), int(y2))
            })
            
        return detections
    
    def classify_room(self, objects: List[Dict]) -> Tuple[str, float]:
        """
        Classify room type based on detected objects
        Returns room type and confidence score
        """
        room_scores = {room: 0 for room in self.room_rules.keys()}
        
        # Count matching objects for each room type
        detected_classes = [obj['class'] for obj in objects]
        for room, required_objects in self.room_rules.items():
            matches = sum(obj in detected_classes for obj in required_objects)
            if matches > 0:
                room_scores[room] = matches / len(required_objects)
        
        # Get room type with highest score
        best_room = max(room_scores.items(), key=lambda x: x[1])
        return best_room[0], best_room[1]
    
    def process_frame(self, frame: np.ndarray) -> Dict:
        """
        Process a single frame and classify the room
        """
        # Detect objects
        detections = self.detect_objects(frame)
        
        # Classify room based on detected objects
        room_type, confidence = self.classify_room(detections)
        
        return {
            'room_type': room_type,
            'confidence': confidence,
            'detected_objects': detections
        }

    def calculate_distance(self, bbox_height, frame_height, actual_height=1.7):
        focal_length = 700  
        if bbox_height > 0:
            distance = (actual_height * focal_length) / (bbox_height / frame_height)
            return distance  
        return float('inf')  

    def give_audio_feedback(self, detections, frame_height):
        last_feedback_time = 0  # Store the last feedback time
        current_time = time.time()

        # Allow feedback every 0.5 seconds for faster warnings
        if current_time - last_feedback_time < 0.5:
            return

        if not detections:
            return

        for detection in detections:
            confidence = detection['confidence'] * 100  # Confidence score in percentage
            class_name = detection['class']  # Class Name
            bbox_height = detection['bbox'][3] - detection['bbox'][1]  # Bounding box height in pixels

            # Calculate distance
            distance = self.calculate_distance(bbox_height, frame_height)

            feedback_fast = ""
            feedback = ""
            
            # Warnings for different objects
            if confidence > 85 and distance < 4000:  # Distance threshold: 50 meters
                if class_name == "person":
                    if distance > 1700 and distance <= 4000:
                        feedback = f"Caution! Person ahead"
                        self.speak(feedback)
                    elif distance <= 1700:
                        feedback_fast = f"Alert! Person very close"
                        self.speak(feedback_fast)
                else:
                    if distance > 1700 and distance <= 4000:
                        feedback = f"Warning! {class_name} ahead"
                        self.speak(feedback)
                    elif distance <= 1700:
                        feedback_fast = f"Danger! {class_name}"
                        self.speak(feedback_fast)

        # Update the last feedback time
        last_feedback_time = current_time

    def navigate_to_room(self, current_room: str, target_room: str) -> str:
        """
        Provide navigation suggestion based on current room and target room
        Also speaks out the directions using TTS
        """
        if current_room == target_room:
            navigation_message = "You are already in the target room."
            self.speak(navigation_message)
            return navigation_message
        
        current_coords = self.house_layout[current_room]['coords']
        target_coords = self.house_layout[target_room]['coords']
        
        # Simple navigation logic: direction based on x and y coordinates
        direction = []
        if target_coords[0] > current_coords[0]:
            direction.append("Move right")
        elif target_coords[0] < current_coords[0]:
            direction.append("Move left")
        
        if target_coords[1] > current_coords[1]:
            direction.append("Move down")
        elif target_coords[1] < current_coords[1]:
            direction.append("Move up")
        
        navigation_message = " -> ".join(direction)
        self.speak(navigation_message)
        return navigation_message

    def speak(self, message: str):
        """
        Convert the navigation message to speech
        """
        self.speaker.say(message)
        self.speaker.runAndWait()

    def ask_for_target_room(self) -> str:
        """
        Ask the user which room they want to go to, using voice input.
        """
        print("Please say the name of the room you want to go to.")
        self.speak("Please say the name of the room you want to go to.")
        
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()

        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                print("Listening for room name...")
                audio = recognizer.listen(source, timeout=5)
            
            room_name = recognizer.recognize_google(audio).lower()
            print(f"You said: {room_name}")

            # Validate room selection
            while room_name not in self.house_layout:
                self.speak("Invalid room name. Please try again.")
                print("Invalid room name. Please try again.")
                
                # Listen again
                with microphone as source:
                    recognizer.adjust_for_ambient_noise(source)
                    audio = recognizer.listen(source, timeout=5)
                
                room_name = recognizer.recognize_google(audio).lower()
                print(f"You said: {room_name}")
            
            return room_name
        except sr.UnknownValueError:
            self.speak("Sorry, I couldn't understand that. Please try again.")
            print("Sorry, I couldn't understand that.")
            return self.ask_for_target_room()
        except sr.RequestError:
            self.speak("Sorry, I'm having trouble with the speech service. Please try again later.")
            print("Sorry, I'm having trouble with the speech service.")
            return self.ask_for_target_room()

# Main program logic
def main():
    # Initialize the classifier
    classifier = RoomAndHazardClassifier()
    
    # Open the video capture
    cap = cv2.VideoCapture(0)  # 0 for default camera
    
    if not cap.isOpened():
        print("Error: Could not open camera.")
        return
    
    # Ask user for target room via voice
    target_room = classifier.ask_for_target_room()
    
    current_room = None
    
    while True:
        # Capture a frame from the camera
        ret, frame = cap.read()
        if not ret:
            print("Error: Failed to capture frame.")
            break
        
        # Process the frame
        results = classifier.process_frame(frame)
        
        # Display results on the frame
        room_type = results['room_type']
        confidence = results['confidence']
        cv2.putText(frame, f"Room: {room_type} ({confidence:.2f})", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
        
        for obj in results['detected_objects']:
            class_name = obj['class']
            conf = obj['confidence']
            bbox = obj['bbox']
            cv2.rectangle(frame, (bbox[0], bbox[1]), (bbox[2], bbox[3]), (255, 0, 0), 2)
            cv2.putText(frame, f"{class_name} ({conf:.2f})", (bbox[0], bbox[1] - 10),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 0, 0), 2)
        
        # Update current room
        if current_room != room_type:
            current_room = room_type
            print(f"Current room: {current_room}")
        
        # Provide navigation suggestion based on user input
        if current_room:
            navigation = classifier.navigate_to_room(current_room, target_room)
            print(f"Navigation from {current_room} to {target_room}: {navigation}")
        
        # Give audio feedback for any detected hazards
        classifier.give_audio_feedback(results['detected_objects'], frame.shape[0])

        # Show the frame
        cv2.imshow('Room and Hazard Classifier', frame)
        
        # Break the loop on 'q' key press
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break
    
    # Release the capture and close windows
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()
