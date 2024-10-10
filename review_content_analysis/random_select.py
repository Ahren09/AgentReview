import os
import random
import shutil

# Set the path to the main directory where files are located (absolute path to the target directory)
# In this case, the directory contains the original data in JSON format
base_dir = 'real_review/original_data/'

# Define the target directory where the selected JSON files will be copied
# This is a subdirectory within the base directory, named 'selected_files'
selected_base_dir = os.path.join(base_dir, 'selected_files')

# Create a list to store the full paths of all JSON files found in the base directory
json_files = []

# Traverse the base directory and its subdirectories to locate all files
# Collect the paths of files that have a '.json' extension
for root, dirs, files in os.walk(base_dir):
    for file in files:
        if file.endswith('.json'):  # Check if the file is a JSON file
            json_files.append(os.path.join(root, file))  # Add the full path of the file to the list

# Calculate the number of files to select randomly
# 1% of the total number of JSON files is selected, with a minimum of 1 file
num_files_to_select = max(1, int(len(json_files) * 0.01))

# Randomly select 1% of the JSON files from the list of all files
selected_files = random.sample(json_files, num_files_to_select)

# Print the number of selected files for reference
print(f"Selected {num_files_to_select} file(s):")

# Copy the selected files to the target directory ('selected_files'), preserving their original directory structure
for file in selected_files:
    # Get the relative path of the file (relative to the base directory)
    relative_path = os.path.relpath(file, base_dir)

    # Create the full destination path for the file in the target directory
    dest_file_path = os.path.join(selected_base_dir, relative_path)

    # Ensure that the destination directory exists; if not, create it
    dest_dir = os.path.dirname(dest_file_path)
    os.makedirs(dest_dir, exist_ok=True)

    # Copy the file from the original location to the destination
    shutil.copy(file, dest_file_path)

# Print confirmation message after all files have been successfully copied
print("File copying completed.")
