---
title: WRPI-auto User Manual
author: Hisen Zhang
header: ${title}  -  Exported on ${today}
footer: Page ${pageNo} / ${pageCount}
---

# User Manual

This manual is for user reference. For more details about this software, please refer to programming manual in `doc/` folder.

**Table of Contents**

<!-- vscode-markdown-toc -->
* [Before starting](#Beforestarting)
	* [Logging levels](#Logginglevels)
* [Deployment](#Deployment)
	* [Install Python Environment](#InstallPythonEnvironment)
	* [Install Python Modules](#InstallPythonModules)
	* [Acquire ffmpeg & ffprobe](#Acquireffmpegffprobe)
	* [Configure Station](#ConfigureStation)
	* [Import Media](#ImportMedia)
	* [Directory Structure](#DirectoryStructure)
* [Start](#Start)
	* [Preparation](#Preparation)
	* [Run](#Run)
* [User Interface](#UserInterface)
	* [TUI](#TUI)
		* [Display](#Display)
		* [Key binds](#Keybinds)

<!-- vscode-markdown-toc-config
	numbering=false
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

## <a name='Beforestarting'></a>Before starting

Here are some important things to know before starting this software.

### <a name='Logginglevels'></a>Logging levels

Severity increases down the list.

- `DEBUG` Very detailed level of output for program debugging & diagnostic purpose.
- `INFO` Regular information for station logs. **Default level of output.**
- `WARNING` Program foresees a issue may result in abnormality. 
  - Will trigger **Discord alert** and **need manual intervention** on (and beyond) this level.
- `ERROR` Program can't recover from the issue by itself, but may still proceed.
  - Will trigger **email alert**
- `CRITICAL` Unrecoverable issue. Program halts immediately.

## <a name='Deployment'></a>Deployment

### <a name='InstallPythonEnvironment'></a>Install Python Environment

Visit [www.python.org](https://www.python.org/) to download installer matching your system platform.
Recommended Python version >= 3.8.10

### <a name='InstallPythonModules'></a>Install Python Modules

On Windows run the following script:

```bash
pip install -r windows-requirements.txt
```

or if using Unix:

```bash
pip install -r requirements.txt
```

### <a name='Acquireffmpegffprobe'></a>Acquire ffmpeg & ffprobe

`ffmpeg` and `ffprobe` are used for media processing (i.e. loudness normalization) and metadata extraction. Recommended ffmpeg version 4.4, but for 32-bit Windows platform only some earlier version builds are available. Version 4.3.1 was tested to work on 32-bit Windows.

Go [ffmpeg.org](http://ffmpeg.org/download.html) to download compiled executables (not source!) for the specific platform. Then copy them to `bin/`. **If such path doesn't exist, create one.** See example [directory structure](#Directory-Structure) below. 

### <a name='ConfigureStation'></a>Configure Station

Create a copy from `doc/sample-config.yml` to the side of `main.py` in the project base directory. Rename this copy to `config.yml`. Then modify items in `config.yml` such as station name, audio loudness and quality, SMTP etc. Follow the comments in the file.

### <a name='ImportMedia'></a>Import Media

All media used are stored in `lib/` under different category organized by folders. Here are some default ones:

- stationID
- show
- PSA
- fill

Customization allows more categories, which is configurable in the config file. Remember to create a folder of the same name under `lib/`.

<div style="page-break-after: always; break-after: page;"></div>

### <a name='DirectoryStructure'></a>Directory Structure

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

## <a name='Start'></a>Start

### <a name='Preparation'></a>Preparation

- Set cart computer (where this software runs on) system volume to 100%.
- Set physical mixer channel (i.e. cart channel) to 100% (0dB)
- Start the program. Refer to section [Run](#Run).

### <a name='Run'></a>Run

This software runs in two modes:

**Text User Interface (TUI)**

- Default mode
  - preferred if the hardware system has a terminal (i.e. monitor and keyboard) 
- Full user control
  - Volume, mute, pause, etc.
- Use slightly more hardware resource than headless mode.

**Headless mode**

- For compromised hardware environment
  - Raspberry Pi
  - Servers
- Less hardware resource consumption.

To start with TUI:

```bash
python main.py
```

Headless mode (no UI, no control):
```bash
python main.py --headless
```

Use flag `-h` for help.

## <a name='UserInterface'></a>User Interface

User control is all accomplished in Text User Interface, also known as TUI.

### <a name='TUI'></a>TUI

TUI stands for Text User Interface. TUI has two core functions:

- Display important information, such as
  - Media queue
  - Logging
  - System statistics
- Accepts user input through key binds, for
  - Play control

Below is a screenshot of TUI.

![TUI example](https://i.imgur.com/Ed6osFC.png)

#### <a name='Display'></a>Display

The entire screen splits into four widgets:

- Media Queue
- Now Playing
- System Statistics
- Station Log

Besides above listed, root window always resides in the back.

- Press `ESC` to defocus from any widget. 
- Use arrow keys to navigate among widgets. The selected widget has broader highlighted.
- Press `ENTER` to focus on the selected widget.

**Each widget has its own key binds.** The key binds applies only when it's on focus. To select root window, defocus from any widget.

The following sections introduce each widget.

##### <a name='MediaQueue'></a>Media Queue

```text
+-- Media Queue (5) [0:10:00 / 0:21:59] ----------+
|   1. [0:08:16] lib\show\Bossa Antigua.mp3       |
|   2. [0:03:44] lib\show\Let's Get Lost.m4a *    |
|   3. [0:02:22] lib\show\My Funny Valentine.mp3  |
|   4. [0:04:37] lib\show\O Gato.mp3              |
|   5. [0:03:02] lib\show\Someone to Watch Over M |
|                                                 |
+-------------------------------------------------+
```
Media Queue shows the current playlist. The widget title has the format:

`Media Queue` (`Total items`) [`Remaining length` / `Total length`]

Where in the example above, the total number of audio in queue is 5, and takes 21 minutes 59 seconds to play all of them. All time code has `H:MM:SS` format.

The piece playing now (No. 2 *Let's get Lost*) has green highlights with star `*` in the end of line. `Remaining length` sums starting from the third piece to the end.

Each item has the format:

`Ordering number` [`Length`] `path-to-audio`

##### <a name='NowPlaying'></a>Now Playing

```text
+-- Now Playing ----------------------------------+
| [ show ] (100%) lib\show\Let's Get Lost.m4a     |
| [ fill ] (100%) <empty>                         |
| [ PSA  ] (100%) <empty>                         |
|                                                 |
+-------------------------------------------------+
```

A summary of mixer status. Each line represents a channel, having format:

[`channel`] (`volume`) `path-to-audio`

##### <a name='SystemStatistics'></a>System Statistics

```text
+-- System Statitics -----------------------------+
| [ CPU ] (  6%)                                  |
| [ RAM ] ( 81%) free:    1.5 GiB total:    8.0 G |
| [ STR ] ( 38%) free:  318.9 GiB total:  512.0 G |
| [ PWR ] (100%)                                  |
|                                                 |
+-------------------------------------------------+
```

A summary of system resources is listed here. Refresh interval is configurable in `schedule` section.

- `CPU` Central processing unit load.
- `RAM` System virtual memory usage. The total includes physical and swap space.
- `STR` Disk usage of the partition that this software runs on.
- `PWR` System power supply. If system is battery powered and plugged into AC outlet, the line will indicate `CHARGING`.

##### <a name='StationLog'></a>Station Log

```text
+-- Station Log -----------------------------------------------------------+
| 2021-06-25 00:15:07,659 - Daemon     [INFO] Scheduler started.           |
| 2021-06-25 00:15:07,660 - TUI        [INFO] TUI starting...              |
| 2021-06-25 00:15:10,504 - TUI        [INFO] Playing "lib\show\Bossa Anti |
| 2021-06-25 00:15:24,362 - TUI        [INFO] Playing "lib\show\Let's Get  |
| 2021-06-25 00:19:08,223 - TUI        [INFO] Playing "lib\show\My Funny V |
| 2021-06-25 00:19:30,000 - Daemon     [INFO] Mixer digest: [show]  (100%) |
| 2021-06-25 00:21:30,614 - TUI        [INFO] Playing "lib\show\O Gato.mp3 |
|                                                                          |
+--------------------------------------------------------------------------+
```

This is a copy of log you will find in the log folder on the screen. Severity highlights use different colors, with following mapping:

| Logging Level | Color   |
|---------------|---------|
| DEBUG         | Blue    |
| INFO          | Green   |
| WARNING       | Yellow  |
| ERROR         | Red     |
| CRITICAL      | Magenta |

For persistent log files, checkout `log/`.

#### <a name='Keybinds'></a>Key binds

Remember, **Each widget has its own key binds.** For example, key binds in Media Queue is different from that in Station Log, nor it extends root window's.

**Key binds are case sensitive.**

Here's a reference sheet for all key binds (mnemonic in parentheses):

##### <a name='Global'></a>Global

- `ESC` defocus from the current widget

##### <a name='RootWindow'></a>Root Window

Switch focus:

- `q` focus on Widget `Media Queue`
- `l` focus on Widget `Station Log`
- `r` focus on Widget `System Statistics` (system **r**esources)

Play control:

- `i` Play station ID immediately
- `m` Mute
- `M` Unmute
- `p` Pause
- `P` Resume (un**P**ause)
- `n` Play next
- `ctrl+UP` Volume up 10%
- `ctrl+DOWN` Volume down 10% (temporarily)

Miscellaneous:

- `ctrl+Q` quit this software
- `h` help screen

##### <a name='MediaQueue'></a>Media Queue

- `UP` Select previous item
- `DOWN` Select next item
- `PAGE UP`	Move selected item up
- `PAGE DOWN` Move selected item down
- `HOME` Move selected item to the top of queue
- `END` Move selected item to the end of queue

##### <a name='NowPlaying'></a>Now Playing

< empty >

##### <a name='SystemStatistics'></a>System Statistics

< empty >

##### <a name='StationLog'></a>Station Log

< empty >
