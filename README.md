# PathShift

This program was developed to clean up files, especially .jar files. It fixes the problem that Lobster _data is not automatically cleaned up when a new version is patched, as these files are used by another process.

## Features

- **Browse Files**: Browse and select log files (`.log`) and text files (`.txt`).
- **View File Content**: Display the content of the selected file in a text area.
- **Move Files**: Move files to a specified destination directory.
- **Check for Updates**: Check for the latest updates from GitHub releases.

## Installation

1. Clone the repository:
    ```sh
    git clone https://github.com/zaricj/FileMover.git
    ```

2. Navigate to the project directory:
    ```sh
    cd FileMover
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

## Usage

1. Run the application:
    ```sh
    python PathShift.py
    ```

2. Use the menu options to browse and select files, view file content, and move files.

## How to Use

![GUI Image](docs\image.png)

### 1. Browsing Files

- Click on the `Browse File` button to select a log file (`.log`) or text file (`.txt`).

### 2. Selecting Destination Path

- Click on the `Set Folder` button in order to select a folder path where the files should be moved to.

#### Viewing File Content

- The content of the selected file will be displayed in the text area.
- For log files, you can select a date from the combobox to filter and display log entries for that date.

### 3. Search Pattern

- Enter text which will filter the displayed content of the read file and match only lines that start like the inputted text.

### 4. Convert to Regex

- The `Convert to Regex` button converts the inputted text to a regular expression in order to find the lines that only match that pattern.

### 5. Search

- The `Search` button searches the file content which is displayed and re-display only found matches based on the regular expression.

![GIF 01](docs\gifs\01_PathShift_SearchFunction.gif)

### 6. Text to replace

- Use this input to replace text with the second input

### 7. Replace text with

- Enter text here which will replace the text from "Text to replace" input in the file content view.

### 8. Phrases to remove

- For cleaning up unwanted text and to leave only full paths to files, this input is comma-separated.

### 9. Apply the changes

- Press the `Apply` button to take over the changes based on the inputs.

![GIF 02](docs\gifs\02_PathShift_TextManiFunction.gif)

### Using Autofill option GIF (Quicker than manual input)

![GIF 03](docs\gifs\03_PathShift_AutoFillFunction.gif)

### 10. Move files

- Moved the files in the displayed file content view to the set destination path.

## Acknowledgements

- [PySide6](https://www.qt.io/qt-for-python) for providing the GUI framework.
- [GitHub API](https://docs.github.com/en/rest) for enabling update checks.

