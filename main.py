import logging
import base64
import requests
import json
import os
import ipywidgets as widgets
from IPython.display import display, HTML

# Access the OpenAI API Key
api_key = os.getenv('OPENAI_API_KEY')

# Check if the API key was loaded successfully
if api_key is None:
    raise ValueError("API key not found. Make sure to set it in your environment.")

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class ImageStoryGenerator:
    def __init__(self, logger):
        self.logger = logger
        self.api_key = os.getenv('OPENAI_API_KEY')
        self.model = "gpt-4o-mini"
        self.temperature = 0.5
        self.max_tokens = 400
        self.cache = {}

        # Prompt for the image processing API
        self.image_processing_prompt = """
        You are an expert in analyzing and describing visual imagery. Your task is to provide a detailed, rich, and descriptive analysis of the provided image that highlights its key features, elements, and any potential themes or moods it might evoke.

        Instructions:
        - Review the image and identify the key visual elements and features (e.g., colors, shapes, textures, composition, etc.).
        - Describe the visual appearance of each person, including their clothing and any distinct characteristics.
        - Return the description of each person in a list format.
        """

    def process_image(self, image_data):
        self.logger.info("Processing image attachment")

        try:
            encoded_image = base64.b64encode(image_data).decode("utf-8")

            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}"
            }

            payload = {
                "model": self.model,
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": self.image_processing_prompt},
                            {"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{encoded_image}"}}
                        ]
                    }
                ],
                "max_tokens": self.max_tokens
            }

            response = requests.post("https://api.openai.com/v1/chat/completions", headers=headers, json=payload)
            response.raise_for_status()
            result = response.json()
            descriptions = result['choices'][0]['message']['content'].split('\n')
            return descriptions

        except Exception as e:
            self.logger.error(f"Error processing image: {e}")
            return []

    def generate_story_from_image(self, image_data, people_names, genre, desired_length):
        self.logger.info("Generating story from image")

        image_content = self.process_image(image_data)
        names_list = ", ".join(people_names)

        story_prompt = f"""
        Based on the following image description and the provided character names: {names_list}, create a short story in the first person that is engaging and creative for a {genre} audience. The story should be no more than {desired_length} words.

        Image Description:
        {image_content}
        """

        try:
            response = requests.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {self.api_key}"
                },
                json={
                    "model": self.model,
                    "messages": [{"role": "user", "content": story_prompt}],
                    "max_tokens": self.max_tokens,
                    "temperature": self.temperature
                }
            )
            response.raise_for_status()
            result = response.json()
            story = result['choices'][0]['message']['content']
            return story
        except Exception as e:
            self.logger.error(f"Error generating story: {e}")
            return "Error generating story."

# For running the interactive widgets
def run():
    # Instantiate ImageStoryGenerator
    image_story_generator = ImageStoryGenerator(logger)

    # Create an image upload widget
    file_upload = widgets.FileUpload(
        accept='image/*',  # Accept only image files
        multiple=False  # Single file upload
    )

    # Create widgets for the interactive inputs
    genre_input = widgets.Dropdown(
        options=['adventure', 'fantasy', 'mystery', 'drama', 'horror', 'action'],
        description='Genre:',
        layout=widgets.Layout(width='auto')
    )

    length_input = widgets.IntSlider(
        value=200, min=100, max=500, step=50,
        description='Story Length:',
        layout=widgets.Layout(width='auto')
    )

    generate_button = widgets.Button(
        description="Generate Story",
        button_style='info',
        layout=widgets.Layout(width='auto')
    )

    def on_button_click(b):
        # Check if an image was uploaded
        if not file_upload.value:
            print("Please upload an image.")
            return

        # Extract the uploaded image data
        uploaded_image = list(file_upload.value.values())[0]['content']

        # Process the image to get visual descriptions
        person_descriptions = image_story_generator.process_image(uploaded_image)

        # If there are no descriptions, stop
        if not person_descriptions:
            print("Failed to process image.")
            return

        # Create widgets for name inputs based on the person descriptions
        name_inputs = [
            widgets.Text(
                placeholder=f'Enter name for {desc}',
                description=desc,
                layout=widgets.Layout(width='auto')
            )
            for desc in person_descriptions
        ]

        # Display the name inputs and the rest of the UI for genre and length
        display(widgets.VBox([widgets.VBox(name_inputs), genre_input, length_input, generate_button]))

        def on_generate_story_click(b):
            # Get the names from the inputs
            people_names = [name_input.value for name_input in name_inputs if name_input.value.strip()]
            genre = genre_input.value
            length = length_input.value

            if not people_names:
                print("Please provide valid names.")
                return

            # Generate the story based on the image and inputs
            story = image_story_generator.generate_story_from_image(uploaded_image, people_names, genre, length)
            display(HTML(f"<h3>Generated Story:</h3><p>{story}</p>"))

        # Link the generate button click to the new function
        generate_button.on_click(on_generate_story_click)

    # Link the upload widget and button click
    file_upload.observe(lambda change: on_button_click(None), names='value')

    # Display the file upload widget and the initial buttons
    display(widgets.VBox([file_upload, genre_input, length_input, generate_button]))

# Uncomment below line when running in production
run()
