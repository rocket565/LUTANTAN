# Lu Tantan

Lu Tantan is a Streamlit-based AI travel vlog generator. Enter a destination, choose a storytelling style and a generation mode, and the application builds a scene-by-scene script before producing a downloadable MP4.

The current user interface and generated narration are primarily in Chinese.

## Features

- Generates destination-based travel scripts with OpenAI-compatible models
- Falls back to a built-in sample script when OpenAI is not configured
- Supports Alibaba Cloud Wanxiang text-to-video (`wan2.2-t2v-plus`)
- Supports Wanxiang image-to-video (`wan2.2-i2v-plus`)
- Accepts uploaded JPG, JPEG, and PNG travel photos in image-to-video mode
- Can generate source images automatically with Wanxiang (`wanx-v1`)
- Includes eight script styles, from energetic travel guides to food, documentary, family, and luxury themes
- Calculates scene timing from narration length
- Adds optional Chinese voice-over with Microsoft Edge TTS
- Adds optional burned-in subtitles with resolution-aware sizing
- Supports fades and crossfades between scenes
- Produces landscape, portrait, and square videos
- Includes a one-scene test mode for quicker API checks

## How It Works

```text
Destination and creative settings
              |
              v
   OpenAI script generation
     (or built-in fallback)
              |
              v
  +---------------------------+
  | Text-to-video             |
  |            or             |
  | Image generation/upload   |
  | -> image-to-video         |
  +---------------------------+
              |
              v
      MoviePy composition
              |
              v
 Voice-over, subtitles, transitions
              |
              v
       Downloadable MP4
```

## Requirements

- Python 3.9 or later
- A valid [Alibaba Cloud Model Studio](https://www.alibabacloud.com/en/product/model-studio) API key with access to the Wanxiang models
- FFmpeg for video and audio processing (`imageio-ffmpeg` is installed with the project; a system installation is recommended)
- Internet access to Alibaba Cloud Model Studio and Microsoft Edge TTS
- An OpenAI or OpenAI-compatible API key if you want AI-generated scripts

Video generation is a paid, asynchronous API operation and may take several minutes. Model availability, quotas, pricing, and supported resolutions can change on the provider side.

## Installation

Clone the repository and move into the application directory:

```bash
git clone <repository-url>
cd LUTANTAN/lu_tantan_vlog
```

Create and activate a virtual environment.

On Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

On macOS or Linux:

```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install the dependencies:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements_full.txt
```

Verify that FFmpeg is available:

```bash
ffmpeg -version
```

## Configuration

Create a `.env` file inside `lu_tantan_vlog` and configure the services you intend to use:

```dotenv
# Required for image and video generation
TONGYI_API_KEY=your_dashscope_api_key

# Optional: without this, the application uses a built-in sample script
OPENAI_API_KEY=your_openai_api_key
OPENAI_API_BASE=https://api.openai.com/v1
OPENAI_MODEL=gpt-4o

# Output settings
TTS_VOICE=zh-CN-YunxiNeural
VIDEO_FPS=24
VIDEO_HEIGHT=1080
VIDEO_CODEC=libx264
AUDIO_CODEC=aac
ASSETS_DIR=assets
```

`TONGYI_API_KEY` is required by the UI before generation can begin. `OPENAI_API_BASE` can point to an OpenAI-compatible endpoint.

Do not commit real API keys. If a key has ever been committed or shared, revoke it and create a replacement.

## Running the App

Run the launcher from the application directory:

```bash
python start.py
```

The launcher checks the basic environment and starts Streamlit at [http://localhost:8501](http://localhost:8501).

You can also start Streamlit directly:

```bash
python -m streamlit run main.py
```

## Usage

1. Enter a travel destination.
2. Choose either a travel guide or travel memory content type.
3. Select a script style.
4. Choose text-to-video or image-to-video generation.
5. For image-to-video, either let Wanxiang create the images or upload your own photos.
6. Select the output resolution and optional voice-over, subtitles, and transitions.
7. Use test mode for a single-scene trial, or start the full generation workflow.
8. Preview and download the finished MP4 from the Streamlit page.

Uploaded photos are temporarily stored under the configured assets directory and are sent to Alibaba Cloud Model Studio for image-to-video processing. Voice-over text is sent to Microsoft Edge TTS. Review the providers' privacy and data retention policies before using sensitive material.

## Supported Resolutions

| Layout | Resolution |
| --- | --- |
| Landscape 16:9 | 1920 x 1080 |
| Portrait 9:16 | 1080 x 1920 |
| Square 1:1 | 1440 x 1440 |
| Landscape | 1632 x 1248 |
| Portrait | 1248 x 1632 |
| Small landscape | 832 x 480 |
| Small portrait | 480 x 832 |
| Small square | 624 x 624 |

Actual resolution support is enforced by the selected Wanxiang model and may differ by account or API version.

## Project Structure

```text
LUTANTAN/
|-- README.md
`-- lu_tantan_vlog/
    |-- main.py                       # Streamlit application and workflow
    |-- start.py                      # Environment check and launcher
    |-- config.py                     # Environment-based configuration
    |-- ai_engine.py                  # Script generation and prompt processing
    |-- tongyi_wanxiang_engine.py     # Image/video generation and composition
    |-- audio_engine.py               # Edge TTS narration
    |-- subtitle_engine_v3.py         # Burned-in subtitle rendering
    |-- duration_calculator.py        # Narration-aware scene timing
    |-- script_styles.py              # Storytelling style definitions
    |-- ui_helpers.py                 # Streamlit UI helpers
    `-- requirements_full.txt         # Python dependencies
```

Generated files are written below `lu_tantan_vlog/assets` by default:

```text
assets/
|-- audio/
|-- images/
`-- output/
```

The final file is named `lu_tantan_<destination>.mp4`.

## Troubleshooting

### The Generate button reports that Wanxiang is not configured

Confirm that `.env` is in `lu_tantan_vlog`, contains `TONGYI_API_KEY`, and that the app was restarted after the file changed.

### Script generation uses sample content

This is expected when `OPENAI_API_KEY` is empty or when the configured model request fails. Check `OPENAI_API_BASE`, `OPENAI_MODEL`, credentials, and provider access.

### FFmpeg or encoding errors occur

Run `ffmpeg -version` in the same terminal used to start Streamlit. Also confirm that the configured `VIDEO_CODEC` and `AUDIO_CODEC` are supported by your FFmpeg build.

### Subtitle characters do not render correctly

Install a font with Chinese glyph support. The renderer checks common Microsoft YaHei and SimHei fonts on Windows, PingFang and Heiti on macOS, and DejaVu fonts on Linux.

### Generation times out or returns no media

Check the DashScope quota, model permissions, network access, and API service status. Test mode is useful for validating the setup with only one scene.

## Technology Stack

- Streamlit for the web interface
- OpenAI Python SDK for script generation
- Alibaba Cloud DashScope and Wanxiang for image and video generation
- Edge TTS for Chinese narration
- MoviePy, Pillow, and FFmpeg for media composition

## License

No license file is currently included. Unless a license is added, the source code remains subject to the default copyright restrictions.
