import os
import requests


model_url = os.getenv("MODEL_URL", "https://drive.google.com/uc?export=download&id=1fz2UlF08GiAUOe28MqRmcZf6kZ0JMMoo")
model_path = os.getenv("MODEL_PATH", "model.jpg")
if not os.path.exists(model_path):
    print("model does not exists.")
    print("Downloading the model from the URL...")
    try:
        response = requests.get(model_url)
        response.raise_for_status()  # Raise an error for bad responses
        with open("model.jpg", "wb") as model_file:
            model_file.write(response.content)
        print("Model downloaded successfully.")
    except requests.exceptions.RequestException as e:
        print(f"Failed to download the model: {e}")