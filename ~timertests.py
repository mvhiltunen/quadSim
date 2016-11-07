import time, threading
from PyQt4 import QtCore, QtGui, Qt

class timer(threading.Thread):
    def __init__(self, target, args):
        super(timer, self).__init__()
        self.target = target
        self.args = args
        self.on = False
        self.ms = None

    def set_interval(self, ms):
        self.ms = ms


    def run(self):
        self.on = True
        if self.ms:
            tt = time.time()
            interval = self.ms/1000.0
            while self.on:
                gap = time.time()-tt
                if gap < interval:
                    time.sleep(interval-gap)
                tt = time.time()
                self.target(*self.args)


if __name__ == '__main__':
    import sys
    def a(value=0):
        k = 0
        print value
        for i in xrange(value):
            k += 100


    app = QtGui.QApplication(sys.argv)
    L = [56]
    T = timer(a, L)
    T.set_interval(333)
    T.start()
    time.sleep(3)
    L[0] = 34
    timer3 = Qt.QTimer()
    timer3.timeout.connect(a)
    timer3.start(200)
    sys.exit(app.exec_())







