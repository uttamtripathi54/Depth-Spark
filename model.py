import os
from dotenv import load_dotenv
import fal_client
import requests
from urllib.parse import urlparse

load_dotenv()

def process_image_to_3d(image_path_or_url, is_url=True):
    """
    Process an image (URL or file) using fal-ai/trellis to generate a 3D GLTF model.
    
    Args:
        image_path_or_url (str): URL or file path of the input image.
        is_url (bool): True if input is a URL, False if it's a file path.
    
    Returns:
        dict: The fal-ai/trellis API response containing the model URL or data.
    
    Raises:-
        Exception: If the API call or processing fails.
    """
    try:
        # Prepare input data for fal-ai/trellis
        if is_url:
            # Validate URL
            parsed_url = urlparse(image_path_or_url)
            if not parsed_url.scheme or not parsed_url.netloc:
                raise ValueError(f"Invalid image URL: {image_path_or_url}")
            input_data = {'image_url': image_path_or_url}
        else:
            # Validate file exists and is an image
            if not os.path.exists(image_path_or_url):
                raise FileNotFoundError(f"Image file not found: {image_path_or_url}")
            allowed_extensions = {'.png', '.jpg', '.jpeg', '.gif'}
            if not any(image_path_or_url.lower().endswith(ext) for ext in allowed_extensions):
                raise ValueError(f"Unsupported file format: {image_path_or_url}")
            
            # Upload the file to fal-ai storage and get the URL
            with open(image_path_or_url, 'rb') as f:
                # Read the file content
                file_content = f.read()
                # Get the file name and extension
                file_name = os.path.basename(image_path_or_url)
                # Determine the MIME type based on extension
                extension = os.path.splitext(file_name)[1].lower()
                mime_types = {
                    '.png': 'image/png',
                    '.jpg': 'image/jpeg',
                    '.jpeg': 'image/jpeg',
                    '.gif': 'image/gif'
                }
                mime_type = mime_types.get(extension, 'application/octet-stream')
                # Upload the file using fal_client.upload
                uploaded_url = fal_client.upload(file_content, file_name=file_name, content_type=mime_type)
                input_data = {'image_url': uploaded_url}

        # Submit to fal-ai/trellis
        print(f"Submitting to fal-ai/trellis with input: {input_data}")
        result = fal_client.submit(
            'fal-ai/trellis',
            arguments=input_data,
        ).get()

        # Log the result for debugging
        print(f"fal-ai/trellis result: {result}")

        # Validate the result
        if not isinstance(result, dict):
            raise ValueError(f"Unexpected fal-ai/trellis response format: {result}")
        
        # Check for model_mesh or other expected keys
        if 'model_mesh' not in result or not isinstance(result['model_mesh'], dict) or 'url' not in result['model_mesh']:
            print(f"Warning: No model_mesh.url found in result: {result}")
            # Return the result anyway to allow app.py to handle other possible keys
            return result

        # Verify the model URL is accessible
        model_url = result['model_mesh']['url']
        try:
            response = requests.head(model_url, timeout=5)
            if response.status_code != 200:
                print(f"Warning: Model URL is not accessible (HTTP {response.status_code}): {model_url}")
        except requests.RequestException as e:
            print(f"Warning: Failed to verify model URL: {model_url}, Error: {str(e)}")

        return result

    except Exception as e:
        print(f"Error in process_image_to_3d: {str(e)}")
        raise