import time, threading
from PyQt4 import QtCore, QtGui, Qt
import random

class Timer(QtGui.QWidget):
    def __init__(self, arg):
        super(Timer, self).__init__()
        self.args = arg
        self.on = False
        self.ms = None
        self.frame_timer = QtCore.QTimer(self)
        self.frame_timer.timeout.connect(self.printti)
        self.frame_timer.start(50)
        self.paused = False
        self.resize(200,300)
        self.num = 0
        self.numlabel = QtGui.QLabel("0")
        self.statlabel = QtGui.QLabel("-")
        self.leiska = QtGui.QVBoxLayout()
        self.setLayout(self.leiska)
        self.leiska.addWidget(self.numlabel)
        self.leiska.addWidget(self.statlabel)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == 80:
            self.pause()
        if QKeyEvent.key() == 32:
            self.printti()

    def pause(self):
        if self.paused:
            self.frame_timer.start(10)
        else:
            self.frame_timer.stop()
        self.paused = not self.paused

    def printti(self):
        self.num += 1
        self.numlabel.setText(str(self.num))
        self.statlabel.setText(str(self.frame_timer.isActive()))


if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    T = Timer(3)
    T.show()

    sys.exit(app.exec_())
    import ctypes

    ctypes.create_string_buffer()
    ctypes.c_int()
    ctypes. by







