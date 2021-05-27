# WRPI AUTO

The automated broadcast system for WRPI

## Dependencies

Recommended Python version >= 3.8.10

```bash
pip install -r requirements.txt
```

## Import Audios

All media used are stored in `lib/` under different category organized by folders. Here are some default ones:

```text
./lib/
    ├─fill
    ├─PSA
    ├─show
    │      show1.mp3
    │      show2.mp3
    │      show3.mp3
    │
    └─stationID
            brief.mp3
            long.mp3
```
You are free to add more categories.

## Run
```bash
python main.py
```
