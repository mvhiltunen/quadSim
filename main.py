#!/usr/bin/env python
# -*- coding: utf8 -*-


from PyQt4 import QtCore, QtGui, QtOpenGL
from sip import setdestroyonexit
from OpenGL.GLU import *
import time, sys
import constants as C
import multiprocessing
from GLWidget import GLWidget
from multiprocessing import Manager, Queue
from machineSimPar import MachineP
from commandPromptWindow import CommandLine


class Holder(QtGui.QMainWindow):
    def __init__(self, params=None):
        super(Holder, self).__init__()
        self.resize(1280,720)
        self.params = C.default_parameters.copy()
        self.params.update(params)
        self.glwidget = GLWidget(self.params)
        self.glwidget.setParent(self)
        self.setCentralWidget(self.glwidget)
        self.command_que = Queue(1000)
        self.control_que = Queue(1000)
        self.manager = Manager()
        self.result_dict = self.manager.dict()
        self.machine = MachineP(command_queue=self.command_que, status_duct=self.result_dict, control_queue=self.control_que, parameters=self.params)
        #self.controller = Controller(status_duct=self.results_dict, control_queue=self.control_que, parameters=self.params)
        self.result_dict["draw_info"] = self.machine.get_draw_info()
        self.glwidget.setDrawInfoDict(self.result_dict)
        self.paused = False
        self.frozen = False
        self.commandline = None
        self.machine.start()
        time.sleep(0.1)
        self.glwidget.unfreeze()

    def keyPressEvent(self, event):
        if event.key() in C.control_codes_to_keys:
            self.glwidget.keyPressEvent(event)

    def keyReleaseEvent(self, event):
        if event.key() in C.control_codes_to_keys:
            self.glwidget.keyReleaseEvent(event)
        elif event.key() == C.main_keys_to_codes["P"]:
            self.pause()
        elif event.key() == C.main_keys_to_codes["C"]:
            self.openCommandLine()

    def mousePressEvent(self, event):
        if not self.frozen:
            self.glwidget.mousePressEvent(event)
        super(Holder, self).mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not self.frozen:
            self.glwidget.mouseMoveEvent(event)
        super(Holder, self).mouseMoveEvent(event)

    def wheelEvent(self,event):
        if not self.frozen:
            self.glwidget.wheelEvent(event)
        super(Holder, self).wheelEvent(event)

    def pause(self):
        self.command_que.put(("pause", []))
        self.paused = not self.paused

    def freeze(self):
        self.glwidget.freeze()
        self.frozen = not self.frozen

    def openCommandLine(self):
        self.freeze()
        if not self.paused:
            self.pause()
        self.commandline = CommandLine(self, self)
        self.commandline.setFocus()
        self.commandline.move(self.width()/2 - self.commandline.width()/2, self.height()/3 - self.commandline.height()/2)
        self.commandline.show()

    def command(self, cmd):
        print "received command:", cmd

    def release(self):
        self.freeze()
        if self.commandline:
            self.commandline.hide()
            self.commandline.close()
            self.commandline = None
        self.setFocus()
        if self.paused:
            self.pause()

    def closeEvent(self, *args, **kwargs):
        self.command_que.put(("stop", []))
        self.glwidget.closeEvent(*args, **kwargs)
        for ch in multiprocessing.active_children():
            ch.terminate()
        if self.commandline:
            self.commandline.close()
        super(Holder, self).closeEvent(*args, **kwargs)







if __name__ == '__main__':
    params = {"mode":"parallel",
              "min_dt":0.00025,
              "goal_fps":60,
              "timestep_eval_frequency":10.0,
              "update_frequency":100.0,
              "control_frequency":50.0,
              "control_sharpness":97.0,
              "MOVE_OBJECT":False,
              "MOVE_FLOOR":False,
              "dt_relaxation_coeff":0.9,
              "testing":True}

    app = QtGui.QApplication(sys.argv)
    mainWin = Holder(params)
    mainWin.show()
    sys.exit(app.exec_())

