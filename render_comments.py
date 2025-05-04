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

def render_comment_html(c, width):
    # escape text to avoid breaking HTML
    author     = html.escape(c["author"])
    time_text  = html.escape(c["_time_text"])
    text       = html.escape(c["text"])
    thumbnail  = c["author_thumbnail"]
    author_url = c["author_url"]
    likes      = c["like_count"]
    # Format like count 
    if likes >= 1_000_000:
        likes_str = f"{likes / 1_000_000:.1f}M"
    elif likes >= 1_000:
        likes_str = f"{likes / 1_000:.1f}K"
    else:
        likes_str = str(likes)
    likes_str = likes_str.replace('.0', '') 

    # Basic SVG paths for thumbs up/down (approximations)
    thumb_up_svg = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" focusable="false"><path d="M18.77 11h-4.23l1.52-4.94C16.38 5.03 15.54 4 14.38 4c-.58 0-1.14.24-1.52.65L7 11H3v10h4h1h9.43c1.06 0 1.98-.67 2.19-1.61l1.34-6C21.23 12.15 20.18 11 18.77 11zM7 20H4v-8h3v8zm12.98-6.83-1.34 6C18.54 19.65 18.03 20 17.43 20H8v-8.61l5.6-6.06C13.79 5.12 14.08 5 14.38 5c.26 0 .5.11.63.3.07.1.15.26.09.47l-1.52 4.94L13.18 12h1.35h4.23c.41 0 .8.17 1.03.46.11.15.18.33.16.51z"></path></svg>'
    # Corrected thumbs down path based on user example
    thumb_down_svg = '<svg xmlns="http://www.w3.org/2000/svg" height="24" viewBox="0 0 24 24" width="24" focusable="false"><path d="M17,4h-1H6.57C5.5,4,4.59,4.67,4.38,5.61l-1.34,6C2.77,12.85,3.82,14,5.23,14h4.23l-1.52,4.94C7.62,19.97,8.46,21,9.62,21 c0.58,0,1.14-0.24,1.52-0.65L17,14h4V4H17z M10.4,19.67C10.21,19.88,9.92,20,9.62,20c-0.26,0-0.5-0.11-0.63-0.3 c-0.07-0.1-0.15-0.26-0.09-0.47l1.52-4.94l0.4-1.29H9.46H5.23c-0.41,0-0.8-0.17-1.03-0.46c-0.12-0.15-0.25-0.4-0.18-0.72l1.34-6 C5.46,5.35,5.97,5,6.57,5H16v8.61L10.4,19.67z M20,13h-3V5h3V13z"></path></svg>'

    return f"""
<!DOCTYPE html>
<html><head>
  <meta charset="utf-8">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Roboto:ital,wght@0,100..900;1,100..900&display=swap" rel="stylesheet">
  <style>
    body {{ 
      margin:0; 
      padding:0; 
      background-color: #fff; /* --yt-spec-base-background */
      font-family: "Roboto", Arial, sans-serif; /* Apply Roboto */
    }}
    .comment {{ 
      /* font-family: Roboto, Arial, sans-serif; */ /* Moved to body */
      display: flex;
      align-items: flex-start;
      padding: 12px 0px; /* Adjust padding slightly */
      width: {width}px; /* Use passed width */
      overflow: hidden; 
      margin-left: 10px; /* Simulate typical indent */
    }}
    .avatar {{
      flex-shrink: 0;
      margin-right: 12px; /* --ytd-margin-3x ? */
      width: 36px; height: 36px; /* Smaller avatar like YT */
      border-radius: 50%;
    }}
    .body {{
      flex-grow: 1;
    }}
    .header {{
      display: flex;
      align-items: center;
      font-size: 13px; 
      line-height: 1.3;
      margin-bottom: 2px; 
    }}
    .author {{
      font-weight: 700; /* Make author bold */
      color: #0f0f0f; /* --yt-spec-text-primary */
      text-decoration: none;
      margin-right: 8px; /* --ytd-margin-2x */
    }}
    a.author:hover {{ text-decoration: none; }}
    .time {{
      color: #606060; /* --yt-spec-text-secondary */
      font-size: 12px;
    }}
    .text {{
      margin: 2px 0 8px 0; /* Top: 2px, Bottom: --ytd-margin-2x */
      font-size: 14px;
      line-height: 20px; /* Set to 20px */
      color: #0f0f0f; /* --yt-spec-text-primary */
      white-space: pre-wrap; 
      word-wrap: break-word;
    }}
    .footer {{
      display: flex; 
      align-items: center;
      font-size: 13px;
      color: #606060; /* --yt-spec-text-secondary */
    }}
    .footer .icon-button {{
      /* Button wrapper for icon */
      display: inline-flex;
      padding: 8px; /* Give space around icon */
      border-radius: 50%; /* Circular hover */
      cursor: pointer;
      margin-right: -8px; /* Offset padding */
    }}
     .footer .icon-button:hover {{
         background-color: rgba(0, 0, 0, 0.05); /* --yt-spec-badge-chip-background */
     }}
    .footer .icon {{
      /* SVG icon styling */
      width: 16px;
      height: 16px;
      fill: #606060; /* --yt-spec-text-secondary */
    }}
    .footer .likes {{
      margin-left: 4px; /* Space after thumb icon */
      margin-right: 8px; /* Space before dislike icon */
      font-size: 12px;
    }}
    .footer .reply-btn {{
        margin-left: 8px; /* --ytd-margin-2x */
        font-weight: 500;
        font-size: 12px; /* Smaller reply button text */
        color: #0f0f0f; /* --yt-spec-text-primary */
        cursor: pointer;
        padding: 8px 16px; /* YouTube's button padding */
        border-radius: 18px; /* More rounded */
    }}
    .footer .reply-btn:hover {{
        background-color: rgba(0, 0, 0, 0.05); /* --yt-spec-badge-chip-background */
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
      <div class="footer">
         <span class="icon-button"><span class="icon">{thumb_up_svg}</span></span>
         <span class="likes">{likes_str if likes > 0 else ''}</span>
         <span class="icon-button" style="margin-left: 0px;"><span class="icon">{thumb_down_svg}</span></span>
         <span class="reply-btn">Reply</span>
      </div>
    </div>
  </div>
</body>
</html>
"""

def main(json_path, dpi_scale, width):
    # load comments
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    comments = data["comments"] 

    # prepare output dir
    out_dir = Path("screenshots")
    out_dir.mkdir(exist_ok=True)

    # Calculate window size based on args (add padding)
    # Use the provided width and a large fixed height
    scaled_width = int(width * dpi_scale) + 40 # Add horizontal padding
    fixed_height = 2000 # Keep height large for auto-crop

    # configure headless Chrome
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    # Set window size dynamically based on width arg and scale
    chrome_opts.add_argument(f"--window-size={scaled_width},{fixed_height}") 
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)

    for c in comments:
        html_src = render_comment_html(c, width)
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
    parser.add_argument('--width', type=int, default=420,
                        help='Width of the comment element in pixels. Default is 420.')
    
    args = parser.parse_args()

    main(args.json_path, args.dpi, args.width)
