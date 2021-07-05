# Programming Manual

This manual is for programmers reference. For usage/operation, please refer to user manual in `doc/` folder.

**Table of Contents**

<!-- vscode-markdown-toc -->
* [General Design Goals](#GeneralDesignGoals)
* [Developing Environment](#DevelopingEnvironment)
	* [Python](#Python)
	* [Module Dependencies](#ModuleDependencies)
	* [Tools](#Tools)
		* [IDE](#IDE)
		* [Doc Rendering](#DocRendering)
* [Code Structure](#CodeStructure)
* [Core Classes](#CoreClasses)
* [Doc Writing](#DocWriting)
	* [User Manual](#UserManual)
	* [Programming Manual](#ProgrammingManual)
* [Unit Test](#UnitTest)

<!-- vscode-markdown-toc-config
	numbering=false
	autoSave=true
	/vscode-markdown-toc-config -->
<!-- /vscode-markdown-toc -->

## <a name='GeneralDesignGoals'></a>General Design Goals

1. High service availability
    - Audio service shall never stop unless intended
2. Low hardware requirement
    - Use as less hardware resource as possible
3. High accessibility
    - Available across platforms
    - Ease of use

## <a name='DevelopingEnvironment'></a>Developing Environment

This software is written mainly in Python 3. Some functions were implemented by calling external binaries, namely ffmpeg.

### <a name='Python'></a>Python

The prototype was developed under Python version 3.8.10

### <a name='ModuleDependencies'></a>Module Dependencies

Python module dependencies are listed in `requirements.txt`. Note that TUI is based on ncurses, which is only available on Unix; thus on Windows there are extra modules to include. Checkout `windows-requirements.txt`.

### <a name='Tools'></a>Tools

#### Code Browser

Use SourceTrail to visualize call/use graph to better understand how modules interact with each other.

#### <a name='IDE'></a>IDE

It is recommended to use Visual Studio Code as IDE for this software. Some handy extensions are listed below:

#### <a name='DocRendering'></a>Doc Rendering

Docs are written in markdown. To generate PDF, use Typora. Here's the [website](https://typora.io/).

## <a name='CodeStructure'></a>Code Structure

This software adopted Model-View-Controller structure:

1. Model: Play control
2. View: TUI (optional, may run in headless mode)
3. Controller: Station manager

TUI displays status and forwards key binds input commands from user, then these commands apply via station manager, and finally results in audio play control.

## <a name='CoreClasses'></a>Core Classes

## <a name='DocWriting'></a>Doc Writing

### <a name='UserManual'></a>User Manual

User manual aims at general audience without non-technical background. It should be available for both online access and physical access - that says, keep a printed copy in studio as well.

To generate printable PDF, use Typora with customized stylesheet. The customized stylesheet is based on builtin theme `pixyll` with a few improvement:

- border for \<code> tags
- paper size changed to US letter (you may need to adjust this per your locale)
- page break before secondary headings

To apply those customization, copy `doc/manual/pixyll.user.css` to Typora theme folder. Restart Typora and now this stylesheet applies.

### <a name='ProgrammingManual'></a>Programming Manual

The manual you are reading right now is written for technician; Programming manual includes program design rules, code organization, and miscellaneous information for maintenance.

Code specific comments comes within the code base.

## <a name='UnitTest'></a>Unit Test

This software use Python's standard unittest framework.

Each class should have a independent test file named `test_*.py`, include a test case named `Test[ClassName]`. Each test has function name `test_*`.

Take `util.conversion` as an example:

```python
# filename: test_conversion.py
import unittest
from modules.util import conversion


class TestFloatToHMS(unittest.TestCase):

    def setUp(self):
        self.secondsPerDay = 86400

    def test_zero(self):
        assert conversion.floatToHMS(0.0) == "0:00:00"

    def test_positive(self):
        assert conversion.floatToHMS(60.0) == "0:01:00"

    def test_negative(self):
        try:
            conversion.floatToHMS(-60.0)
        except ValueError as e:
            assert str(e) == "Duration must be non-negative"

    def test_big(self):
        assert conversion.floatToHMS(self.secondsPerDay-1) == "23:59:59"

    def test_hour_3_digits(self):
        secondsIn100Hours = 360000
        assert conversion.floatToHMS(secondsIn100Hours) == "100:00:00"
```