import requests
import geocoder
import speech_recognition as sr
import pyttsx3
import time

# Initialize the text-to-speech engine globally
engine = pyttsx3.init()

def speak_text(text):
    """Convert text to speech."""
    try:
        engine.say(text)
        engine.runAndWait()
    except RuntimeError:
        print("Error: Text-to-speech engine is busy.")

def meters_to_steps(distance_meters):
    """Convert meters to steps based on an average step length (0.762 meters per step)."""
    step_length = 0.762  # average step length in meters
    return int(distance_meters / step_length)

def get_navigation_steps(origin_coords, destination_coords):
    API_KEY = "sk.eyJ1Ijoia2VlMzMiLCJhIjoiY200bG03ZDJuMDNoMjJtc2NqeDdubHN1eiJ9.N2Vp8nb5VFjWdCk5K0_GPA"

    MAPBOX_DIRECTIONS_URL = "https://api.mapbox.com/directions/v5/mapbox/walking"
    url = f"{MAPBOX_DIRECTIONS_URL}/{origin_coords};{destination_coords}"
    params = {
        'access_token': API_KEY,
        'geometries': 'geojson',
        'overview': 'full',
        'steps': 'true'
    }

    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'routes' in data and data['routes']:
            steps = data['routes'][0]['legs'][0]['steps']
            return [(step['maneuver']['instruction'], step['distance']) for step in steps]
        else:
            print("Error: No routes found.")
            return None
    else:
        print("HTTP Error:", response.status_code, response.text)
        return None
def navigate(origin_coords,destination_address):
            if destination_address:
                # Convert destination address to coordinates
                mapbox_api_key = "sk.eyJ1Ijoia2VlMzMiLCJhIjoiY200bG03ZDJuMDNoMjJtc2NqeDdubHN1eiJ9.N2Vp8nb5VFjWdCk5K0_GPA"
                destination_coords = get_destination_coordinates(destination_address, mapbox_api_key)
                
                
                
                if destination_coords:
                    speak_text("Fetching navigation steps...")
                    steps = get_navigation_steps(origin_coords, destination_coords)
                
                    if steps:
                        for instruction, distance in steps:
                            distance_steps = meters_to_steps(distance)  # Convert meters to steps
                            step_instruction = f"{instruction}. Walk {distance_steps} steps."
                            print(step_instruction)
                            speak_text(step_instruction)
    
                            # Simulate real-time delay (e.g., waiting until user completes this step)
                            time.sleep(5)
                            current_location = geocoder.ip('me')
                            if current_location.ok:
                                origin_coords = f"{current_location.latlng[1]},{current_location.latlng[0]}"
                                # Adjust this delay as needed
                                navigate(origin_coords,destination_address)
                    
                    
                    
                    else:
                        speak_text("Failed to fetch navigation steps.")
                else:
                    speak_text("Could not find coordinates for the destination address.")
            else:
                speak_text("No destination address provided.")

def get_destination_coordinates(destination_address, api_key):
    MAPBOX_GEOCODING_URL = "https://api.mapbox.com/geocoding/v5/mapbox.places"
    url = f"{MAPBOX_GEOCODING_URL}/{destination_address}.json"
    params = {
        'access_token': api_key
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        data = response.json()
        if 'features' in data and data['features']:
            coordinates = data['features'][0]['geometry']['coordinates']
            return f"{coordinates[0]},{coordinates[1]}"  # longitude,latitude
        else:
            print("Error: No matching location found.")
            return None
    else:
        print("HTTP Error:", response.status_code, response.text)
        return None

def get_voice_input():
    recognizer = sr.Recognizer()
    with sr.Microphone() as source:
        print("Listening for the destination address...")
        try:
            audio = recognizer.listen(source)
            destination = recognizer.recognize_google(audio)
            print(f"You said: {destination}")
            return destination
        except sr.UnknownValueError:
            print("Sorry, I could not understand your voice.")
            return None
        except sr.RequestError as e:
            print(f"Speech recognition error: {e}")
            return None

if __name__ == "__main__":
    # Fetch current location
    current_location = geocoder.ip('me')
    if current_location.ok:
        origin_coords = f"{current_location.latlng[1]},{current_location.latlng[0]}"  # longitude,latitude

        # Get destination address from user's voice input
        destination_address = get_voice_input()
        navigate(origin_coords,destination_address)
        
    else:
        speak_text("Error: Unable to fetch current location. Check your internet connection.")