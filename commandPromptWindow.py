# -*- coding: cp1252 -*-

from PyQt4 import QtGui, QtCore
from stylesheets import getStylesheet

class widget0(QtGui.QWidget):
    def __init__(self, parent=None):
        super(widget0, self).__init__()
        self.setStyleSheet(getStylesheet("orange"))
        self.lo = QtGui.QGridLayout()
        self.setUpStuff()
        self.setLayout(self.lo)

    def setUpStuff(self):
        self.BTN = QtGui.QPushButton("commandline")
        self.BTN.clicked.connect(self.openCML)
        self.lo.addWidget(self.BTN, 0, 0)

    def release(self):
        self.setEnabled(True)

    def openCML(self):
        self.cml = CommandLine(self)
        self.setEnabled(False)
        self.cml.show()

    def command(self, arg):
        print "commanded:", arg



class CommandPrompt(QtGui.QWidget):
    def __init__(self, master):
        super(CommandPrompt, self).__init__()
        self.master = master
        self.lo = QtGui.QGridLayout()
        self.setUpStuff()
        self.setLayout(self.lo)

    def setUpStuff(self):
        self.commandLine = QtGui.QTextEdit()
        self.commandLine = CommandLine(self)
        self.commandLine.setFixedSize(200, 40)
        self.lo.addWidget(self.commandLine, 0, 0)

    def keyPressEvent(self, QKeyEvent):
        if QKeyEvent.key() == "enter":
            print(self.commandLine.toPlainText())
            print QKeyEvent.key()
        self.close()

    def closeEvent(self, QCloseEvent):
        self.master.release()
        try:
            pause = self.master.__getattr__("pause")
            self.master.pause()
        except:
            pass
        super(CommandPrompt, self).closeEvent(QCloseEvent)



class CommandLine(QtGui.QLineEdit):
    def __init__(self, master):
        super(CommandLine, self).__init__()
        self.setStyleSheet(getStylesheet("orange"))
        self.master = master
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(400, 25)

    def keyPressEvent(self, QKeyEvent):
        super(CommandLine, self).keyPressEvent(QKeyEvent)
        print QKeyEvent.key()
        if QKeyEvent.key() == 16777220:
            self.send()
        if QKeyEvent.key() == 16777216:
            self.close()

    def send(self):
        if self.master:
            cmd = self.text().toUtf8()
            self.master.command(cmd)
        self.close()

    def closeEvent(self, *args, **kwargs):
        if self.master:
            self.master.release()
        super(CommandLine, self).closeEvent(*args, **kwargs)



if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    W0 = widget0()
    W0.show()
    #CL = CommandLine(None)
    #CL.show()
    sys.exit(app.exec_())