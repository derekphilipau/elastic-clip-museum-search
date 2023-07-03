import os
import jsonlines
import requests
import csv
from PIL import Image

IMG_RESTRICTED_BASE_URL = 'https://d1lfxha3ugu3d4.cloudfront.net/images/opencollection/objects/size1/'
IMG_SM_BASE_URL = 'https://d1lfxha3ugu3d4.cloudfront.net/images/opencollection/objects/size3/'
NOT_ON_VIEW = 'This item is not on view'

CLIP_SIZE = 224

# Set your paths
jsonl_file = 'data/collections.jsonl'
out_csv = 'data/descriptions.csv'
image_dir = 'data/images'

# Set whether you want padding or not
padding = True

def get_image_url(filename, copyright_restricted):
    if not filename:
        return None
    if copyright_restricted == 0:
        return f"{IMG_SM_BASE_URL}{filename}"
    return f"{IMG_RESTRICTED_BASE_URL}{filename}"

def resize_with_padding(image_path):
    image = Image.open(image_path)
    width, height = image.size
    max_dim = max(width, height)
    padded_image = Image.new('RGB', (max_dim, max_dim), color=(255, 255, 255))
    padded_image.paste(image, ((max_dim - width) // 2, (max_dim - height) // 2))
    padded_image = padded_image.resize((CLIP_SIZE, CLIP_SIZE))
    padded_image.save(image_path)

def resize_without_padding(image_path):
    image = Image.open(image_path)
    image = image.resize((CLIP_SIZE, CLIP_SIZE))
    image.save(image_path)

def download_image(url, filename, padding):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)
        if padding:
            resize_with_padding(filename)
        else:
            resize_without_padding(filename)
        return True
    else:
        print(f"Failed to download image from {url}")
        return False

def get_primary_artist(artists):
    if not artists:
        return ''
    primary_artist = min(artists, key=lambda x: x['rank'])
    return f"{primary_artist['role']}: {primary_artist['name']}. "

def create_description(data):
    title = data.get('title', '')
    date = data.get('object_date', '')
    medium = data.get('medium', '')
    classification = data.get('classification', '')
    if classification == '(not assigned)':
        classification = ''
    else:
        classification = f"Classification: {classification}. "
    primary_artist = get_primary_artist(data.get('artists', []))
    description = f"Title: {title}. Date: {date}. {primary_artist}{classification}Medium: {medium}."
    return description

def process_data(jsonl_file, out_csv, image_dir, padding):
    with jsonlines.open(jsonl_file) as reader, open(out_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'description']) # write header
        for obj in reader:
            id = obj['id']
            # download image
            download_result = False
            if ('museum_location' in obj and obj['museum_location'] and obj['museum_location']['name'] != NOT_ON_VIEW):
                if 'primary_image' in obj and obj['primary_image']:
                    image_url = get_image_url(obj['primary_image'], obj['copyright_restricted'])
                    download_result = download_image(image_url, f"{image_dir}/{id}.jpg", padding)
                    if not download_result:
                        image_url = get_image_url(obj['primary_image'], 1)
                        download_result = download_image(image_url, f"{image_dir}/{id}.jpg", padding)
            if download_result:
                # create description
                description = create_description(obj)
                writer.writerow([id, description]) # write row to CSV            

# Ensure output directories exist
os.makedirs(image_dir, exist_ok=True)

process_data(jsonl_file, out_csv, image_dir, padding)
