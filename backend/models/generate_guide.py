from openai import OpenAI
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Initialize the OpenAI client with your project-scoped API key
client = OpenAI(
    api_key=os.getenv("OPENAI_PROJECT_API_KEY")  # Ensure your API key is stored securely
)

def generate_study_guide(prompt):
    try:
        # Use the OpenAI client to generate a response
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Specify the model
            store=True,  # Store the completion if required
            messages=[
                {"role": "system", "content": "You are a helpful assistant for generating study guides."},
                {"role": "user", "content": f"Create a study guide for: {prompt}"}
            ]
        )
        # Extract and return the generated content using dot notation
        return completion.choices[0].message.content
    except Exception as e:
        raise Exception(f"Error generating study guide: {e}")
