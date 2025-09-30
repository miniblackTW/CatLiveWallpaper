import sys
import os
import shutil
import pyautogui
import win32gui
import win32con
import ctypes
from PyQt5 import QtWidgets, QtCore, QtGui
import atexit

def get_ww():
    pg = win32gui.FindWindow("Progman", None)
    res = ctypes.c_ulong()
    ctypes.windll.user32.SendMessageTimeoutW(
        pg, 0x052C, 0, 0, win32con.SMTO_NORMAL, 1000, ctypes.byref(res)
    )
    ww_list = []

    def cb(hwnd, l):
        p = win32gui.FindWindowEx(hwnd, 0, "SHELLDLL_DefView", None)
        if p != 0:
            l.append(win32gui.FindWindowEx(0, hwnd, "WorkerW", None))
        return True

    win32gui.EnumWindows(cb, ww_list)
    return ww_list[0] if ww_list else None

class Wp(QtWidgets.QLabel):
    def __init__(self, res_dir, frames):
        super().__init__()
        self.res_dir = res_dir
        self.frames = frames
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setScaledContents(True)
        self.showFullScreen()

        self.h = pyautogui.size().height
        self.cur = None
        self.pic = QtGui.QPixmap()
        self.setPixmap(self.pic)

        self.t = QtCore.QTimer()
        self.t.timeout.connect(self.upd)
        self.t.start(50)
        self.run = True

    def upd(self):
        if not self.run:
            return
        _, y = pyautogui.position()
        f = int((y / self.h) * (self.frames - 1)) + 1
        f = max(1, min(self.frames, f))
        if f != self.cur:
            fp = os.path.join(self.res_dir, f"f-{f:03}.jpg")
            if os.path.exists(fp):
                self.pic.load(fp)
                self.setPixmap(self.pic)
                self.cur = f

    def go(self):
        self.run = True

    def stop(self):
        self.run = False

    def back(self, bg):
        self.stop()
        if os.path.exists(bg):
            self.pic.load(bg)
            self.setPixmap(self.pic)
            self.cur = None

class Ctl(QtWidgets.QWidget):
    def __init__(self, wp, bg, restore_fn):
        super().__init__()
        self.wp = wp
        self.bg = bg
        self.restore_fn = restore_fn

        self.setWindowFlags(
            QtCore.Qt.Window |
            QtCore.Qt.CustomizeWindowHint |
            QtCore.Qt.WindowMinimizeButtonHint
        )
        self.setFixedSize(300, 150)
        self.setStyleSheet("""
            QWidget {
                background-color: #222;
                border-radius: 15px;
            }
            QPushButton {
                background-color: #444;
                color: white;
                border: none;
                border-radius: 8px;
                padding: 8px;
            }
            QPushButton:hover {
                background-color: #555;
            }
        """)

        lay = QtWidgets.QVBoxLayout()
        self.setLayout(lay)

        self.btn = QtWidgets.QPushButton("PAUSE")
        self.btn.clicked.connect(self.toggle)
        lay.addWidget(self.btn)

        self.quit = QtWidgets.QPushButton("EXIT")
        self.quit.clicked.connect(self.end)
        lay.addWidget(self.quit)

        self.state = True

    def toggle(self):
        if self.state:
            self.wp.stop()
            self.btn.setText("RESUME")
        else:
            self.wp.go()
            self.btn.setText("PAUSE")
        self.state = not self.state

    def end(self):
        self.restore_fn()
        QtWidgets.QApplication.quit()

    def closeEvent(self, e):
        e.ignore()

def main():
    d = os.path.join(os.path.dirname(__file__), "resources")
    os.makedirs(d, exist_ok=True)
    bg = os.path.join(d, "bg.png")
    SPI = 0x0073
    buf = ctypes.create_unicode_buffer(512)
    ctypes.windll.user32.SystemParametersInfoW(SPI, 512, buf, 0)
    ori = buf.value
    if os.path.exists(ori) and not os.path.exists(bg):
        shutil.copyfile(ori, bg)
    app = QtWidgets.QApplication(sys.argv)
    frames = 39
    w = Wp(d, frames)
    ww = get_ww()
    if ww:
        hwnd = w.winId().__int__()
        win32gui.SetParent(hwnd, ww)

    def restore_and_quit():
        if w:
            hwnd = w.winId().__int__()
            if win32gui.IsWindow(hwnd):
                win32gui.SetParent(hwnd, 0)
            w.back(bg)
            w.close()
        if os.path.exists(bg):
            ctypes.windll.user32.SystemParametersInfoW(
                20, 0, bg,
                1 | 2
            )
    atexit.register(restore_and_quit)
    ctl = Ctl(w, bg, restore_and_quit)
    ctl.show()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
