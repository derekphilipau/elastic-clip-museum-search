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
out_csv = 'data/image_data.csv'
image_dir = 'data/images'

# Set whether you want padding or not
is_padding = True
padding_color = (255, 255, 255) # white seems a bit better than black
on_view_only = False

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
    padded_image = Image.new('RGB', (max_dim, max_dim), color=padding_color)
    padded_image.paste(image, ((max_dim - width) // 2, (max_dim - height) // 2))
    padded_image = padded_image.resize((CLIP_SIZE, CLIP_SIZE))
    padded_image.save(image_path)

def resize_without_padding(image_path):
    image = Image.open(image_path)
    image = image.resize((CLIP_SIZE, CLIP_SIZE))
    image.save(image_path)

def download_image(url, filename, is_padding):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(filename, 'wb') as file:
            for chunk in response:
                file.write(chunk)
        if is_padding:
            resize_with_padding(filename)
        else:
            resize_without_padding(filename)
        return True
    else:
        print(f"Failed to download image from {url}")
        return False

def get_primary_artist(artists):
    if not artists:
        return None
    primary_artist = min(artists, key=lambda x: x['rank'])
    return {
        "role": primary_artist['role'],
        "name": primary_artist['name']
    }

def write_description(writer, data):
    title = data.get('title', '')
    primary_constituent = get_primary_artist(data.get('artists', []))
    role = ''
    constituent = ''
    if primary_constituent:
        if "role" in primary_constituent:
            role = primary_constituent['role']
        if "name" in primary_constituent:
            constituent = primary_constituent['name']
    classification = data.get('classification', '')
    if classification == '(not assigned)':
        classification = ''
    medium = data.get('medium', '')
    date = data.get('object_date', '')

    writer.writerow([data['id'], title, role, constituent, classification, medium, date]) # write row to CSV

def process_data(jsonl_file, out_csv, image_dir, is_padding):
    with jsonlines.open(jsonl_file) as reader, open(out_csv, 'w', newline='') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['id', 'title', 'role', 'constituent', 'classification', 'medium', 'date']) # write header
        for obj in reader:
            id = obj['id']
            if os.path.isfile(f"{image_dir}/{id}.jpg"):
                # don't re-download image
                write_description(writer, obj)
            elif (not on_view_only or ('museum_location' in obj and obj['museum_location'] and obj['museum_location']['name'] != NOT_ON_VIEW)):
                # download image
                download_result = False
                # check if file already exists:
                if 'primary_image' in obj and obj['primary_image']:
                    image_url = get_image_url(obj['primary_image'], obj['copyright_restricted'])
                    download_result = download_image(image_url, f"{image_dir}/{id}.jpg", is_padding)
                    if not download_result:
                        image_url = get_image_url(obj['primary_image'], 1)
                        download_result = download_image(image_url, f"{image_dir}/{id}.jpg", is_padding)
                if download_result:
                    write_description(writer, obj)

# Ensure output directories exist
os.makedirs(image_dir, exist_ok=True)

process_data(jsonl_file, out_csv, image_dir, is_padding)
