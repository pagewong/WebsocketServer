import os

from PySide2.QtWidgets import (QApplication, QMainWindow, QPushButton, QPlainTextEdit,
                               QVBoxLayout, QWidget, QProgressBar, QLineEdit, QLabel, QHBoxLayout, QSizePolicy)
from PySide2.QtCore import QProcess, QTimer
import sys
import re

# A regular expression, to extract the % complete.
progress_re = re.compile("Total complete: (\d+)%")

def simple_percent_parser(output):
    """
    Matches lines using the progress_re regex,
    returning a single integer for the % progress.
    """
    m = progress_re.search(output)
    if m:
        pc_complete = m.group(1)
        return int(pc_complete)


class MainWindow(QMainWindow):

    def __init__(self, **kwargs):
        super().__init__()

        self.root_path = kwargs.get('root_path')
        self.exe_call = kwargs.get('exe_call')
        self.p = None

        self.host_input = QLineEdit("0.0.0.0")
        self.port_input = QLineEdit("8765")
        self.send_input = QPlainTextEdit()

        self.log_text = QPlainTextEdit()
        self.log_text.setReadOnly(True)

        self.start_button = QPushButton("Start Server")
        self.stop_button = QPushButton("Stop Server")
        self.send_button = QPushButton("Send")

        self.start_button.pressed.connect(self.start_process)
        self.stop_button.pressed.connect(self.stop_process)
        self.send_button.pressed.connect(self.send_message)  # Connect send button to send_message method

        # Set size policy for buttons to expand
        sizePolicy = QSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.start_button.setSizePolicy(sizePolicy)
        self.stop_button.setSizePolicy(sizePolicy)
        self.send_button.setSizePolicy(sizePolicy)

        # Layout for host and port with label
        ws_address_layout = QHBoxLayout()
        host_label = QLabel("Host:")
        port_label = QLabel("Port:")
        ws_address_layout.addWidget(host_label)
        ws_address_layout.addWidget(self.host_input)
        ws_address_layout.addWidget(port_label)
        ws_address_layout.addWidget(self.port_input)

        # Layout for start and stop buttons
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.addWidget(self.start_button)
        control_buttons_layout.addWidget(self.stop_button)


        l = QVBoxLayout()
        l.addLayout(ws_address_layout)
        l.addLayout(control_buttons_layout)
        l.addWidget(self.send_input)

        l.addWidget(self.send_button)
        l.addWidget(self.log_text)

        w = QWidget()
        w.setLayout(l)

        self.setCentralWidget(w)

        # Set the initial size of the window
        self.resize(800, 400)  # Width, Height

    def write_log(self, s):
        self.log_text.appendPlainText(s)

    def send_message(self):
        message = self.send_input.toPlainText().strip()
        if message:  # Check if the message is not empty
            if self.p and self.p.state() == QProcess.Running:
                self.p.write((message + "\n").encode())  # Send the message to the process
                self.log_text.appendPlainText("Sent message: " + message)
                self.send_input.clear()  # Optionally clear the input after sending
            else:
                self.log_text.appendPlainText("Error: Server process is not running.")
        else:
            self.log_text.appendPlainText("Error: No message to send.")

    def start_process(self):
        if self.p is None:  # No process running.
            self.write_log("Executing process")
            self.p = QProcess()  # Keep a reference to the QProcess (e.g. on self) while it's running.
            self.p.readyReadStandardOutput.connect(self.handle_stdout)
            self.p.readyReadStandardError.connect(self.handle_stderr)
            self.p.stateChanged.connect(self.handle_state)
            self.p.finished.connect(self.process_finished)  # Clean up once complete.
            # self.p.start("python", ['ws_main.py'])


            # Get the path of the current Python interpreter
            if self.exe_call:
                python_executable = os.path.join(self.root_path, 'runtime', 'python.exe')
            else:
                python_executable = sys.executable

            print(f"pexe:{python_executable}")

            # Construct the relative path to the script
            script_path = os.path.join(os.path.dirname(__file__), 'ws', 'ws_main.py')

            args = [script_path, self.host_input.text(), self.port_input.text()]

            # Start the process
            self.p.start(python_executable, args)
            # self.p.start('ping', '127.0.0.1')

    def stop_process(self):
        if self.p is not None:
            # Send a command to the websocket server to close the connection
            self.p.write("close\n".encode())  # Ensure your server recognizes "close" as a command to shut down
            self.write_log("Sending close command to the server...")
            # Give the server a little time to process the close command
            QTimer.singleShot(1000, self.terminate_process)

    def terminate_process(self):
        if self.p is not None:
            self.p.terminate()  # Attempt to terminate the process
            self.write_log("Stopping the server...")
            # Wait for an additional 4 seconds to check if process has terminated
            QTimer.singleShot(4000, self.force_stop_process)

    def force_stop_process(self):
        if self.p is not None and self.p.state() != QProcess.NotRunning:
            self.p.kill()  # Forcefully kill the process if still running
            self.write_log("Server forcefully stopped.")

    def handle_stderr(self):
        data = self.p.readAllStandardError()
        stderr = bytes(data).decode("utf8")
        # Extract progress if it is in the data.
        progress = simple_percent_parser(stderr)
        if progress:
            self.progress.setValue(progress)
        self.write_log(stderr)

    def handle_stdout(self):
        data = self.p.readAllStandardOutput()
        stdout = bytes(data).decode("utf8")
        self.write_log(stdout)

    def handle_state(self, state):
        states = {
            QProcess.NotRunning: 'Not running',
            QProcess.Starting: 'Starting',
            QProcess.Running: 'Running',
        }
        state_name = states[state]
        self.write_log(f"State changed: {state_name}")

    def process_finished(self):
        self.write_log("Process finished.")
        self.p = None


def main(exe_call=False):

    app = QApplication(sys.argv)

    current_path = os.getcwd()
    base_path = os.path.dirname(current_path)
    root_path = base_path if not exe_call else current_path
    print(f"root_path:{root_path}")
    w = MainWindow(root_path=root_path, exe_call=exe_call)
    w.show()

    app.exec_()


if __name__ == '__main__':

    main()
