# -*- coding: cp1252 -*-

from PyQt4 import QtGui, QtCore
from stylesheets import getStylesheet

class widget0(QtGui.QWidget):
    def __init__(self, parent=None):
        super(widget0, self).__init__()
        self.resize(500,200)
        self.setStyleSheet(getStylesheet("orange"))
        #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
        self.lo = QtGui.QVBoxLayout()
        self.setUpStuff()
        self.setLayout(self.lo)

    def setUpStuff(self):
        self.BTN = QtGui.QPushButton("commandline")
        self.BTN.clicked.connect(self.openCML)
        self.lo.addWidget(self.BTN, 1)

    def release(self):
        self.setEnabled(True)
        self.setFocus()

    def openCML(self):
        self.cml = CommandLine(self, self)
        self.cml.move(10,30)
        self.cml.setFocus()
        self.cml.show()

    def command(self, arg):
        print "commanded:", arg


class CommandLineWidget(QtGui.QWidget):
    def __init__(self,master,toParent=None):
        super(CommandLineWidget, self).__init__(toParent)
        self.setStyleSheet(getStylesheet("orange"))
        self.master = master
        self.setParent(toParent)
        self.leiska = QtGui.QVBoxLayout()
        self.cmdline = QtGui.QLineEdit()
        self.cmdline.setFixedSize(200,300)
        self.cmdline.setText("Foobar")
        self.suggestions = QtGui.QTextEdit()
        self.leiska.addWidget(self.cmdline)
        self.leiska.addWidget(self.suggestions)
        self.setWindowFlags(QtCore.Qt.FramelessWindowHint)

    def keyPressEvent(self, QKeyEvent):
        super(CommandLineWidget, self).keyPressEvent(QKeyEvent)
        if QKeyEvent.key() == 16777220:
            self.send()
        if QKeyEvent.key() == 16777216:
            self.close()
        self.cmdline.keyPressEvent(QKeyEvent)

    def send(self):
        cmd = self.text().toUtf8()
        self.master.command(cmd)
        self.close()

    def closeEvent(self, *args, **kwargs):
        self.master.release()
        super(CommandLine, self).closeEvent(*args, **kwargs)



class CommandLine(QtGui.QLineEdit):
    def __init__(self, master, toParent=None):
        super(CommandLine, self).__init__(toParent)
        self.master = master
        self.setStyleSheet(getStylesheet("orange"))
        self.setFixedSize(400, 25)



    def keyPressEvent(self, QKeyEvent):
        super(CommandLine, self).keyPressEvent(QKeyEvent)
        if QKeyEvent.key() == 16777220:
            self.send()
        if QKeyEvent.key() == 16777216:
            self.close()

    def send(self):
        cmd = self.text().toUtf8()
        self.master.command(cmd)
        self.close()

    def closeEvent(self, *args, **kwargs):
        self.master.release()
        super(CommandLine, self).closeEvent(*args, **kwargs)


class SuggestionField(QtGui.QLineEdit):
    def __init__(self, parent):
        super(SuggestionField, self).__init__()
        #self.setParent(parent)
        self.setText("KooKoo")
        #self.setStyleSheet(getStylesheet("orange"))
        self.commands = ["reset","kill","set_time_dilation","foo","bar","foobar"]
        #self.append("Koo")

    def setSuggestions(self, string):
        #THIS is ugly
        L = []
        self.clear()
        for cmd in self.commands:
            if cmd.startswith(string):
                L.append(cmd)
        if L:
            for cmd in L:
                self.append(cmd)
                self.append('\n')



if __name__ == '__main__':
    import sys
    app = QtGui.QApplication(sys.argv)
    W0 = widget0()
    W0.show()
    #CL = CommandLine(None)
    #CL.show()
    sys.exit(app.exec_())