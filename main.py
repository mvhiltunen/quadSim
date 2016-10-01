#!/usr/bin/env python


import sys
import numpy as np


from PyQt4 import QtCore, QtGui, QtOpenGL

from sip import setdestroyonexit
setdestroyonexit(False)

import sys
from OpenGL.GLU import *



# IMPORT OBJECT LOADER
from objloader import *
import time, math
import constants as C
from machineSim import Machine


class GLWidget(QtOpenGL.QGLWidget):
    xRotationChanged = QtCore.pyqtSignal(int)
    yRotationChanged = QtCore.pyqtSignal(int)
    zRotationChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.z = np.array([0.0, 0.0, 1.0])
        self.setBaseSize(1000, 1200)
        self.W_DOWN = self.A_DOWN = self.S_DOWN = self.D_DOWN = self.SPACE_DOWN = False
        self.UP_DOWN = self.DOWN_DOWN = self.RIGHT_DOWN = self.LEFT_DOWN = self.CTRL_DOWN = False

        self.goal_fps = 60.0
        self.goal_steptime = 1.0/120.0
        self.starttime = None
        self.steps_done = 0

        self.avg_frametime = 0.1
        self.avg_fps = 10.0
        self.TTime = time.time()

        self.machine = Machine()
        self.machine.physics_tick(0.01)
        self.MOVE_OBJECT= True
        self.MOVE_FLOOR = False

        self.d90 = np.pi/2.0
        self.d360 = np.pi * 2.0
        self.camDirection = np.array([self.d90, 0.0])
        self.camPosition = np.array([0.0, -5.0, 5.0])
        self.camVectorX = np.array([0.0, 0.0, 0.0])
        self.camVectorY = np.array([0.0, 0.0, 0.0])
        self.camVectorZ = np.array([0.0, 0.0, 0.0])
        self.obtainCamVectors()

        self.xRot = 0.0
        self.yRot = 0.0
        self.zRot = 0.0

        self.xPos = 0.0
        self.yPos = 0.0
        self.zPos = 0.0
        self.zoomLevel = 1.0

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.advance)
        timer.start(20)


    def updateFPStime(self):
        newtime = time.time()
        frametime = newtime-self.TTime
        self.avg_frametime = self.avg_frametime*0.5 + frametime
        self.avg_fps = self.avg_fps*0.5 + 0.5/self.avg_frametime
        self.TTime = time.time()

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

    def toRadians(self, degree):
        return degree*0.017453292519943*(1.0/16)

    def normalizeAngle(self, angle):
        angle = angle % self.d360
        return angle



    def initializeGL(self):
        print "InitGL"
        lightPos = (5.0, 5.0, 10.0, 1.0)
        reflectance1 = (0.8, 0.1, 0.0, 1.0)
        reflectance2 = (0.0, 0.8, 0.2, 1.0)
        reflectance3 = (0.2, 0.2, 1.0, 1.0)


        glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)

        glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
        glEnable(GL_LIGHT0)
        glEnable(GL_LIGHTING)
        glEnable(GL_COLOR_MATERIAL)
        glEnable(GL_DEPTH_TEST)
        glShadeModel(GL_SMOOTH)

        self.mainmotor_obj = OBJ("MainMotor.obj", swapyz=True)
        self.sidemotor_obj = OBJ("SideMotor.obj", swapyz=True)
        self.hextile_obj = OBJ("HexTile.obj", swapyz=True)
        self.stick_obj = OBJ("Stick.obj", swapyz=True)
        self.hull_obj = OBJ("MainHull.obj", swapyz=True)

        glEnable(GL_NORMALIZE)
        glClearColor(0.0, 0.0, 0.0, 1.0)



    def paintGL(self):
        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

        glPushMatrix()
        glLoadIdentity()

        glRotate(-self.d90 * 57.2957795, 1.0, 0.0, 0.0)
        glRotate(self.camDirection[1] * -57.2957795, 1.0, 0.0, 0.0)
        glRotate((self.camDirection[0]-self.d90) * -57.2957795, 0.0, 0.0, 1.0)
        glTranslate(-self.camPosition[0], -self.camPosition[1], -self.camPosition[2])

        tile_r = 10.39232 # = 5.196160*2
        downrange_x = 1*self.machine.P[0]*self.MOVE_FLOOR
        downrange_y = 1*self.machine.P[1]*self.MOVE_FLOOR
        glPushMatrix()
        glTranslate(0.0, 0.0, -0.1)
        self.drawFloor(10, tile_r, downrange_x, downrange_y) #Floor of hexagonals
        glPopMatrix()

        glPushMatrix()
        glTranslate(0.0, 0.0, 0.0)
        self.drawMachine(self.machine, self.hull_obj, self.mainmotor_obj, self.sidemotor_obj)
        glFinish()
        glPopMatrix()

        glPopMatrix()



    def resizeGL(self, width, height):
        side = min(width, height)
        if side < 0:
            return
        viewport = (1000,800)
        #glViewport((width - side) // 2, (height - side) // 2, side, side)
        glViewport(0,0, viewport[0], viewport[1])

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width, height = viewport
        gluPerspective(80.0, width/float(height), 1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslated(0.0, 0.0, -30.0)


    def keyPressEvent(self, event):
        K = event.key()
        if K == 16777235: #UP
            self.UP_DOWN = True
        if K == 16777237: #DOWN
            self.DOWN_DOWN = True
        if K == 16777234: #LEFT
            self.LEFT_DOWN = True
        if K == 16777236: #RIGHT
            self.RIGHT_DOWN = True
        if K == 87: #W
            self.W_DOWN = True
        if K == 65:#A
            self.A_DOWN = True
        if K == 83:#S
            self.S_DOWN = True
        if K == 68:#D
            self.D_DOWN = True
        if K == 32:
            self.SPACE_DOWN = True
        if K == 16777249:
            self.CTRL_DOWN = True
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


    def wheelEvent(self,event):
        tick = event.delta()/120
        self.setZoom(tick)


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


    def advance(self):
        self.updateFPStime()
        self.keyPressHandle()
        self.machine.physics_tick(self.avg_frametime)
        self.updateGL()


    def keyPressHandle(self):
        if self.LEFT_DOWN:
            self.camDirection[0] += 0.12
        if self.RIGHT_DOWN:
            self.camDirection[0] -= 0.12
        if self.UP_DOWN:
            self.camDirection[1] += 0.04
        if self.DOWN_DOWN:
            self.camDirection[1] -= 0.04
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



    def drawMachine(self, machine, hull, mainmotor, sidemotor):
        pos, dir = machine.get_hull_pos_and_ax_angle()
        ax0, deg0 = dir

        glPushMatrix()
        glTranslate(pos[0]*self.MOVE_OBJECT, pos[1]*self.MOVE_OBJECT, pos[2])

        glPushMatrix()
        glRotate(deg0, ax0[0], ax0[1], ax0[2])
        glCallList(hull.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(1)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(2)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(3)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(sidemotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(4)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(-e_pos[0]*2, -e_pos[1]*2, -e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(sidemotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPopMatrix()


    def drawFloor(self, R, tile_r, pos_x, pos_y):
        tile_sep = tile_r * 1.1
        c30 = math.cos(0.5235987755)
        s30 = math.sin(0.5235987755)

        glPushMatrix()
        offset_x = pos_x % ((2*tile_sep*c30))
        offset_y = pos_y % (2*tile_sep*s30)
        glTranslate(offset_x, offset_y, 0)


        floor_r_i = int(R*1.6)
        floor_r_j = int(R*1.6)
        for i in range(-floor_r_i, floor_r_i):
            for j in range(-floor_r_j, floor_r_j):
                i2 = int(i/2.0)
                ic = i-i2
                j2 = int(j/2.0)
                jc = j-j2
                os = abs(i%2)

                x = (ic*tile_sep*c30)+(i2*tile_sep*c30)
                y = (jc*tile_sep)+os*tile_sep*s30

                if math.sqrt(x*x+y*y) < (R * tile_r):
                    glPushMatrix()
                    glTranslate(x, y, 0)
                    glCallList(self.hextile_obj.gl_list)
                    glPopMatrix()

        glPopMatrix()

if __name__ == '__main__':

    app = QtGui.QApplication(sys.argv)
    mainWin = GLWidget()
    mainWin.show()
    sys.exit(app.exec_())
