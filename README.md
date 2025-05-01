# Monokakido to Yomitan Dictionary Converter

Convert Monokakido dictionary files to Yomitan format.

## Overview

This project provides tools to convert dictionaries from the Monokakido format to the Yomitan format. Currently supports the following dictionaries:

- 大辞泉
- 旺文社 全訳古語辞典
- 研究社 新和英大辞典 (Index files are corrupted as of now :/)
- 三省堂 全訳読解古語辞典
- 現代心理学辞典
- 角川新字源 改訂新版
- 南山堂医学大辞典 第20版
- 明鏡国語辞典 第三版
- 旺文社国語辞典 第十二版
- 漢字林
- 例解学習国語 第十二版

## Prerequisites

- Python 3.9+
- Required libraries (see `requirements.txt`)
- Monokakido dictionary files. No instructions will provided for extracting the raw dictionary data.

## Installation

1. Clone this repository:
   ```bash
   git clone https://github.com/kiwakiwaa/monokakido-to-yomitan.git
   cd monokakido-to-yomitan
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```


## Usage

1. Place the appropriate dictionary files in "assets" and "data".

2. Configure the dictionary you want to convert in `main.py`:
   ```python
   config_to_process = "daijisen"
   ```

3. Run the conversion script:
   ```bash
   python src/main.py
   ```

4. The converted dictionary will be saved in the `converted` directory.

## Supported Dictionaries

| Dictionary | Type | Status |
|------------|------|--------|
| 大辞泉 | Daijisen | ✅ Supported |
| 旺文社 全訳古語辞典 | OZK5 | ✅ Supported |
| 研究社 新和英大辞典 | KNJE | WIP |
| 三省堂 全訳読解古語辞典 | SKOGO | ✅ Supported |
| 現代心理学辞典 | YDP | ✅ Supported |
| 角川新字源 改訂新版 | SHINJIGEN2 | ✅ Supported (MDX) |
| 南山堂医学大辞典 第20版 | NANMED20 | ✅ Supported (SQL) |
| 明鏡国語辞典 第三版 | MK3 | ✅ Supported |
| 旺文社国語辞典 第十二版 | OKO12 | ✅ Supported |
| 漢字林 | TISMKANJI | ✅ Supported |
| 例解学習国語 第十二版 | RGKO12 | ✅ Supported |

## Directory Structure

- `/parser` - Contains parser classes for each dictionary
- `/utils` - Utility functions for file handling, jp processing, etc.
- `/config` - Configuration classes for dictionaries and paths
- `/index` - Index reader classes for dictionary lookup

## How It Works

The conversion process involves:

1. Reading the extracted dictionary XML files
2. Parsing the entries and their structures
3. Converting the content to Yomitan's format
4. Packaging everything into a zip that Yomitan can import

Each dictionary type has its own specialised parser that handles the unique structure and features of that dictionary.

## Adding a New Dictionary

To add support for a new dictionary:

1. Create a new parser in the `/parser` directory
2. Define the tag mappings for HTML conversion
3. Implement any special handling for links, images, etc.
4. Add the dictionary configuration to the `dictionary_configs` in `main.py`
5. Use the original css as reference to add styling.
