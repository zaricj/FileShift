import sys
from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLineEdit, QFileDialog, QTextEdit, QLabel, QMessageBox, QGroupBox
from PySide6.QtGui import QTextOption, QCloseEvent
from PySide6.QtCore import Qt, QSettings, QFile, QTextStream
import shutil

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        # Settings to save current location of the windows on exit
        self.settings = QSettings("Application","Name")
        geometry = self.settings.value("geometry", bytes())
        self.restoreGeometry(geometry)
        self.initialize_theme('_internal\\theme_files\\dark.qss')

        self.initUI()

    def initUI(self):
        self.setWindowTitle('File Mover')
        self.setGeometry(800, 400, 1000, 700)

        layout = QVBoxLayout()

        # Input paths layout
        horizontal_layout_a = QHBoxLayout()
        self.file_path_input = QLineEdit(self)
        self.file_path_input.setPlaceholderText('Enter the path to the text file containing file paths')
        horizontal_layout_a.addWidget(self.file_path_input)

        self.browse_button = QPushButton('Browse File', self)
        self.browse_button.clicked.connect(self.browse_files)
        horizontal_layout_a.addWidget(self.browse_button)
        layout.addLayout(horizontal_layout_a)

        horizontal_layout_b = QHBoxLayout()
        self.destination_input = QLineEdit(self)
        self.destination_input.setPlaceholderText('Enter the destination directory')
        horizontal_layout_b.addWidget(self.destination_input)

        self.set_folder_button = QPushButton('Set Folder', self)
        self.set_folder_button.clicked.connect(self.browse_folder)
        horizontal_layout_b.addWidget(self.set_folder_button)
        layout.addLayout(horizontal_layout_b)

        # Move button
        self.move_button = QPushButton('Move Files', self)
        self.move_button.clicked.connect(self.move_files)
        layout.addWidget(self.move_button)

        # Status label
        self.status_label = QLabel('', self)
        layout.addWidget(self.status_label)

        # Group box for text editors
        text_edit_layout = QHBoxLayout()

        # File view
        file_view_layout = QVBoxLayout()
        file_view_label = QLabel("File View:", self)
        self.file_content_display = QTextEdit(self)
        self.file_content_display.setReadOnly(False)
        self.file_content_display.setWordWrapMode(QTextOption.ManualWrap)
        file_view_layout.addWidget(file_view_label)
        file_view_layout.addWidget(self.file_content_display)
        text_edit_layout.addLayout(file_view_layout)

        # Program output
        program_output_layout = QVBoxLayout()
        program_output_label = QLabel("Program Output:", self)
        self.program_output = QTextEdit(self)
        self.program_output.setReadOnly(True)
        self.program_output.setWordWrapMode(QTextOption.ManualWrap)
        program_output_layout.addWidget(program_output_label)
        program_output_layout.addWidget(self.program_output)
        text_edit_layout.addLayout(program_output_layout)

        layout.addLayout(text_edit_layout)

        self.setLayout(layout)
        
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
