# Fitness Heart Rate Analyzer

A tool to analyze and compare heart rate data from fitness files (.fit and .gpx formats).

## Features

- Supports both .fit and .gpx file formats
- Calculate average heart rate for specific time sections
- Compare heart rates between two sections
- Command-line interface for easy use

## Installation

1. Clone this repository
2. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

Run the analyzer from the command line:

```bash
python src/heart_rate_analyzer.py your_file.fit \
    --section1-start 00:10:00 \
    --section1-end 00:15:00 \
    --section2-start 00:30:00 \
    --section2-end 00:35:00
```

### Arguments

- `file_path`: Path to your .fit or .gpx file
- `--section1-start`: Start time for first section (format: HH:MM:SS)
- `--section1-end`: End time for first section (format: HH:MM:SS)
- `--section2-start`: Start time for second section (format: HH:MM:SS)
- `--section2-end`: End time for second section (format: HH:MM:SS)

## Example

```bash
python src/heart_rate_analyzer.py workout.fit \
    --section1-start 00:10:00 \
    --section1-end 00:15:00 \
    --section2-start 00:30:00 \
    --section2-end 00:35:00
```

This will compare the average heart rate between:
- Section 1: 10:00 - 10:15
- Section 2: 10:30 - 10:35

## Future Plans

- Web interface for easy file upload and analysis
- Support for more file formats
- Additional analysis features (e.g., heart rate zones, trends)
- Cloud storage integration 