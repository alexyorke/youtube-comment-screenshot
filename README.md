# YouTube Comment Screenshot

This script renders all individual YouTube comment threads from a JSON file (obtained via `yt-dlp`) into PNG image files using Selenium and Pillow. It allows customization of the output image dimensions, DPI scaling, and padding.
The script supports rendering comments in English and other languages, provided the fonts used by the browser can display the necessary characters.

![Sample Output](sample.png)

## Prerequisites

- Python 3.6+
- pip (Python package installer)
- [yt-dlp](https://github.com/yt-dlp/yt-dlp) (or youtube-dl)
- Google Chrome browser
- ChromeDriver (managed automatically by `webdriver-manager`)

## Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/alexyorke/youtube-comment-screenshot.git
    cd youtube-comment-screenshot
    ```
2.  **(Optional but recommended) Create a virtual environment:**
    ```bash
    python -m venv venv
    # Activate the environment (Windows PowerShell):
    .\venv\Scripts\Activate.ps1
    # Or (Git Bash / Linux / macOS):
    # source venv/bin/activate
    ```
3.  **Install dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

## Usage

1.  **Download Comment Data:**
    You need to use `yt-dlp` to download the comment data for a YouTube video into a JSON file. Run the following command, replacing the URL with your target video and `video.json` with your desired output filename:

    ```bash
    yt-dlp --skip-download --write-comments --dump-single-json "https://www.youtube.com/watch?v=V9Hjb2S4e0Y" > video.json
    ```

    _(Note: `--skip-download` is added to prevent downloading the video itself)_

2.  **Run the Rendering Script:**
    Execute the Python script, providing the path to the JSON file generated in the previous step. You can also specify optional arguments for scaling, width, and padding.

    ```bash
    python render_comments.py <json_path> [--dpi <scale>] [--width <pixels>] [--padding <pixels>]
    ```

    **Arguments:**

    - `json_path`: (Required) Path to the input JSON file (e.g., `video.json`).
    - `--dpi <scale>`: (Optional) Device scale factor for rendering (e.g., `2.0` for 2x). Default: `1.0`.
    - `--width <pixels>`: (Optional) Width of the comment element in pixels. Default: `420`.
    - `--padding <pixels>`: (Optional) Whitespace padding to add around the comment image. Default: `0`.

    **Examples:**

    - Render comments from `video.json` with default settings:
      ```bash
      python render_comments.py video.json
      ```
    - Render with 2x DPI scaling:
      ```bash
      python render_comments.py video.json --dpi 2.0
      ```
    - Render at 600px width, 2x DPI, and 10px padding:
      ```bash
      python render_comments.py video.json --width 600 --dpi 2.0 --padding 10
      ```

## Output

The generated PNG images for each comment thread will be saved in the `screenshots/` directory within the project folder.
