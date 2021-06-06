# WRPI AUTO

The broadcast automation system for WRPI or general broadcast station. Features include:

- Automated station ID
- Programmable show schedule
- Loudness normalization (EBU R 128)
- Text user interface and headless mode
- Station logging
- Email alert

## Deployment

### 0. Python

Recommended Python version >= 3.8.10

### 1. Python Modules

Windows:

```bash
pip install -r windows-requirements.txt
```

Unix:

```bash
pip install -r requirements.txt
```

### 2. ffmpeg & ffprobe

`ffmpeg` and `ffprobe` are used for media processing (i.e. loudness normalization) and metadata extraction. Recommended ffmpeg version 4.4, but for 32-bit Windows platform only some earlier version builts are available. Version 4.3.1 was tested to work on 32-bit Windows.

Go [http://ffmpeg.org/download.html](http://ffmpeg.org/download.html) to download compiled excutables for the specific platform. Then copy them to `bin/`. See example directory structure below.

### 3. Station Configuration

Create a copy from `modules/sample-config.py`. Rename the copy to `modules/config.py`.
Then modify configs in `modules/config.py` such as station name, audio loudness and quality, SMTP etc.

### 4. Import Media

All media used are stored in `lib/` under different category organized by folders. Here are some default ones:

- stationID
- show
- PSA
- fill

You are free to add more categories.

### Directory Structure

This is an example directory structure on Windows.

```text
./
│   db.json     // database
│   main.py     // program entry
│   WRPI.log    // log file
│
├─bin           // external binaries
│   ffmpeg.exe  // for audio processing
|   ffprobe.exe
│
├─lib           // sound library
│  ├─fill
│  ├─PSA
│  ├─show
│  │    show1.mp3
│  │    show2.mp3
│  │    show3.mp3
│  │
│  └─stationID
│          brief.mp3
│          long.mp3
│
├─log           // log files
│   WRPI.2021-06-06.log
│
└─modules       // program modules
```

## Run

For text user interface (TUI):

```bash
python main.py
```

Headless mode (no UI, no control):
```bash
python main.py --headless
```

Use `-h` for help.

## User Mannual

- Set cart computer (this software runs on) system volume to 100%.
- Set physical mixer channel (e.g. cart channel) to 100% (0dB)

