# WRPI AUTO

The automated broadcast system for WRPI

## Deployment

Recommended Python version >= 3.8.10

### Python Modules

```bash
pip install -r requirements.txt
```

### ffmpeg

Recommended ffmpeg version 4.4

Go [http://ffmpeg.org/download.html](http://ffmpeg.org/download.html) to download compiled excutable for the specific platform. Then copy it to `bin/`. See example directory structure below.

### Import Media

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
└─modules       // program modules
```

## Run
```bash
python main.py
```

## TODO

- Email alert
- Text UI