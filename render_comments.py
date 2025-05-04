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

def main(json_path):
    # load comments
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    comments = data["comments"] # Access comments via the key

    # prepare output dir
    out_dir = Path("screenshots")
    out_dir.mkdir(exist_ok=True)

    # configure headless Chrome
    chrome_opts = Options()
    chrome_opts.add_argument("--headless")
    chrome_opts.add_argument("--disable-gpu")
    chrome_opts.add_argument("--window-size=500,200")
    service = ChromeService(ChromeDriverManager().install())
    driver = webdriver.Chrome(service=service, options=chrome_opts)

    for c in comments:
        html_src = render_comment_html(c)
        # URL-encode the HTML source
        encoded_html = urllib.parse.quote(html_src)
        data_url = "data:text/html;charset=utf-8," + encoded_html
        driver.get(data_url)

        # Wait for the comment element to be present before finding it
        wait = WebDriverWait(driver, 10) # Wait up to 10 seconds
        comment_el = wait.until(EC.presence_of_element_located((By.ID, "comment")))

        # find the comment container and screenshot it
        file_name = out_dir / f"{c['id']}.png"
        comment_el.screenshot(str(file_name))
        print(f"Saved: {file_name}")

    driver.quit()

if __name__ == "__main__":
    import sys
    if len(sys.argv) != 2:
        print("Usage: python render_comments.py comments.json")
        sys.exit(1)
    main(sys.argv[1])
