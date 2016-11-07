#!/usr/bin/env python
# -*- coding: utf8 -*-

import numpy as np
from PyQt4 import QtCore, QtGui, QtOpenGL
from sip import setdestroyonexit
setdestroyonexit(False)
from OpenGL.GLU import *
# IMPORT OBJECT LOADER
import time, math, sys
import constants as C
from machineSim import Machine
from machineSimPar import MachineP
from objloader import *
from multiprocessing import Manager, Queue
import multiprocessing
import drawFunctions
from commandPromptWindow import CommandLine
from stylesheets import getStylesheet

class SimWidget(QtOpenGL.QGLWidget):
    xRotationChanged = QtCore.pyqtSignal(int)
    yRotationChanged = QtCore.pyqtSignal(int)
    zRotationChanged = QtCore.pyqtSignal(int)

    def __init__(self, parameters=None):
        super(SimWidget, self).__init__()
        self.params = parameters
        if not self.params:
            self.params = C.default_parameters
        self.z = np.array([0.0, 0.0, 1.0])
        self.W_DOWN = self.A_DOWN = self.S_DOWN = self.D_DOWN = self.SPACE_DOWN = False
        self.UP_DOWN = self.DOWN_DOWN = self.RIGHT_DOWN = self.LEFT_DOWN = self.CTRL_DOWN = False
        self.MOVE_OBJECT = True
        self.MOVE_FLOOR = False
        self.d90 = np.pi/2.0
        self.d360 = np.pi * 2.0
        self.camDirection = np.array([self.d90, 0.0])
        self.camPosition = np.array([0.0, -5.0, 5.0])
        self.camVectorX = np.array([0.0, 0.0, 0.0])
        self.camVectorY = np.array([0.0, 0.0, 0.0])
        self.camVectorZ = np.array([0.0, 0.0, 0.0])
        self.lastPos = None
        self.obtainCamVectors()

        self.mode = self.params["mode"]
        self.min_dt = self.params["min_dt"]

        self.command_que = None
        self.manager = None
        self.status_duct = None
        self.machine = None
        self.paused = False
        self.commandline = None

        self.initializeMachine()

        self.goal_fps = 60.0
        self.goal_steptime = 1.0 / 120.0
        self.framecount = 0

        self.avg_frametime = 0.1
        self.avg_fps = 10.0
        self.TTime = time.time()

        self.frame_timer = QtCore.QTimer(self)
        self.frame_timer.timeout.connect(self.advance)
        self.frame_timer.start(18)

    def initializeMachine(self):
        if self.mode == "single":
            self.machine = Machine()

        elif self.mode == "parallel":
            self.command_que = Queue(1000)
            self.manager = Manager()
            self.status_duct = self.manager.dict()
            self.machine = MachineP(command_queue=self.command_que, status_duct=self.status_duct, parameters=self.params)
            self.status_duct["draw_info"] = self.machine.get_draw_info()
            self.machine.start()
            time.sleep(0.1)

    def obtainCamVectors(self):
        self.camVectorX[0] = np.sin(self.camDirection[0])
        self.camVectorX[1] = -np.cos(self.camDirection[0])
        self.camVectorZ[0] = np.cos(self.camDirection[0])*np.cos(self.camDirection[1])
        self.camVectorZ[1] = np.sin(self.camDirection[0])*np.cos(self.camDirection[1])
        self.camVectorZ[2] = np.sin(self.camDirection[1])
        self.camVectorY = np.cross(self.camVectorX, self.camVectorZ)

    def changeZRotation(self, d_angle):
        angle = self.camDirection[0]+d_angle
        angle = self.normalizeAngle(angle)
        self.camDirection[0] = angle
        self.obtainCamVectors()

    def changeXRotation(self, d_angle):
        angle = self.camDirection[1] + d_angle
        angle = sorted( (-self.d90, angle, self.d90) )[1]
        self.camDirection[1] = angle
        self.obtainCamVectors()

    def changeXPosition(self, dx):
        self.camPosition += self.camVectorX * dx

    def changeYPosition(self, dy):
        self.camPosition += self.camVectorY * dy

    def setZoom(self, change):
        if change < 0:
            self.camPosition -= self.camVectorZ * 3
        if change > 0:
            self.camPosition += self.camVectorZ * 3

    def normalizeAngle(self, angle):
        angle = angle % self.d360
        return angle

    def initializeGL(self):
        print "InitGL...",
        lightPos = (5.0, 5.0, 10.0, 1.0)

        glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)

        self.mainmotor_obj = OBJ("MainMotor.obj", swapyz=True)
        self.sidemotor_obj = OBJ("SideMotor.obj", swapyz=True)
        self.hextile_obj = OBJ("HexTile.obj", swapyz=True)
        self.stick_obj = OBJ("Stick.obj", swapyz=True)
        self.hull_obj = OBJ("MainHull.obj", swapyz=True)

        glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        glEnable(GL_NORMALIZE)
        glClearColor(0.0, 0.0, 0.0, 1.0)
        glLoadIdentity()
        print " ...done."

    def paintGL(self):
        self.framecount += 1
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushMatrix()
        glLoadIdentity()
        glRotate(-self.d90 * 57.2957795, 1.0, 0.0, 0.0)
        glRotate(self.camDirection[1] * -57.2957795, 1.0, 0.0, 0.0)
        glRotate((self.camDirection[0]-self.d90) * -57.2957795, 0.0, 0.0, 1.0)
        glTranslate(-self.camPosition[0], -self.camPosition[1], -self.camPosition[2])

        draw_info = self.get_draw_info()

        tile_r = 10.39232
        downrange_x = draw_info["hull_pos"][0]*self.MOVE_FLOOR
        downrange_y = draw_info["hull_pos"][1]*self.MOVE_FLOOR
        glPushMatrix()
        glTranslate(0.0, 0.0, -0.1)
        drawFunctions.drawFloor(tile=self.hextile_obj, R=9, tile_r=tile_r, pos_x=downrange_x, pos_y=downrange_y)
        glPopMatrix()

        glPushMatrix()
        glTranslate(0.0, 0.0, 0.0)
        drawFunctions.drawMachine(HORIZONTAL_MOVE=self.MOVE_OBJECT, draw_info=draw_info, hull=self.hull_obj, mainmotor=self.mainmotor_obj, sidemotor=self.sidemotor_obj)
        glPopMatrix()
        glPopMatrix()


    def resizeGL(self, width, height):
        #viewport = C.getResolution(0.7)
        viewport = (int(self.width()), int(self.height()))
        width, height = viewport
        if min(width, height) < 0:
            return
        #glViewport((width - side) // 2, (height - side) // 2, side, side)
        glViewport(0,0, width, height)
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(80.0, width/float(height), 1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslated(0.0, 0.0, -30.0)

    def keyPressEvent(self, event):
        K = event.key()
        if K == 16777235: #UP
            self.UP_DOWN = True
        elif K == 16777237: #DOWN
            self.DOWN_DOWN = True
        elif K == 16777234: #LEFT
            self.LEFT_DOWN = True
        elif K == 16777236: #RIGHT
            self.RIGHT_DOWN = True
        elif K == 87: #W
            self.W_DOWN = True
        elif K == 65:#A
            self.A_DOWN = True
        elif K == 83:#S
            self.S_DOWN = True
        elif K == 68:#D
            self.D_DOWN = True
        elif K == 32:#Space
            self.SPACE_DOWN = True
        elif K == 16777249:#Ctrl
            self.CTRL_DOWN = True
        elif K == 80:#P
            self.pause()
        elif K == 67:#C
            self.openCommandLine()
        #print event.key()

    def keyReleaseEvent(self, event):
        K = event.key()
        if K == 16777235: #UP
            self.UP_DOWN = False
        if K == 16777237: #DOWN
            self.DOWN_DOWN = False
        if K == 16777234: #LEFT
            self.LEFT_DOWN = False
        if K == 16777236: #RIGHT
            self.RIGHT_DOWN = False
        if K == 87: #W
            self.W_DOWN = False
        if K == 65:#A
            self.A_DOWN = False
        if K == 83:#S
            self.S_DOWN = False
        if K == 68:#D
            self.D_DOWN = False
        if K == 32:
            self.SPACE_DOWN = False
        if K == 16777249:
            self.CTRL_DOWN = False

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()
        if event.buttons() & QtCore.Qt.LeftButton:
            self.changeXRotation(0.002 * dy)
            self.changeZRotation(0.002 * dx)
        elif event.buttons() & QtCore.Qt.RightButton:
            self.changeXPosition(0.06 * -dx)
            self.changeYPosition(0.06 * dy)
        self.lastPos = event.pos()

    def wheelEvent(self,event):
        tick = event.delta()/120
        self.setZoom(tick)

    def keyPressHandle(self):
        if self.LEFT_DOWN:
            self.camDirection[0] += 0.10
        if self.RIGHT_DOWN:
            self.camDirection[0] -= 0.10
        if self.UP_DOWN:
            self.camDirection[1] += 0.050
        if self.DOWN_DOWN:
            self.camDirection[1] -= 0.050
        if self.W_DOWN:
            self.camPosition += self.camVectorZ * 3
        if self.S_DOWN:
            self.camPosition -= self.camVectorZ * 2
        if self.A_DOWN:
            self.camPosition -= self.camVectorX * 2
        if self.D_DOWN:
            self.camPosition += self.camVectorX * 2
        if self.SPACE_DOWN:
            self.camPosition += self.z
        if self.CTRL_DOWN:
            self.camPosition -= self.z
        self.camDirection[1] = sorted((-self.d90, self.camDirection[1], self.d90))[1]
        self.obtainCamVectors()


    def advance(self):
        self.keyPressHandle()
        self.advance_machines()
        self.updateGL()

    def updateFPStime(self):
        newtime = time.time()
        frametime = (newtime-self.TTime)/self.framecount
        self.TTime = newtime
        self.avg_frametime = self.avg_frametime*0.5 + frametime*0.5
        self.avg_fps = self.avg_fps*0.5 + 0.5/frametime
        self.framecount = 0


    def advance_machines(self):
        if self.mode == "single":
            self.machine.physics_tick(self.avg_frametime)
            if self.framecount > 20:
                self.updateFPStime()
        elif self.mode == "parallel":
            pass

    def get_draw_info(self):
        if self.mode == "single":
            return self.machine.get_draw_info()
        elif self.mode == "parallel":
            return self.status_duct["draw_info"]
        else:
            return False

    def pause(self):
        self.command_que.put(("pause", []))
        self.paused = not self.paused

    def closeEvent(self, *args, **kwargs):
        self.frame_timer.stop()
        if self.mode == "parallel":
            self.command_que.put( ("stop",[]) )
            time.sleep(0.05)
        for pr in multiprocessing.active_children():
            pr.terminate()
        if self.commandline:
            self.commandline.close()
        super(SimWidget, self).closeEvent(*args, **kwargs)

    def openCommandLine(self):
        self.setEnabled(False)
        if not self.paused:
            self.pause()
        self.commandline = CommandLine(self)
        self.commandline.show()

    def command(self, cmd):
        print "received command:", cmd

    def release(self):
        self.setEnabled(True)
        self.commandline = None
        if self.paused:
            self.pause()


if __name__ == '__main__':
    params = {"mode": "parallel",
              "min_dt": 0.00025,
              "goal_fps": 60,
              "frametime_eval_time": 0.1,
              "update_time": 0.01,
              "dt_relaxation_coeff": 0.9}
    app = QtGui.QApplication(sys.argv)
    mainWin = SimWidget(parameters=params)
    mainWin.show()
    sys.exit(app.exec_())

