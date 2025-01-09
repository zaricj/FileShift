import sys
import shutil
import os
from PySide6.QtWidgets import QApplication, QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QMessageBox, QGroupBox, QComboBox, QMenu, QMenuBar, QWidget
from PySide6.QtGui import QTextOption, QCloseEvent, QIcon, QAction
from PySide6.QtCore import Qt, QSettings, QFile, QTextStream

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        # Settings to save current location of the windows on exit
        self.settings = QSettings("Application","Name")
        geometry = self.settings.value("geometry", bytes())
        icon = QIcon("_internal\\icon\\app.ico")
        self.restoreGeometry(geometry)
        self.initialize_theme('_internal\\theme_files\\dark.qss')
        self.setWindowIcon(icon)
        self.initUI()
        self.setWindowTitle('File Mover')
        self.setGeometry(800, 400, 1000, 700)
        self.create_menu_bar()

    def initUI(self):
        central_widget = QWidget()
        main_layout = QVBoxLayout(central_widget)
    
        # Input paths layout
        horizontal_layout_a = QHBoxLayout()
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText('Enter the path to the text file containing file paths')
        horizontal_layout_a.addWidget(self.file_path_input)
    
        self.browse_button = QPushButton('Browse File', self)
        self.browse_button.clicked.connect(self.browse_files)
        horizontal_layout_a.addWidget(self.browse_button)
        main_layout.addLayout(horizontal_layout_a)
    
        horizontal_layout_b = QHBoxLayout()
        self.destination_input = QLineEdit(self)
        self.destination_input.setPlaceholderText('Enter the destination directory')
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
        self.status_label = QLabel('', self)
        main_layout.addWidget(self.status_label)
    
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
        self.file_view_combobox.currentIndexChanged.connect(lambda: self.file_content_display.setStyleSheet(f"font-size: {self.file_view_combobox.currentText   ()}"))
    
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

        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)

        # Open Menu
        open_menu = menubar.addMenu("&Open")
        
        open_csv_folder = QAction("Open Destination Folder", self)
        open_csv_folder.triggered.connect(lambda: self.open_folder_helper_method(self.destination_input.text()))
        open_menu.addAction(open_csv_folder)
        
        # Help menu
        help_menu = menubar.addMenu("&Help")
        how_to_use_action = QAction("How to Use", self)
        help_menu.addAction(how_to_use_action)
    
    def open_folder_helper_method(self, folder_path):
        try:
            if not os.path.isdir(folder_path) or not os.path.exists(folder_path):
                QMessageBox.critical(self,"Not a valid path",f"The entered folder path '{folder_path}' is not valid or does not exist.")
            else:
                os.startfile(folder_path)
        except Exception as ex:
            message = f"An exception of type {type(ex).__name__} occurred. Arguments: {ex.args!r}"
            QMessageBox.critical(self, "Error", message)
        
    def browse_files(self):
        file_dialog = QFileDialog(self)
        file_path, _ = file_dialog.getOpenFileName(self, 'Open File', '', 'Text Files (*.txt)')
        if file_path:
            self.file_path_input.setText(file_path)
            with open(file_path, 'r') as file:
                self.file_content_display.setText(file.read())
            total_lines = self.get_line_count(file_path)
            self.status_label.setText(f'Found {total_lines} files.')
    
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
        self.program_output.clear()
        file_path = self.file_path_input.text()
        destination = self.destination_input.text()
        if not file_path or not destination:
            self.status_label.setText('Please provide both file path and destination directory.')
            return

        line_count = 1
        err_count = 0
        warn_count = 0
        task_completed_message = "Moving task completed successfully."

        try:
            with open(file_path, 'r') as file:
                lines = file.readlines()
                total_lines = len(lines)
                for line in lines:
                    file_to_move = line.strip()
                    if file_to_move:
                        try:
                            shutil.move(file_to_move, destination)
                            self.program_output.append(f'Moved <span style="color: #197cff">{file_to_move}</span> to <span style="color: green">{destination}</span>')
                            self.status_label.setText(f'Moved {line_count}/{total_lines} files.')
                        except FileNotFoundError:
                            self.program_output.append(f'<span style="color: orange">WARN: {file_to_move}</span> not found, skipping.')
                            warn_count += 1
                            continue
                        except shutil.Error as e:
                            self.program_output.append(f'<span style="color: red">ERROR: {e}</span>')
                            err_count += 1
                            continue
                        line_count += 1
                self.program_output.append(f"\n{task_completed_message.upper()}")
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
