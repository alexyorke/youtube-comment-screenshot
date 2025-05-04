#!/usr/bin/env python3
import json
import os
import html
from pathlib import Path
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service as ChromeService
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.common.by import By
import urllib.parse
import argparse
from PIL import Image, ImageChops
import io

def render_comment_html(c):
    # escape text to avoid breaking HTML
    author     = html.escape(c["author"])
    time_text  = html.escape(c["_time_text"])
    text       = html.escape(c["text"])
    # Reverted: No longer specifically removing newlines here
    thumbnail  = c["author_thumbnail"]
    author_url = c["author_url"]
    likes      = c["like_count"]
    return f"""
<!DOCTYPE html>
<html><head>
  <meta charset="utf-8">
  <style>
    body {{ margin:0; padding:0; }}
    .comment {{
      font-family: Arial, sans-serif;
      display: flex;
      align-items: flex-start;
      padding: 10px;
      border-bottom:1px solid #e0e0e0;
      width: 420px;
      overflow: hidden;
    }}
    .avatar {{
      flex-shrink: 0;
      margin-right: 8px;
      width: 36px; height: 36px;
      border-radius: 50%;
    }}
    .body {{
      flex-grow: 1;
    }}
    .header {{
      display: flex;
      align-items: center;
      font-size: 14px;
      line-height: 1.2;
    }}
    .author {{
      font-weight: 500;
      color: #065fd4;
      text-decoration: none;
      margin-right: 6px;
    }}
    .time {{
      color: #606060;
      font-size: 12px;
    }}
    .text {{
      margin: 4px 0;
      font-size: 14px;
      line-height: 1.4;
    }}
    .footer {{
      font-size: 12px;
      color: #606060;
    }}
  </style>
</head>
<body>
  <div class="comment" id="comment">
    <img class="avatar" src="{thumbnail}" alt="avatar">
    <div class="body">
      <div class="header">
        <a class="author" href="{author_url}">{author}</a>
        <span class="time">{time_text}</span>
      </div>
      <div class="text">{text}</div>
      <div class="footer">👍 {likes}</div>
    </div>
  </div>
</body>
</html>
"""

def main(json_path, dpi_scale):
    # load comments
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    comments = data["comments"] 

    # prepare output dir
    out_dir = Path("screenshots")
    out_dir.mkdir(exist_ok=True)

    # configure headless Chrome
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    # Use a large fixed window size
    chrome_opts.add_argument("--window-size=2000,2000") 
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)

    for c in comments:
        html_src = render_comment_html(c)
        encoded_html = urllib.parse.quote(html_src)
        data_url = "data:text/html;charset=utf-8," + encoded_html
        driver.get(data_url)

        wait = WebDriverWait(driver, 10) 
        comment_el = wait.until(EC.presence_of_element_located((By.ID, "comment")))
        
        # Get element dimensions BEFORE scaling
        location = comment_el.location
        size = comment_el.size
        x, y = location['x'], location['y']
        w, h = size['width'], size['height']
        
        # Apply scaling via CSS transform if dpi_scale > 1.0
        if dpi_scale > 1.0:
            driver.execute_script(f"arguments[0].style.transform = 'scale({dpi_scale})'; arguments[0].style.transformOrigin = 'top left';", comment_el)
            # Optional delay - might be needed for complex rendering
            # import time
            # time.sleep(0.1) 

        # Take screenshot of the viewport
        png = driver.get_screenshot_as_png()
        
        # Load image with Pillow and ensure RGB
        img = Image.open(io.BytesIO(png)).convert('RGB')

        # Create a white background image
        bg = Image.new('RGB', img.size, (255, 255, 255))
        
        # Calculate difference between image and white background
        diff = ImageChops.difference(img, bg)
        
        # Get bounding box of the difference (non-white areas)
        bbox = diff.getbbox()
        
        # Crop the original image if content was found
        if bbox:
            cropped_img = img.crop(bbox)
        else:
            # Handle case where screenshot is entirely white (error?)
            print(f"Warning: Screenshot for {c['id']} seems empty.")
            cropped_img = img # Keep the original (blank) image

        # Calculate crop box based on original location/size and dpi_scale
        # left = x 
        # top = y
        # right = x + w * dpi_scale
        # bottom = y + h * dpi_scale
        
        # Crop the image
        # cropped_img = img.crop((left, top, right, bottom)) # Removed manual crop
        
        # Save the auto-cropped image
        file_name = out_dir / f"{c['id']}.png"
        cropped_img.save(file_name)
        
        print(f"Saved: {file_name} (Scale: {dpi_scale}x)")

        # Reset transform if it was applied
        if dpi_scale > 1.0:
            driver.execute_script("arguments[0].style.transform = 'none';", comment_el)

    driver.quit()

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Render comment threads from JSON to PNG images using Selenium.')
    parser.add_argument('json_path', help='Path to the JSON file containing comment data.')
    parser.add_argument('--dpi', type=float, default=1.0, 
                        help='Device scale factor for rendering (e.g., 2.0 for 2x DPI). Default is 1.0.')
    
    args = parser.parse_args()

    main(args.json_path, args.dpi)
