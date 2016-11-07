#!/usr/bin/env python

from PyQt4 import QtCore, QtGui, QtOpenGL
import sys, time
import numpy as np
from threading import Thread
import threading


class Hound(QtCore.QThread):
    def __init__(self, target, interval):
        super(Hound, self).__init__()
        self.target = target
        self.interval = interval
        self.on = True

    def stop(self):
        self.on = False

    def run(self):
        next_t = time.time()
        while self.on:
            #next_t = time.time() + self.interval
            next_t = next_t + self.interval
            self.target()
            tt = time.time()
            if tt < next_t:
                time.sleep(next_t - tt)


class SimWidget(QtOpenGL.QGLWidget):
    def __init__(self):
        super(SimWidget, self).__init__()
        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.foo)
        self.M = np.random.rand(1000,1000)
        self.M2 = np.random.rand(1000,1000)
        self.tt = time.time()
        #timer.start(1000)
        #print timer.interval()
        #self.foo()
        #self.foo()
        #self.foo()
        #self.foo()
        self.hound = Hound(target=self.foo, interval=1.0)
        self.hound.start()

    def foo(self):
        tt = time.time()
        print tt-self.tt
        self.tt = tt
        for i in range(500):
            M3 = self.M+self.M2
            #M3 = M3.transpose(1,0)

    def closeEvent(self, *args, **kwargs):
        self.hound.stop()
        super(SimWidget, self).closeEvent(*args, **kwargs)



if __name__ == '__main__':
    app = QtGui.QApplication(sys.argv)
    mainWin = SimWidget()
    mainWin.show()
    sys.exit(app.exec_())