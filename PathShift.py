import os
import re
import shutil
import subprocess
import sys
import webbrowser
import py7zr
import requests
from datetime import datetime
from pathlib import Path
from PySide6.QtCore import QFile, QSettings, QTextStream
from PySide6.QtGui import QAction, QCloseEvent, QIcon, QTextOption
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFileDialog,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QStatusBar,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)


# Regex Generator class to convert string to regex pattern
class RegexGenerator:
    def __init__(self, string_pattern_to_detect):
        self.string_pattern_to_detect = string_pattern_to_detect
        self.regex_string = ""
        self.special_chars = ".^$*+?{}[]\\|()"
        self.create_regex()

    def create_regex(self):
        if not self.string_pattern_to_detect:
            return

        # Add start anchor if needed
        # self.regex_string = "^"  # Uncomment if you want to match from start of line

        pattern_chunks = []
        current_chunk = []
        current_type = self.determine_char_type(self.string_pattern_to_detect[0])

        # Process characters in groups
        for char in self.string_pattern_to_detect:
            char_type = self.determine_char_type(char)
            
            # For exact word matching, treat each character as special
            if char_type == "CHARACTER":
                if current_chunk and current_type != "CHARACTER":
                    pattern_chunks.append((current_type, "".join(current_chunk)))
                    current_chunk = []
                current_chunk.append(char)
                current_type = char_type
            else:
                if current_chunk:
                    pattern_chunks.append((current_type, "".join(current_chunk)))
                pattern_chunks.append((char_type, char))
                current_chunk = []
                current_type = char_type

        # Add the last chunk
        if current_chunk:
            pattern_chunks.append((current_type, "".join(current_chunk)))

        # Convert chunks to regex
        for chunk_type, chunk_content in pattern_chunks:
            if chunk_type == "SPECIAL":
                if chunk_content in self.special_chars:
                    self.regex_string += f"\\{chunk_content}"
                else:
                    self.regex_string += f"{chunk_content}"
            elif chunk_type == "CHARACTER":
                # For exact word matching
                self.regex_string += f"({chunk_content})"
            else:
                pattern = self.get_pattern_for_type(chunk_type)
                if len(chunk_content) > 1:
                    self.regex_string += f"{pattern}{{{len(chunk_content)}}}"
                else:
                    self.regex_string += pattern

        # Add end anchor if needed
        # self.regex_string += "$"  # Uncomment if you want to match to end of line

    def get_pattern_for_type(self, char_type):
        patterns = {
            "DIGIT": "\\d",
            "CHARACTER": "[a-zA-Z]",
            "WHITESPACE": "\\s",
            "SPECIAL": ""
        }
        return patterns.get(char_type, "")

    def determine_char_type(self, char):
        if char.isnumeric():
            return "DIGIT"
        elif char.isalpha():
            return "CHARACTER"
        elif char.isspace():
            return "WHITESPACE"
        else:
            return "SPECIAL"

    def get_regex(self):
        return self.regex_string

    def check_if_valid(self):
        import re
        try:
            re.compile(self.regex_string)
            return True
        except re.error:
            return False

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Initializing current working director and theme file(s)
        self.current_working_dir = os.getcwd()
        self.refresh_icon = QIcon("_internal\\icon\\refresh.svg")
        theme_file_path = os.path.join(self.current_working_dir,"_internal","theme_files")
        dark_theme_file = os.path.join(theme_file_path,"dark.qss")
        self.version = "1.1.3" # Current version of the application
        self.settings = QSettings("Application", "Name") # Settings to save current location of the windows on exit
        geometry = self.settings.value("geometry", bytes())
        icon = QIcon("_internal\\icon\\app.ico")
        self.restoreGeometry(geometry)
        self.initialize_theme(dark_theme_file)
        self.setWindowIcon(icon)
        self.initUI()
        self.setWindowTitle(f"PathShift v{self.version} © - by Jovan")
        self.create_menu_bar()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)  # Main layout is horizontal
        
        # Status Bar
        self.statusbar = QStatusBar()
        self.statusbar.setSizeGripEnabled(False)
        self.statusbar.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)

        # Left Panel - Controls
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        # File Operations Panel
        file_ops_group = QGroupBox("File Operations")
        file_ops_group.setMinimumWidth(550)
        file_ops_layout = QVBoxLayout()

        # Input file selection with icon
        file_input_layout = QHBoxLayout()
        self.file_path_input = QLineEdit()
        self.file_path_input.setPlaceholderText("Select a text or log file to read and display it's content...")
        self.file_path_input.setReadOnly(False)
        self.file_path_input.textChanged.connect(lambda: self.refresh_icon_button.setVisible(True) if os.path.isfile(self.file_path_input.text()) else self.refresh_icon_button.setVisible(False))
        self.browse_button = QPushButton("Browse File")
        self.browse_button.clicked.connect(self.browse_file)
        self.refresh_icon_button = QPushButton()
        self.refresh_icon_button.setIcon(self.refresh_icon)
        self.refresh_icon_button.setToolTip("Refresh the file content view.")
        self.refresh_icon_button.setVisible(False)
        self.refresh_icon_button.clicked.connect(self.refresh_file_content)
        file_input_layout.addWidget(self.file_path_input)
        file_input_layout.addWidget(self.browse_button)
        file_input_layout.addWidget(self.refresh_icon_button)

        # Destination selection with icon
        dest_input_layout = QHBoxLayout()
        self.destination_input = QLineEdit()
        self.destination_input.setPlaceholderText("Select destination directory where the files should be moved to...")
        self.destination_input.setReadOnly(False)
        self.set_folder_button = QPushButton("Set Folder")
        self.set_folder_button.clicked.connect(self.browse_folder)
        dest_input_layout.addWidget(self.destination_input)
        dest_input_layout.addWidget(self.set_folder_button)

        # Action buttons
        action_layout = QHBoxLayout()
        self.move_button = QPushButton("Move Files")
        self.move_button.setToolTip("If the file content view contains full file paths in each new line\nthen it moves those listed files to the set destination directory.")
        self.move_button.clicked.connect(self.move_files)
        
        action_layout.addWidget(self.move_button)
        #action_layout.addStretch()

        file_ops_layout.addLayout(file_input_layout)
        file_ops_layout.addLayout(dest_input_layout)
        file_ops_layout.addLayout(action_layout)
        file_ops_group.setLayout(file_ops_layout)
        
        # Search and Manipulation Panel
        search_group = QGroupBox("Search and Manipulation")
        search_group.setMinimumWidth(550)
        search_layout = QVBoxLayout()

        # Pattern search
        pattern_layout = QVBoxLayout()
        pattern_header = QHBoxLayout()
        pattern_header.addWidget(QLabel("Search Pattern:"))
        self.regex_pattern_input = QLineEdit()
        self.regex_pattern_input.setPlaceholderText("Enter text to convert to regex pattern which is used to search the displayed file content...")
        self.regex_pattern_input.setToolTip("Enter a regex pattern to search for in the displayed file content.")
        self.regex_pattern_input.setClearButtonEnabled(True)
        
        pattern_buttons = QHBoxLayout()
        self.convert_entered_string_to_regex_button = QPushButton("Convert to Regex")
        self.convert_entered_string_to_regex_button.setToolTip("Convert the entered string to a regex pattern.")
        self.convert_entered_string_to_regex_button.clicked.connect(self.generate_regex)
        self.search_file_contents_and_display_button = QPushButton("Search")
        self.search_file_contents_and_display_button.setToolTip("Search the displayed file content for the entered regex pattern and display only those matches.")
        self.search_file_contents_and_display_button.clicked.connect(self.search_and_replace_file_content)
        pattern_buttons.addWidget(self.convert_entered_string_to_regex_button)
        pattern_buttons.addWidget(self.search_file_contents_and_display_button)
        
        pattern_layout.addLayout(pattern_header)
        pattern_layout.addWidget(self.regex_pattern_input)
        pattern_layout.addLayout(pattern_buttons)

        # Text manipulation
        manipulation_layout = QVBoxLayout()
        
        find_layout = QVBoxLayout()
        find_layout.addWidget(QLabel("Find text to replace:"))
        self.find_string_input = QLineEdit()
        self.find_string_input.setPlaceholderText("Enter text to replace (e.g., ./lib/)")
        self.find_string_input.setToolTip("Enter the text to find which will be replaced later in the displayed file content.\nExample: ./lib/")
        self.find_string_input.setClearButtonEnabled(True)
        find_layout.addWidget(self.find_string_input)

        replace_layout = QVBoxLayout()
        replace_layout.addWidget(QLabel("Replace text with:"))
        self.change_path_separator_button = QPushButton("Switch Path Separator")
        self.change_path_separator_button.setVisible(False)
        self.change_path_separator_button.clicked.connect(self.change_path_separator)
        self.replace_string_input = QLineEdit()
        self.replace_string_input.setPlaceholderText("Replace text in file content with (e.g., D:/Lobster_data/lib/)")
        self.replace_string_input.setToolTip("Enter the text to replace the found text within the displayed file content.\nExample: D:/Lobster_data/lib/")
        self.replace_string_input.setClearButtonEnabled(True)
        self.replace_string_input.textChanged.connect(self.enable_change_path_separator_button)
        replace_layout.addWidget(self.replace_string_input)
        replace_layout.addWidget(self.change_path_separator_button)

        remove_layout = QVBoxLayout()
        remove_layout.addWidget(QLabel("Remove phrases (comma-separated):"))
        self.phrase_to_remove_input = QLineEdit()
        self.phrase_to_remove_input.setPlaceholderText("Enter phrases to remove (e.g., Marking file, to be deleted on exit of JVM)")
        self.phrase_to_remove_input.setToolTip("Enter phrases to remove from the displayed file content.\nCan be comma-separated (eg., Marking file, to be deleted on exit of JVM).")
        self.phrase_to_remove_input.setClearButtonEnabled(True)
        remove_layout.addWidget(self.phrase_to_remove_input)

        self.apply_button = QPushButton("Apply Changes")
        self.apply_button.setToolTip("Apply the changes to the displayed file content.")
        self.apply_button.clicked.connect(self.apply_and_replace_file_content)
        
        manipulation_layout.addLayout(find_layout)
        manipulation_layout.addLayout(replace_layout)
        manipulation_layout.addLayout(remove_layout)
        manipulation_layout.addWidget(self.apply_button)

        search_layout.addLayout(pattern_layout)
        search_layout.addSpacing(10)
        search_layout.addLayout(manipulation_layout)
        search_group.setLayout(search_layout)

        # Add panels to left layout
        left_layout.addWidget(file_ops_group)
        left_layout.addWidget(search_group)
        left_layout.addStretch()

        # Right Panel - Content Views
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)

        # File Content View
        content_group = QGroupBox("File Content")
        content_layout = QVBoxLayout()

        content_toolbar = QHBoxLayout()
        self.log_dates_combobox = QComboBox()
        self.log_dates_combobox.setToolTip("Select a date to view the log entries for that date.\nThis will re-display the log entries for the selected date in the file view.")
        self.log_dates_combobox.setMinimumWidth(120)
        self.log_dates_combobox.currentTextChanged.connect(lambda: self.extract_lines_by_date_and_display(
            self.extract_data_from_log(self.file_path_input.text()), 
            self.log_dates_combobox.currentText()
        ))
        self.font_size_combobox_file_contents = QComboBox()
        self.font_size_combobox_file_contents.addItems(["10px","11px","12px", "14px", "16px", "18px", "20px"])
        self.font_size_combobox_file_contents.setCurrentIndex(2)
        self.font_size_combobox_file_contents.currentIndexChanged.connect(lambda: self.file_content_display.setStyleSheet(
            f"font-size: {self.font_size_combobox_file_contents.currentText()}"))
        self.font_size_combobox_file_contents.setMinimumWidth(60)
        
        self.font_size_combobox_output = QComboBox()
        self.font_size_combobox_output.addItems(["10px","11px","12px", "14px", "16px", "18px", "20px"])
        self.font_size_combobox_output.setCurrentIndex(2)
        self.font_size_combobox_output.currentIndexChanged.connect(lambda: self.program_output.setStyleSheet(
            f"font-size: {self.font_size_combobox_output.currentText()}"))
        self.font_size_combobox_output.setMinimumWidth(60)
        
        content_toolbar.addWidget(QLabel("Log Date:"))
        content_toolbar.addWidget(self.log_dates_combobox)
        content_toolbar.addSpacing(20)
        content_toolbar.addWidget(QLabel("Font Size:"))
        content_toolbar.addWidget(self.font_size_combobox_file_contents)
        content_toolbar.addSpacing(20)
        content_toolbar.addWidget(QLabel("Status:"))
        content_toolbar.addWidget(self.statusbar)
        #content_toolbar.addStretch()

        self.file_content_display = QTextEdit()
        self.file_content_display.setReadOnly(False)
        self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)
        self.file_content_display.undoAvailable
        
        # Progressbar
        self.progressbar = QProgressBar()
        self.progressbar.setMaximumHeight(15)
        self.progressbar.setMinimumWidth(260)
        self.progressbar.setVisible(False)
        
        # Statusbar line count
        self.line_count_statusbar = QStatusBar()
        self.line_count_statusbar.setSizeGripEnabled(False)
        self.line_count_statusbar.setStyleSheet("color: #ffffff; font-size: 14px")
        self.file_content_display.cursorPositionChanged.connect(lambda: self.line_count_statusbar.showMessage(f"Line: {self.file_content_display.textCursor().blockNumber() + 1}", 10000))
        content_layout.addLayout(content_toolbar)
        content_layout.addWidget(self.file_content_display)
        content_layout.addWidget(self.line_count_statusbar)
        content_group.setLayout(content_layout)

        # Program Output
        output_group = QGroupBox("Program Output")
        output_layout = QVBoxLayout()

        output_toolbar = QHBoxLayout()
        output_toolbar.addWidget(QLabel("Font Size:"))
        output_toolbar.addWidget(self.font_size_combobox_output)
        output_toolbar.addSpacing(10)
        output_toolbar.addWidget(QPushButton("Clear Output", clicked=lambda: self.program_output.clear()))
        output_toolbar.addSpacing(10)
        output_toolbar.addWidget(self.progressbar)
        output_toolbar.addStretch()

        self.program_output = QTextEdit()
        self.program_output.setReadOnly(True)
        self.program_output.setWordWrapMode(QTextOption.ManualWrap)
        
        output_layout.addLayout(output_toolbar)
        output_layout.addWidget(self.program_output)
        output_group.setLayout(output_layout)

        # Add views to right layout
        right_layout.addWidget(content_group, stretch=2)
        left_layout.addWidget(output_group, stretch=1)

        # Set up main layout
        main_layout.addWidget(left_panel, stretch=1)
        main_layout.addWidget(right_panel, stretch=2)

        # Set central widget
        self.setCentralWidget(central_widget)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Clear Program output
        clear_action = QAction("Clear Program Output", self)
        clear_action.triggered.connect(lambda: self.program_output.clear())
        file_menu.addAction(clear_action)

        file_menu.addSeparator()

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        
        # Open Menu
        open_menu = menubar.addMenu("&Open")
        
        open_csv_folder = QAction("Open Destination Folder", self)
        open_csv_folder.triggered.connect(lambda: self.open_folder_helper_method(self.destination_input.text()))
        open_menu.addAction(open_csv_folder)
        
        open_file = QAction("Open Input File", self)
        open_file.triggered.connect(lambda: self.open_file_helper_method(self.file_path_input.text()))
        open_menu.addAction(open_file)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        self.change_word_wrap_action = QAction("Toggle Word Wrap", self)
        self.change_word_wrap_action.setCheckable(True)
        self.change_word_wrap_action.setChecked(True)

        self.change_word_wrap_action.toggled.connect(self.change_word_wrap)
        view_menu.addAction(self.change_word_wrap_action)
        
        # About Menu
        about_menu = menubar.addMenu("&About")
        check_updates_action = QAction("Check for Updates", self)
        check_updates_action.triggered.connect(self.check_for_updates)
        about_menu.addAction(check_updates_action)
        
        # Edit Menu
        # edit_menu = menubar.addMenu("&Edit")
        # 
        # undo_action = QAction("Undo", self)
        # undo_action.triggered.connect(self.file_content_display.undo)
        # edit_menu.addAction(undo_action)
        # 
        # redo_action = QAction("Redo", self)
        # redo_action.triggered.connect(self.file_content_display.redo)
        # edit_menu.addAction(redo_action)
    
    def change_path_separator(self):
        try:
            input_replace_text = self.replace_string_input.text()

            if "/" in input_replace_text:
                new_input_replace_text = input_replace_text.replace("/","\\")
            else:
                new_input_replace_text = input_replace_text.replace("\\","/")

            self.replace_string_input.setText(new_input_replace_text)
        except Exception as ex:
            QMessageBox.critical(self, "Changing path separator error", f"An error occurred while trying to change path separator: {str(ex)}")
    
    def enable_change_path_separator_button(self):
        try:
            text = self.replace_string_input.text()
            if "/" in text or "\\" in text:
                self.change_path_separator_button.setVisible(True)
            else:
                self.change_path_separator_button.setVisible(False)
        except Exception as ex:
            QMessageBox.critical(self, "An error occurred", f"An error has occurred, {str(ex)}")
    
    def search_and_replace_file_content(self):
        try:
            file_view_content = self.file_content_display.toPlainText()
            regex_input = self.regex_pattern_input.text()

            if len(regex_input) > 0:
                # Compile the regex for better performance
                regex = re.compile(regex_input)

                # Split the content into lines
                lines = file_view_content.splitlines()

                # Find and clean lines that match the regex
                matching_lines = []
                for line in lines:
                    if regex.search(line):
                        try:
                            # Clean up the date from the line
                            cleaned_line = re.sub(r"^\d{2}\.\d{2}\.\d{2} \d{2}:\d{2}:\d{2}\s+", "", line)
                        except Exception:
                            cleaned_line = line
                        matching_lines.append(cleaned_line)

                if matching_lines:
                    self.program_output.clear()
                    self.file_content_display.clear()
                    self.program_output.append(f"Found {len(matching_lines)} matching lines for the regex pattern '{regex_input}':")
                    self.statusbar.showMessage(f"Found {len(matching_lines)} matching lines.", 10000)
                    # Display each cleaned line
                    for line in matching_lines:
                        self.file_content_display.append(line)
                else:
                    self.program_output.clear()
                    self.program_output.append(f"No matching lines found for the regex pattern '{regex_input}'.")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while searching and replacing the file content: {str(ex)}")

    def apply_and_replace_file_content(self):
        try:
            # Get content and user inputs
            file_view_content = self.file_content_display.toPlainText()
            phrase_to_remove = self.phrase_to_remove_input.text()  # Phrases to remove (comma-separated)
            original_phrase = self.find_string_input.text()  # Phrase to find
            replacement_phrase = self.replace_string_input.text()  # Phrase to replace with

            lines = file_view_content.splitlines()
            cleaned_lines = []

            for line in lines:
                # Clean and replace each line
                cleaned_line = self.clean_line(line, phrase_to_remove, original_phrase, replacement_phrase)
                cleaned_lines.append(cleaned_line)
            
            if cleaned_lines:
                # Clear the display and show the updated content
                self.statusbar.showMessage("Applied changes to the file content.", 10000)
                self.file_content_display.clear()
                self.file_content_display.setPlainText("\n".join(cleaned_lines))

        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while searching and replacing the file content: {str(ex)}")

    
    def clean_line(self, line, phrase_to_remove, original_phrase, replacement_phrase):
        # Remove user-specified phrases
        if phrase_to_remove:
            splitted_phrase = phrase_to_remove.split(",")
            for phrase in splitted_phrase:
                phrase = phrase.strip()  # Remove leading/trailing spaces
                if phrase:  # Ensure it"s not an empty string
                    line = re.sub(re.escape(phrase) + r"\s*", "", line)

        # Replace the original phrase with the replacement phrase
        if original_phrase and replacement_phrase:
            line = line.replace(original_phrase, replacement_phrase)

        return line

    def change_word_wrap(self):
        if self.change_word_wrap_action.isChecked():
            self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)
            self.program_output.setWordWrapMode(QTextOption.ManualWrap)
        else:
            self.file_content_display.setWordWrapMode(QTextOption.WordWrap)
            self.program_output.setWordWrapMode(QTextOption.WordWrap)
        
    def open_file_helper_method(self, file_path: str):
        try:
            if len(file_path) == 0:
                QMessageBox.critical(self,"No file path provided","Please provide a file path first.")
            elif not os.path.isfile(file_path) or not os.path.exists(file_path):
                QMessageBox.critical(self,"Not a valid path",f"The entered file path '{file_path}' is not valid or does not exist.")
            else:
                if "/" in file_path:
                    file_path = file_path.replace("/","\\")
                os.startfile(file_path)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(self, "Error", message)
    
    def open_folder_helper_method(self, folder_path):
        try:
            if len(folder_path) == 0:
                QMessageBox.critical(self,"No file path provided","Please provide a folder path first.")
            elif not os.path.isdir(folder_path) or not os.path.exists(folder_path):
                QMessageBox.critical(self,"Not a valid path",f"The entered folder path '{folder_path}' is not valid or does not exist.")
            else:
                os.startfile(folder_path)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(self, "Error", message)
            
    def clean_paths_in_line(self, file_content_display_text):
        try:
            file_content_display_text = self.file_content_display.toPlainText()
            lines = file_content_display_text.splitlines()

            # Remove single quotes from each line
            cleaned_lines = [line.replace("'", "") for line in lines]      
            return cleaned_lines
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while cleaning high commas ' in the paths: {str(ex)}")
        
    def generate_regex(self):
        try:
            input_text = self.regex_pattern_input.text()
            if len(input_text) > 0:
                self.regex_pattern_input.clear()
                self.generator = RegexGenerator(input_text)
                self.regex_pattern_input.setText(self.generator.get_regex())
                self.program_output.setText(f"Generated the following RegEx: '{self.generator.get_regex()}'.")
            else:
                QMessageBox.warning(self, "Input warning", "No string has been entered in the input element.")
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while generating the regex: {str(ex)}")
    
    def extract_dates_from_log(self, log_content):
        try:
            # Split the log content into lines
            lines = log_content.splitlines()

            # Define possible date patterns with strict and specific matching
            date_patterns = [
                (r"^(\d{2}\.\d{2}\.\d{4})", "%d.%m.%Y"),  # DD.MM.YYYY
                (r"^(\d{2}-\d{2}-\d{4})", "%d-%m-%Y"),    # DD-MM-YYYY
                (r"^(\d{2}\.\d{2}\.\d{2})", "%d.%m.%y"),  # DD.MM.YY
                (r"^(\d{2}-\d{2}-\d{2})", "%d-%m-%y")     # DD-MM-YY
            ]

            dates = set()  # Use a set to store unique dates

            # Process each line
            for line in lines:
                # Extract the first 10 characters of the line
                first_10_chars = line[:10]

                # Try to match each pattern
                for pattern, date_format in date_patterns:
                    match = re.match(pattern, first_10_chars)
                    if match:
                        date_str = match.group(1)
                        try:
                            # Validate the date by parsing it
                            datetime.strptime(date_str, date_format)
                            dates.add((date_str, date_format))  # Store date and its format
                            break  # Stop checking other patterns once a match is found
                        except ValueError:
                            # If the date is invalid (e.g., 30.02.2023), skip it
                            continue

            if not dates:
                raise ValueError("No valid date patterns found in the log file.")

            # Convert matched dates to datetime objects
            dates_datetime = []
            for date_str, date_format in dates:
                dates_datetime.append(datetime.strptime(date_str, date_format))

            # Sort the datetime objects
            dates_datetime_sorted = sorted(dates_datetime)

            # Convert datetime objects back to strings using their original format
            dates_sorted = []
            for date in dates_datetime_sorted:
                # Find the original format for this date
                for date_str, date_format in dates:
                    if datetime.strptime(date_str, date_format) == date:
                        dates_sorted.append(date.strftime(date_format))
                        break

            return dates_sorted

        except Exception as ex:
            QMessageBox.critical(self, "An error occurred", f"An exception of type {type(ex).__name__} occurred while trying to get the log file dates. {str(ex)}")
            return []
    
    def extract_lines_by_date_and_display(self, log_content, selected_date):
        filtered_lines = [
            line for line in log_content.splitlines() if line.startswith(selected_date)
        ]
        try:
            if self.log_dates_combobox.count() > 0:
                if log_content:
                    self.file_content_display.clear()
                    self.program_output.setText(f"Loaded log entries for selected date {selected_date} in file view...")
                    for text_line in filtered_lines:
                        self.file_content_display.append(text_line)
            else:
                self.program_output.clear()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while displaying the log entries: {str(ex)}")
        return filtered_lines
    
    def extract_data_from_log(self, file_path):
        try:
            if file_path:
                with open(file_path, "r") as file:
                    file_data = file.read()
                return file_data
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while reading the file: {str(ex)}")
    
    def refresh_file_content(self):
        try:
            current_text = self.log_dates_combobox.currentText()
            file_path = self.file_path_input.text()
            if os.path.isfile(file_path):
                with open(file_path, "r") as file:
                    file_data = file.read()
                if self.log_dates_combobox.count() > 0:
                    lines = self.extract_lines_by_date_and_display(file_data, current_text)
                    for line in lines:
                        self.file_content_display.append(line)
                else:
                    self.file_content_display.setPlainText(file_data)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while refreshing the file content: {str(ex)}")
        
    def browse_file(self):
        try:
            file_dialog = QFileDialog(self)
            file_path, _ = file_dialog.getOpenFileNames(self, "Open File", "", "Log File (*.log);;Text File (*.txt)")
            if not file_path:
                return
            else:
                # Clear log dates combobox
                if self.log_dates_combobox.count() > 0:
                    self.log_dates_combobox.clear()
                file_path = file_path[0]
                file_extension = Path(file_path).suffix
                if file_path and file_extension == ".log":
                    self.file_content_display.clear()
                    self.file_path_input.setText(file_path)
                    with open(file_path, "r") as file:
                        file_data = file.read()
                        self.log_dates_combobox.addItems(self.extract_dates_from_log(file_data))
                        last_item_index = self.log_dates_combobox.count() - 1
                        self.log_dates_combobox.setCurrentIndex(last_item_index) # Load the last item in the list
                    self.statusbar.setStyleSheet("color: #2cde85")
                    self.statusbar.showMessage("Loaded log file successfully.", 8000)
                elif file_path and file_extension == ".txt":
                    if self.log_dates_combobox.count() > 0:
                        self.log_dates_combobox.clear()
                    self.file_content_display.clear()
                    self.file_path_input.setText(file_path)
                    with open(file_path, "r") as file:
                        file_data = file.read()
                        self.file_content_display.setPlainText(file_data)
                    self.statusbar.setStyleSheet("color: #2cde85")
                    self.statusbar.showMessage("Loaded text file successfully.", 8000)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while opening the file: {str(ex)}")

    def get_line_count(self, file_path):
        with open(file_path, "r") as file:
            lines = file.readlines()
            return len(lines)
    
    def browse_folder(self):
        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(self, "Select Folder")
        if folder_path:
            self.destination_input.setText(folder_path)

    def move_files(self):
        destination = self.destination_input.text()
        text_containing_file_paths = self.file_content_display.toPlainText()
        
        # Check if destination directory has been set before trying to move any files, if not leave function and display error
        if not destination:
            self.statusbar.setStyleSheet("color: red")
            self.statusbar.showMessage("Please provide a destination directory.", 10000)
            self.program_output.setText("ERROR: Destination directory has not been set.")
            return
        else:
            if not text_containing_file_paths:
                self.statusbar.setStyleSheet("color: red")
                self.statusbar.showMessage("File content display is empty, hence nothing to move.")
                return
            else:
                self.statusbar.setStyleSheet("color: #2cde85")
                self.statusbar.showMessage("Using the displayed file content.", 10000)
                self.program_output.clear()
                    
                check_path_string_delimiter = ["/", "\\"]
                task_completed_message = "Task finished, results:"
                #self.statusbar.setStyleSheet("color: #2cde85")
                line_count = 1
                err_count = 0
                warn_count = 0

                try:
                    # Cleaned paths without high commas in the file content display
                    lines = self.clean_paths_in_line(text_containing_file_paths)
                    total_lines = len(lines)
                    for line in lines:
                        #progress = round((line_count / total_lines) * 100)
                        file_to_move = line.strip()
                        if file_to_move:
                            # Get the file name with its immediate parent directory
                            if check_path_string_delimiter[0] in file_to_move:  # Forward slash
                                sub_dir = "/".join(file_to_move.split("/")[-2:])  # Gets "lib/filename.jar"
                            elif check_path_string_delimiter[1] in file_to_move:  # Backslash
                                sub_dir = "\\".join(file_to_move.split("\\")[-2:])  # Gets "lib\filename.jar"
                            # Create the full destination path
                            current_destination = os.path.join(destination, sub_dir)

                            try:
                                # Ensure the destination directory exists
                                if os.path.exists(file_to_move):
                                    os.makedirs(os.path.dirname(current_destination), exist_ok=True)
                                shutil.move(file_to_move, current_destination)
                                self.program_output.append(f"Moved <span style='color:rgb(39, 124, 236)'>{file_to_move}</span> to <span style='color: green'>{current_destination}</span>")
                                self.statusbar.showMessage(f"Moved {line_count}/{total_lines} files.", 10000)
                            except FileNotFoundError:
                                self.program_output.append(f"<span style='color: orange'>WARN: {file_to_move}</span> not found, skipping.")
                                warn_count += 1
                                continue
                            except shutil.Error as e:
                                self.program_output.append(f"<span style='color: red'>ERROR: {e}</span>")
                                err_count += 1
                                continue
                            line_count += 1
                    self.program_output.append(f"\n{task_completed_message}\n")
                    if err_count > 0:
                        self.program_output.append(f"<span style='color: red'><strong>ERROR:</strong></span> {err_count} files failed to move.")
                    if warn_count > 0:
                        self.program_output.append(f"<span style='color: orange'><strong>WARNING:</strong></span> {warn_count} files were not found.")
                except Exception as e:
                    self.program_output.append(f"<span style='color: red'>FATAL ERROR: {e}</span>")

    def initialize_theme(self, theme_file):
        try:
            file = QFile(theme_file)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                self.setStyleSheet(stylesheet)
            file.close()
        except Exception as ex:
            QMessageBox.critical(self, "Theme load error", f"Failed to load theme: {str(ex)}")
            
    def closeEvent(self, event: QCloseEvent):
        # Save geometry on close
        geometry = self.saveGeometry()
        self.settings.setValue("geometry", geometry)
        super(MainWindow, self).closeEvent(event)
        
    def check_for_updates(self):
        install_path = self.current_working_dir
        repo_owner = "zaricj"
        repo_name = "FileSculptor"
        api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        #token = "none"
        
        #headers = {"Authorization": f"token {token}"}

        try:
            response = requests.get(api_url) # Re-add headers=headers and add secret token
            response.raise_for_status()
            latest_release = response.json()
            latest_version = latest_release["tag_name"]

            # Extract the browser_download_url
            if "assets" in latest_release and len(latest_release["assets"]) > 0:
                download_url = latest_release["assets"][0]["browser_download_url"]
            else:
                QMessageBox.critical(self, "Error", "No downloadable assets found in the latest release.")
                return

            if self.version < latest_version:
                reply = QMessageBox.question(
                    self,
                    "Update Available",
                    f"A new version ({latest_version}) is available.\nDo you want to download the update?",
                    QMessageBox.Yes | QMessageBox.No,
                    QMessageBox.No,
                )
                if reply == QMessageBox.Yes:
                    self.progressbar.setVisible(True)
                    self.program_output.append("Downloading update...")
                    zip_path = f"{repo_name}.7z"
                    with requests.get(download_url, stream=True, verify=False) as r:
                        r.raise_for_status()
                        total_size = int(r.headers.get('content-length', 0))
                        downloaded = 0
                        with open(zip_path, "wb") as file:
                            for chunk in r.iter_content(chunk_size=8192):
                                downloaded += len(chunk)
                                file.write(chunk)
                                progress = round((downloaded / total_size) * 100)
                                self.progressbar.setValue(progress)

                    # Unzip the downloaded file
                    extract_path = f"{repo_name}_{latest_version}"
                    with py7zr.SevenZipFile(zip_path, mode='r') as archive:
                        archive.extractall(path=extract_path)
                    
                    # Replace old files with  new ones
                    if os.path.exists(install_path):
                        shutil.rmtree(install_path)
                    shutil.move(extract_path, install_path)

                    # Check if the update was successful
                    if os.path.exists(extract_path):
                        updated_reply = QMessageBox.information(
                            self,
                            "Update Successful",
                            f"The update has been downloaded and unzipped successfully.\nLocation: {os.path.abspath(f'{repo_name}_{latest_version}')}\n\nDo you want to restart the application?", QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
                        # Delete downloaded 7z file
                        os.remove(zip_path)
                        if updated_reply == QMessageBox.Yes:
                            # Restart application
                            self.restart_application()
                        self.progressbar.setVisible(False)
                    else:
                        QMessageBox.critical(self, "Update Failed", "The update file could not be unzipped.")
            else:
                QMessageBox.information(self, "No Updates", "You are using the latest version.")
        except requests.RequestException as e:
            reply = QMessageBox.critical(self, "Error", f"An error occurred while checking for updates:\n{str(e)}\n\nDo you want to open the repo URL manually?", QMessageBox.Yes, QMessageBox.Close)
            if reply == QMessageBox.Yes:
                webbrowser.open(f"https://github.com/{repo_owner}/{repo_name}/releases/tag/{self.version}")
        except Exception as e:
            QMessageBox.critical(self, "Error", f"An error occurred while extracting the update:\n{str(e)}")
            
    def restart_application(self):
        """Restart the application."""
        QApplication.quit()
        subprocess.Popen([sys.executable] + sys.argv)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    app.exec()
