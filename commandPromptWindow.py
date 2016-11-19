# -*- coding: cp1252 -*-

from PyQt4 import QtGui, QtCore
from stylesheets import getStylesheet

class widget0(QtGui.QWidget):
    def __init__(self, parent=None):
        super(widget0, self).__init__()
        self.setStyleSheet(getStylesheet("orange"))
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
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
        #self.setEnabled(False)
        self.cml = CommandLine(self, self)
        #self.cml.move(10,10)
        self.cml.show()

    def command(self, arg):
        print "commanded:", arg




class CommandLine(QtGui.QLineEdit):
    def __init__(self, master, toParent=None):
        super(CommandLine, self).__init__(toParent)
        self.master = master
        self.setStyleSheet(getStylesheet("orange"))
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)
        self.setFixedSize(400, 25)

    def keyPressEvent(self, QKeyEvent):
        super(CommandLine, self).keyPressEvent(QKeyEvent)
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


class SuggestionField(QtGui.QTextEdit):
    def __init__(self, parent):
        super(SuggestionField, self).__init__(parent)
        self.commands = ["reset","kill","set_time_dilation","foo","bar","foobar"]

    def setSuggestions(self, string):
        #THIS is ugly
        L = []
        for cmd in self.commands:
            if cmd.startswith(string):
                L.append(cmd)
        if L:



if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    W0 = widget0()
    W0.show()
    #CL = CommandLine(None)
    #CL.show()
    sys.exit(app.exec_())