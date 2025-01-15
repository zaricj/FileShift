import sys
import shutil
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QMessageBox, QGroupBox, QComboBox, QMenu, QMenuBar, QWidget, QStatusBar
from PySide6.QtGui import QTextOption, QCloseEvent, QIcon, QAction
from PySide6.QtCore import Qt, QSettings, QFile, QTextStream

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
        self.initialize_theme('_internal\\theme_files\\dark.qss')
        self.setWindowIcon(icon)
        self.initUI()
        self.setWindowTitle('File Mover')
        self.create_menu_bar()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
    
        # Input paths layout
        horizontal_layout_a = QHBoxLayout()
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText('Enter the path to the text file which contains file paths...')
        self.file_path_input.setText("C:/Users/ZaricJ/Desktop/test_move.txt")
        horizontal_layout_a.addWidget(self.file_path_input)
    
        self.browse_button = QPushButton('Browse File', self)
        self.browse_button.clicked.connect(self.browse_file)
        horizontal_layout_a.addWidget(self.browse_button)
        main_layout.addLayout(horizontal_layout_a)
    
        horizontal_layout_b = QHBoxLayout()
        self.destination_input = QLineEdit(self)
        self.destination_input.setPlaceholderText('Enter the destination directory where the files should be moved to...')
        self.destination_input.setText("C:/Users/ZaricJ/Desktop/MOVING")
        horizontal_layout_b.addWidget(self.destination_input)
    
        self.set_folder_button = QPushButton('Set Folder', self)
        self.set_folder_button.clicked.connect(self.browse_folder)
        horizontal_layout_b.addWidget(self.set_folder_button)
        main_layout.addLayout(horizontal_layout_b)
    
        # Move button
        self.move_button = QPushButton('Move Files', self)
        self.move_button.clicked.connect(self.move_files)
        main_layout.addWidget(self.move_button)
    
        # Status label
        self.statusbar = QStatusBar()
        self.statusbar.setSizeGripEnabled(False)
        main_layout.addWidget(self.statusbar)
    
        # Horizontal layout for File View and Program Output
        horizontal_layout_c = QHBoxLayout()
    
        # Group box for File View
        file_view_groupbox = QGroupBox("File View")
        file_view_layout = QVBoxLayout()
        file_view_horizontal_layout = QHBoxLayout()
    
        font_size_List = ["12px", "14px", "16px", "18px", "20px"]
        self.file_view_label = QLabel("Font Size:", self)
        self.file_view_combobox = QComboBox()
        self.file_view_combobox.setMinimumWidth(100)
        self.file_view_combobox.setCurrentText("12px")
        self.file_view_combobox.addItems(font_size_List)
        self.file_view_combobox.currentIndexChanged.connect(lambda: self.file_content_display.setStyleSheet(f"font-size: {self.file_view_combobox.currentText()}"))
    
        self.file_content_display = QTextEdit(self)
        self.file_content_display.setReadOnly(False)
        self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)
    
        file_view_horizontal_layout.addWidget(self.file_view_label)
        file_view_horizontal_layout.addWidget(self.file_view_combobox)
        file_view_horizontal_layout.addStretch()
        file_view_layout.addLayout(file_view_horizontal_layout)
        file_view_layout.addWidget(self.file_content_display)
        file_view_groupbox.setLayout(file_view_layout)
        horizontal_layout_c.addWidget(file_view_groupbox)
    
        # Group box for Program Output
        program_output_groupbox = QGroupBox("Program Output")
        program_output_layout = QVBoxLayout()
        program_output_horizontal_layout = QHBoxLayout()
    
        self.font_size_label = QLabel("Font Size:", self)
        self.font_size_combobox = QComboBox()
        self.font_size_combobox.setMinimumWidth(100)
        self.font_size_combobox.setCurrentText("12px")
        self.font_size_combobox.addItems(font_size_List)
        self.font_size_combobox.currentIndexChanged.connect(lambda: self.program_output.setStyleSheet(f"font-size: {self.font_size_combobox.currentText()}"))
    
        self.program_output = QTextEdit(self)
        self.program_output.setReadOnly(True)
        self.program_output.setWordWrapMode(QTextOption.ManualWrap)
    
        program_output_horizontal_layout.addWidget(self.font_size_label)
        program_output_horizontal_layout.addWidget(self.font_size_combobox)
        program_output_horizontal_layout.addStretch()
        program_output_layout.addLayout(program_output_horizontal_layout)
        program_output_layout.addWidget(self.program_output)
        program_output_groupbox.setLayout(program_output_layout)
        horizontal_layout_c.addWidget(program_output_groupbox)
    
        main_layout.addLayout(horizontal_layout_c)
    
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
        
        open_file = QAction("Open Text File", self)
        open_file.triggered.connect(lambda: self.open_file_helper_method(self.file_path_input.text()))
        open_menu.addAction(open_file)
        
        # View Menu
        view_menu = menubar.addMenu("&View")
        self.change_word_wrap_action = QAction("Toggle Word Wrap", self)
        self.change_word_wrap_action.setCheckable(True)
        self.change_word_wrap_action.setChecked(True)

        self.change_word_wrap_action.toggled.connect(self.change_word_wrap)
        view_menu.addAction(self.change_word_wrap_action)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        how_to_use_action = QAction("How to Use", self)
        help_menu.addAction(how_to_use_action)
        
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
            
    def clean_file(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()       
        # Remove single quotes from each line
        cleaned_lines = [line.replace("'", "") for line in lines]      
        # Write the cleaned lines back to the file
        with open(file_path, 'w') as file:
            file.writelines(cleaned_lines)
        
    def browse_file(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt)')
        if file_path:
            self.file_path_input.setText(file_path)
            with open(file_path, 'r') as file:
                self.clean_file(file_path)
                self.file_content_display.setText(file.read())
                total_lines = self.get_line_count(file_path)
            self.statusbar.showMessage(f'Found {total_lines} files in text file to move.')
    
    def get_line_count(self, file_path):
        with open(file_path, 'r') as file:
            lines = file.readlines()
            return len(lines)
    
    def browse_folder(self):
        folder_dialog = QFileDialog(self)
        folder_path = folder_dialog.getExistingDirectory(self, 'Select Folder')
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
            if not file_path or not destination:
                self.statusbar.setStyleSheet("color: red")
                self.statusbar.showMessage("Please provide both file path and destination directory.", 7000)
                return

            check_path_string_delimiter = ["/", "\\"]
            task_completed_message = "Moving task completed successfully."
            self.statusbar.setStyleSheet("color: white")
            line_count = 1
            err_count = 0
            warn_count = 0

            try:
                with open(file_path, 'r') as file:
                    lines = file.readlines()
                    total_lines = len(lines)
                    for line in lines:
                        file_to_move = line.strip()
                        if file_to_move:
                            # Get the file name with its immediate parent directory
                            if check_path_string_delimiter[0] in file_to_move:  # Forward slash
                                sub_dir = '/'.join(file_to_move.split('/')[-2:])  # Gets "lib/filename.jar"
                            elif check_path_string_delimiter[1] in file_to_move:  # Backslash
                                sub_dir = '\\'.join(file_to_move.split('\\')[-2:])  # Gets "lib\filename.jar"

                            # Create the full destination path
                            current_destination = os.path.join(destination, sub_dir)
                            # Ensure the destination directory exists
                            os.makedirs(os.path.dirname(current_destination), exist_ok=True)

                            try:
                                shutil.move(file_to_move, current_destination)
                                self.program_output.append(f'Moved <span style="color: #197cff">{file_to_move}</span> to <span style="color: green">{current_destination}</span>')
                                self.statusbar.showMessage(f'Moved {line_count}/{total_lines} files.')
                            except FileNotFoundError:
                                self.program_output.append(f'<span style="color: orange">WARN: {file_to_move}</span> not found, skipping.')
                                warn_count += 1
                                continue
                            except shutil.Error as e:
                                self.program_output.append(f'<span style="color: red">ERROR: {e}</span>')
                                err_count += 1
                                continue
                            line_count += 1
                    self.program_output.append(f"\n=======================\n{task_completed_message}\n=======================")
                    if err_count > 0:
                        self.program_output.append(f'<span style="color: red">ERROR: {err_count} files failed to move.</span>')
                    if warn_count > 0:
                        self.program_output.append(f'<span style="color: orange">WARNING: {warn_count} files were not found.</span>')
            except Exception as e:
                self.program_output.append(f'<span style="color: red">ERROR: {e}</span>')
            
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

if __name__ == '__main__':
    app = QApplication(sys.argv)
    ex = MainWindow()
    ex.show()
    app.exec()
