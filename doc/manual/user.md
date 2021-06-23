# User Manual

This manual is for users. For more datails about this software please refer to programming manual in `doc/` folder.

## Before starting

Here are some important things to know before starting this software.

### Logging levels: What do they mean?

Severity increases down the list.

- `DEBUG` Very detailed level of output for program debugging & diagnostic purpose.
- `INFO` Regular information for station logs. **Default level of output.**
- `WARNING` Program foresees a issue may result in abnormality. 
  - Will trigger **email alert** and **need manual intervention** on (and beyond) this level.
- `ERROR` Program can't recover from the issue by itself, but may still proceed.
- `CRITICAL` Unrecoverable issue. Program halts immediately.

## Deployment

### Python Environment

Recommended Python version >= 3.8.10

### Python Modules

Windows:

```bash
pip install -r windows-requirements.txt
```

Unix:

```bash
pip install -r requirements.txt
```

### ffmpeg & ffprobe

`ffmpeg` and `ffprobe` are used for media processing (i.e. loudness normalization) and metadata extraction. Recommended ffmpeg version 4.4, but for 32-bit Windows platform only some earlier version builts are available. Version 4.3.1 was tested to work on 32-bit Windows.

Go [ffmpeg.org](http://ffmpeg.org/download.html) to download compiled excutables (not source!) for the specific platform. Then copy them to `bin/`. **If such path doesn't exist, create one.** See example [directory structure](#Directory-Structure) below. 

### Station Configuration

Create a copy from `doc/sample-config.py` to the side of `main.py` in the project base directory. Rename the copy to `config.py`. Then modify configs in `config.py` such as station name, audio loudness and quality, SMTP etc. Follow the comments in the code.

### Import Media

All media used are stored in `lib/` under different category organized by folders. Here are some default ones:

- stationID
- show
- PSA
- fill

You are free to add more categories.

### Directory Structure

This is an example directory structure on Windows. Some files are ignored 

```text
./
│   db.json     // database (program generated)
│   main.py     // program entry
│
├─bin           // external binaries
│   ffmpeg.exe  // for audio processing
|   ffprobe.exe
│
├─doc           // documentation
│   sample.config.yml   // sample config file
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

## Start

### Preparation

- Set cart computer (this software runs on) system volume to 100%.
- Set physical mixer channel (e.g. cart channel) to 100% (0dB)
- Start the program. Refer to section [Run](#Run).

### Run

This software runs in two modes:

- Text User Interface (TUI)
  - Default mode
    - preferred if the hardware system has a terminal (i.e. monitor and keyboard) 
  - Full user control
    - Volume, mute, pause, etc.
  - Use slightly more hardware resource than headless mode.
- Headless mode
  - For compromised hardware environment
    - Raspberry Pi
    - Servers
  - Less hardware resource consumption.

To start:

```bash
python main.py
```

Headless mode (no UI, no control):
```bash
python main.py --headless
```

Use flag `-h` for help.

## Control

### TUI

                