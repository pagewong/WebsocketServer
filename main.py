#-*-coding: UTF-8 -*-
import sys
import os
from PySide2.QtWidgets import QApplication
from ui.main_window import MainWindow

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
