import requests
import json
import PIL
from PIL import Image
import numpy as np

# Define the input data as a list of instances
image = PIL.Image.open("eaImageRecognition/cocData/testingImages/jkim2.jpg")
image = image.resize((512, 512))
image_array = np.array(image)
image_array = np.expand_dims(image_array, axis=0)
input_data = {"instances": image_array.tolist()}

# Define the URL for the prediction endpoint
url = "http://localhost:8501/v1/models/eaPredictBest:predict"

# Send a POST request to the prediction endpoint with the input data
response = requests.post(url, json=input_data)

# Check if the request was successful (HTTP status code 200)
if response.status_code == 200:
    # Parse the JSON response to get the prediction result
    prediction_result = response.json()
    response_data = json.loads(json.dumps(prediction_result))
    prediction = response_data['predictions']

    class_probabilities = np.exp(prediction) / np.sum(np.exp(prediction), axis=1, keepdims=True)
    final_prediction = np.argmax(class_probabilities, axis=1)+1
    print(final_prediction[0])
else:
    print(f"Request failed with status code {response.status_code}")