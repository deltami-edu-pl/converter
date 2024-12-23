import sys
import os
import re
from bs4 import BeautifulSoup

def extract_image_urls(html_content):
    soup = BeautifulSoup(html_content, 'html.parser')
    img_tags = soup.find_all('img')

    image_urls = []
    for img_tag in img_tags:
        src = img_tag.get('src')
        if src:
            image_urls.append(src)

    return image_urls

def get_image_files(folder_path):
    image_files = [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]
    return image_files

def move_used_images(html_file, figures_folder, new_figures_folder):
    if not os.path.isfile(html_file):
        print("UWAGA! Nie ma pliku "+html_file)
        sys.exit(1)
    
    # Read HTML content
    with open(html_file, 'r', encoding='utf-8') as file:
        html_content = file.read()

    # Extract image URLs from HTML
    html_image_urls = extract_image_urls(html_content)
    
    # Identify and remove unused images
    for image_url in html_image_urls:
        image_file = os.path.basename(image_url)
        image_path = os.path.join(figures_folder, image_file)
        new_image_path = os.path.join(new_figures_folder, image_file)
        if os.path.isfile(image_path):
            os.rename(image_path, new_image_path)
            print(f"Moved: {image_path}")

def main():
    
    if len(sys.argv) < 4:
        print("Za mało parametrów: python xxxxx.py <filename> <figures_folder> <color>")
        sys.exit(1)

    filename = sys.argv[1]
    figures_folder = sys.argv[2]
    new_figures_folder = sys.argv[3]
    
    move_used_images(filename, figures_folder, new_figures_folder)

if __name__ == "__main__":
    main()
