import sys
import shutil
import os
import re
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QMessageBox, QGroupBox, QComboBox, QMenu, QMenuBar, QWidget, QStatusBar, QSizePolicy
from PySide6.QtGui import QTextOption, QCloseEvent, QIcon, QAction
from PySide6.QtCore import Qt, QSettings, QFile, QTextStream
from datetime import datetime

# //TODO Add feature to get "Marking file ..." lines and extract their file paths
# //TODO Add input field for user to create replace ./lib/ with D:/Lobster_data/lib/ for example
# // TODO Add input for string to replace from - to
# // TODO Add input to search for regex pattern and replace all text in self.file_content_display with the found pattern

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
        # Settings to save current location of the windows on exit
        self.settings = QSettings("Application", "Name")
        geometry = self.settings.value("geometry", bytes())
        if geometry:
            self.restoreGeometry(geometry)
        icon = QIcon("_internal\\icon\\app.ico")
        self.restoreGeometry(geometry)
        self.initialize_theme("_internal\\theme_files\\dark.qss")
        self.setWindowIcon(icon)
        self.initUI()
        self.setWindowTitle("Dynamic File Mover")
        self.create_menu_bar()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QHBoxLayout(central_widget)  # Changed to QHBoxLayout for side-by-side arrangement
        
        # Statusbar
        self.statusbar = QStatusBar()
        self.statusbar.setSizeGripEnabled(False)

        # Group box for File View (left side)
        file_view_groupbox = QGroupBox("File Content View")
        file_view_layout = QVBoxLayout()

        # Input paths layout
        horizontal_layout_a = QHBoxLayout()
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText("Browse the directory to the file for reading...")
        self.file_path_input.setReadOnly(True)
        horizontal_layout_a.addWidget(self.file_path_input)

        self.browse_button = QPushButton("Browse File", self)
        self.browse_button.clicked.connect(self.browse_file)
        horizontal_layout_a.addWidget(self.browse_button)
        file_view_layout.addLayout(horizontal_layout_a)

        horizontal_layout_b = QHBoxLayout()
        self.destination_input = QLineEdit(self)
        self.destination_input.setPlaceholderText("Browse the destination directory where the files should be moved to...")
        self.destination_input.setReadOnly(True)
        horizontal_layout_b.addWidget(self.destination_input)

        self.set_folder_button = QPushButton("Set Folder", self)
        self.set_folder_button.clicked.connect(self.browse_folder)
        horizontal_layout_b.addWidget(self.set_folder_button)
        file_view_layout.addLayout(horizontal_layout_b)

        # Log file dates combobox
        self.log_dates_combobox = QComboBox(self)
        self.log_dates_combobox.setToolTip("Select a date to view the log entries for that date.\nThis will re-display the log entries for the selected date in the file view.")
        self.log_dates_combobox.setMinimumWidth(85)
        self.log_dates_combobox.currentTextChanged.connect(lambda: self.extract_lines_by_date_and_display(
            self.extract_data_from_log(self.file_path_input.text()), 
            self.log_dates_combobox.currentText()
        ))

        # Horizontal Layout for Regex and Replace
        horizontal_layout_d = QHBoxLayout()
        self.regex_pattern_input = QLineEdit(self)
        self.regex_pattern_input.setPlaceholderText("Enter text to convert to regex pattern to search the file content...")
        self.regex_pattern_input.setToolTip("Enter a regex pattern to search for in the file content.")
        self.regex_pattern_input.setClearButtonEnabled(True)
        self.convert_entered_string_to_regex_button = QPushButton("Convert", self)
        self.convert_entered_string_to_regex_button.setToolTip("Convert the entered string to a regex pattern.")
        self.convert_entered_string_to_regex_button.clicked.connect(self.generate_regex)
        self.search_file_contents_and_display_button = QPushButton("Search", self)
        self.search_file_contents_and_display_button.setToolTip("Search file content for the entered regex pattern and display only those matches.")
        self.search_file_contents_and_display_button.clicked.connect(self.search_and_replace_file_content)
        horizontal_layout_d.addWidget(self.regex_pattern_input)
        horizontal_layout_d.addWidget(self.convert_entered_string_to_regex_button)
        horizontal_layout_d.addWidget(self.search_file_contents_and_display_button)

        horizontal_layout_e = QHBoxLayout()
        self.find_string_input = QLineEdit(self)
        self.find_string_input.setPlaceholderText("Enter text to replace (e.g., ./lib/)")
        self.find_string_input.setToolTip("Enter the text to find which will be replaced later in the file content display.\nExample: ./lib/")
        self.find_string_input.setClearButtonEnabled(True)
        self.replace_string_input = QLineEdit(self)
        self.replace_string_input.setPlaceholderText("Replace text in file content with (e.g., D:/Lobster_data/lib/)")
        self.replace_string_input.setToolTip("Enter the text to replace the found text with in the file content display.\n Example: D:/Lobster_data/lib/")
        self.replace_string_input.setClearButtonEnabled(True)
        self.phrase_to_remove_input = QLineEdit(self)
        self.phrase_to_remove_input.setPlaceholderText("Enter phrases to remove comma-separated (e.g., Marking file, to be deleted on exit of JVM)")
        self.phrase_to_remove_input.setToolTip("Enter phrases to remove from the file content.\nCan be comma-separated (eg., Marking file, to be deleted on exit of JVM).")
        self.phrase_to_remove_input.setClearButtonEnabled(True)
        self.apply_button = QPushButton("Apply", self)
        self.apply_button.setToolTip("Apply the changes to the file content.")
        self.apply_button.clicked.connect(self.apply_and_replace_file_content)
        horizontal_layout_e.addWidget(self.find_string_input)
        horizontal_layout_e.addWidget(self.replace_string_input)
        horizontal_layout_e.addWidget(self.phrase_to_remove_input)
        horizontal_layout_e.addWidget(self.apply_button)

        # File View Content
        file_view_horizontal_layout = QHBoxLayout()
        font_size_list = ["12px", "14px", "16px", "18px", "20px"]
        self.file_view_label = QLabel("Font Size:", self)
        self.file_view_combobox = QComboBox()
        self.file_view_combobox.setMinimumWidth(55)
        self.file_view_combobox.setCurrentText("12px")
        self.file_view_combobox.addItems(font_size_list)
        self.file_view_combobox.currentIndexChanged.connect(lambda: self.file_content_display.setStyleSheet(
            f"font-size: {self.file_view_combobox.currentText()}"
        ))
        self.move_button = QPushButton("Move Files", self)
        self.move_button.setToolTip("Move the files to the destination directory.")
        self.move_button.setMinimumWidth(100)
        self.move_button.clicked.connect(self.move_files)

        file_view_horizontal_layout.addWidget(QLabel("Log Date:", self))
        file_view_horizontal_layout.addWidget(self.log_dates_combobox)
        file_view_horizontal_layout.addWidget(self.file_view_label)
        file_view_horizontal_layout.addWidget(self.file_view_combobox)
        file_view_horizontal_layout.addWidget(self.move_button)
        file_view_horizontal_layout.addWidget(self.statusbar)
        #file_view_horizontal_layout.addStretch()

        self.file_content_display = QTextEdit(self)
        self.file_content_display.setReadOnly(False)
        self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)

        file_view_layout.addLayout(horizontal_layout_d)
        file_view_layout.addLayout(horizontal_layout_e)
        file_view_layout.addLayout(file_view_horizontal_layout)
        file_view_layout.addWidget(self.file_content_display)
        file_view_groupbox.setLayout(file_view_layout)
        main_layout.addWidget(file_view_groupbox)

        # Group box for Program Output (right side)
        program_output_groupbox = QGroupBox("Program Output")
        program_output_layout = QVBoxLayout()
        program_output_horizontal_layout = QHBoxLayout()
        self.font_size_label = QLabel("Font Size:", self)
        self.font_size_combobox = QComboBox()
        self.font_size_combobox.setMinimumWidth(55)
        self.font_size_combobox.setCurrentText("12px")
        self.font_size_combobox.addItems(font_size_list)
        self.font_size_combobox.currentIndexChanged.connect(lambda: self.program_output.setStyleSheet(f"font-size: {self.font_size_combobox.currentText()}"))
        self.program_output = QTextEdit(self)
        self.program_output.setReadOnly(True)
        self.program_output.setWordWrapMode(QTextOption.ManualWrap)
        program_output_horizontal_layout.addWidget(self.font_size_label)
        program_output_horizontal_layout.addWidget(self.font_size_combobox)
        program_output_horizontal_layout.addStretch()
        program_output_layout.addLayout(program_output_horizontal_layout)
        program_output_layout.addWidget(self.program_output)
        program_output_groupbox.setMaximumWidth(600)
        program_output_groupbox.setLayout(program_output_layout)
        main_layout.addWidget(program_output_groupbox)

        self.setCentralWidget(central_widget)

    def create_menu_bar(self):
        menubar = self.menuBar()
        
        # File menu
        file_menu = menubar.addMenu("&File")
        
        # Clear Program output
        clear_action = QAction("Clear Program Output", self)
        clear_action.triggered.connect(lambda: self.program_output.clear())
        file_menu.addAction(clear_action)

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
        file_content_wrap_mode = self.file_content_display.wordWrapMode()
        program_output_wrap_mode = self.program_output.wordWrapMode()
        print(file_content_wrap_mode, program_output_wrap_mode)
        
        if self.change_word_wrap_action.isChecked():
            self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)
            self.program_output.setWordWrapMode(QTextOption.ManualWrap)
        else:
            self.file_content_display.setWordWrapMode(QTextOption.WordWrap)
            self.program_output.setWordWrapMode(QTextOption.WordWrap)
        
    def open_file_helper_method(self, file_path):
        try:
            if len(file_path) == 0:
                QMessageBox.critical(self,"No file path provided","Please provide a file path first.")
            elif not os.path.isfile(file_path) or not os.path.exists(file_path):
                QMessageBox.critical(self,"Not a valid path",f"The entered file path '{file_path}' is not valid or does not exist.")
            else:
                os.startfile(file_path)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(self, "Error", message)
    
    def open_folder_helper_method(self, folder_path):
        try:
            if len(folder_path) == 0:
                QMessageBox.critical(self,"No file path provided","Please provide a file path first.")
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
        date_pattern = r"(\d{2}\.\d{2}\.\d{2})"
        dates = set(re.findall(date_pattern, log_content))
        date_format = "%d.%m.%y"
        dates_datetime = [datetime.strptime(date, date_format) for date in dates]
        # Sort the datetime objects
        dates_datetime_sorted = sorted(dates_datetime)
        # Convert datetime objects back to strings
        dates_sorted = [datetime.strftime(date, date_format) for date in dates_datetime_sorted]

        return dates_sorted
    
    def extract_lines_by_date_and_display(self, log_content, selected_date):
        filtered_lines = [
            line for line in log_content.splitlines() if line.startswith(selected_date)
        ]
        try:
            if log_content:
                self.file_content_display.clear()
                self.program_output.setText(f"Loaded log entries for selected date {selected_date} in file view...")
                for text_line in filtered_lines:
                    self.file_content_display.append(text_line)
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while displaying the log entries: {str(ex)}")
        return filtered_lines
    
    def extract_data_from_log(self, file_path):
        try:
            if file_path:
                with open(file_path, "r") as file:
                    file_data = file.read()
        except Exception as ex:
            QMessageBox.critical(self, "Error", f"An error occurred while reading the file: {str(ex)}")
        return file_data
        
    def browse_file(self):
        try:
            file_dialog = QFileDialog(self)
            file_path, _ = file_dialog.getOpenFileName(self, "Open File", "", "Log Files (*.log)")
            if file_path:
                self.file_content_display.clear()
                self.file_path_input.setText(file_path)
                with open(file_path, "r") as file:
                    file_data = file.read()
                    self.log_dates_combobox.addItems(self.extract_dates_from_log(file_data))
                self.statusbar.setStyleSheet("color: #2cde85")
                self.statusbar.showMessage("Loaded log file successfully.", 8000)
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
        reply = QMessageBox.warning(self, "Warning", "Are you sure you want to move the files?", QMessageBox.Yes | QMessageBox.No)
        if reply == QMessageBox.No:
            return
        else:
            self.program_output.clear()
            file_path = self.file_path_input.text()
            destination = self.destination_input.text()
            text_containing_file_paths = self.file_content_display.toPlainText()
            if not file_path or not destination:
                self.statusbar.setStyleSheet("color: red")
                self.statusbar.showMessage("Please provide both file path and destination directory.", 7000)
                return

            check_path_string_delimiter = ["/", "\\"]
            task_completed_message = "Moving task completed successfully."
            self.statusbar.setStyleSheet("color: #2cde85")
            line_count = 1
            err_count = 0
            warn_count = 0

            try:
                # Cleaned paths without high commas in the file content display
                lines = self.clean_paths_in_line(text_containing_file_paths)
                total_lines = len(lines)
                for line in lines:
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
                            self.program_output.append(f"Moved <span style='color: #197cff'>{file_to_move}</span> to <span style='color: green'>{current_destination}</span>")
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
                self.program_output.append(f"\n=======================\n{task_completed_message}\n=======================\n")
                if err_count > 0:
                    self.program_output.append(f"<span style='color: red'>ERROR: {err_count} files failed to move.</span>")
                if warn_count > 0:
                    self.program_output.append(f"<span style='color: orange'>WARNING: {warn_count} files were not found.</span>")
            except Exception as e:
                self.program_output.append(f"<span style='color: red'>ERROR: {e}</span>")
            
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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    app.exec()
