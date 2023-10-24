import os
from rembg import remove
import uuid

processed_images = []

def remove_background(image_data, output_path):
    output_data = remove(image_data)
    with open(output_path, 'wb') as output_file:
        output_file.write(output_data)
    return output_path

def batch_remove_background(image_data, output_folder):
    if not os.path.exists(output_folder):
        os.makedirs(output_folder)

    unique_filename = str(uuid.uuid4()) + ".png"
    output_path = os.path.join(output_folder, unique_filename).replace("\\", "/")

    output_data = remove(image_data)
    with open(output_path, 'wb') as output_file:
        output_file.write(output_data)

    processed_images.append(output_path)  # Save the full path

    print("Image processed and saved to:", output_path)
    print("Total processed images:", processed_images)

    return output_path