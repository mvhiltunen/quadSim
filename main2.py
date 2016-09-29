#!/usr/bin/env python



import sys
import numpy as np

from PyQt4 import QtCore, QtGui, QtOpenGL

from OpenGL.GL import *


from sip import setdestroyonexit
setdestroyonexit(False)


import sys
from OpenGL.GLU import *


# IMPORT OBJECT LOADER
from objloader import *
import time, math

from machineSim import Machine


class GLWidget(QtOpenGL.QGLWidget):
    xRotationChanged = QtCore.pyqtSignal(int)
    yRotationChanged = QtCore.pyqtSignal(int)
    zRotationChanged = QtCore.pyqtSignal(int)

    def __init__(self, parent=None):
        super(GLWidget, self).__init__(parent)
        self.goal_fps = 60.0
        self.avg_frametime = 0.1
        self.avg_fps = 10.0
        self.TTime = time.time()

        self.machine = Machine()
        self.machine.physics_tick(0.01)
        self.MOVE_OBJECT= False
        self.MOVE_FLOOR = True


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

    def setXRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.xRot:
            self.xRot = angle

    def setYRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.yRot:
            self.yRot = angle

    def setZRotation(self, angle):
        self.normalizeAngle(angle)
        if angle != self.zRot:
            self.zRot = angle

    def setXPosition(self, dx):
        self.xPos += dx/100.0

    def setYPosition(self, dy):
        self.yPos += dy/100.0

    def setZoom(self, change):
        if change < 0:
            self.zoomLevel -= (1.0 + abs(self.zoomLevel)**0.5)
        if change > 0:
            self.zoomLevel += (1.0 + abs(self.zoomLevel)**0.5)

    def toRadians(self, degree):
        return degree*0.017453292519943*(1.0/16)

    def initializeGL(self):
        print "INIT"
        lightPos = (5.0, 5.0, 10.0, 1.0)
        reflectance1 = (0.8, 0.1, 0.0, 1.0)
        reflectance2 = (0.0, 0.8, 0.2, 1.0)
        reflectance3 = (0.2, 0.2, 1.0, 1.0)


        glLightfv(GL_LIGHT0, GL_POSITION, lightPos)
        glEnable(GL_LIGHTING)
        glEnable(GL_LIGHT0)
        glEnable(GL_DEPTH_TEST)

        #glLightfv(GL_LIGHT0, GL_POSITION,  (-40, 200, 100, 0.0))
        #glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
        #glLightfv(GL_LIGHT0, GL_DIFFUSE, (0.5, 0.5, 0.5, 1.0))
        #glEnable(GL_LIGHT0)
        #glEnable(GL_LIGHTING)
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
        radians = self.toRadians(np.array([self.zRot, self.xRot]))
        x = math.cos(radians[0])*self.xPos + math.sin(radians[0])*self.yPos
        y = math.sin(radians[0])*self.xPos + math.cos(radians[0])*self.yPos
        z = math.sin(radians[1])*self.yPos

        glTranslate(0.0, 0.0, self.zoomLevel)
        glRotate(self.xRot / 16.0, 1.0, 0.0, 0.0)
        glRotate(self.yRot / 16.0, 0.0, 1.0, 0.0)
        glRotate(self.zRot / 16.0, 0.0, 0.0, 1.0)
        glTranslate(x*10, -y*10, -z*10)



        tile_r = 10.39232 # = 5.196160*2
        downrange_x = 1*self.machine.P[0]*self.MOVE_FLOOR
        downrange_y = 1*self.machine.P[1]*self.MOVE_FLOOR
        glPushMatrix()
        glTranslate(0.0, 0.0, 0.2)
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
        viewport = (1000,700)

        #glViewport((width - side) // 2, (height - side) // 2, side, side)
        glViewport(0,0, viewport[0], viewport[1])

        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        width, height = viewport
        gluPerspective(80.0, width/float(height), 1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        glTranslated(0.0, 0.0, -30.0)

    def mousePressEvent(self, event):
        self.lastPos = event.pos()

    def wheelEvent(self,event):
        tick = event.delta()/120
        self.setZoom(tick)

    def mouseMoveEvent(self, event):
        dx = event.x() - self.lastPos.x()
        dy = event.y() - self.lastPos.y()

        if event.buttons() & QtCore.Qt.LeftButton:
            self.setXRotation(self.xRot + 8 * dy)
            self.setZRotation(self.zRot + 8 * dx)
        elif event.buttons() & QtCore.Qt.RightButton:
            self.setXPosition(8 * dx)
            self.setYPosition(8 * -dy)

        self.lastPos = event.pos()


    def advance(self):
        self.updateFPStime()
        self.machine.physics_tick(self.avg_frametime)
        self.updateGL()



    def normalizeAngle(self, angle):
        while (angle < 0):
            angle += 360 * 16

        while (angle > 360 * 16):
            angle -= 360 * 16



    def drawMachine(self, machine, hull, mainmotor, sidemotor):
        pos, dir = machine.get_hull_pos_and_ax_angle()
        ax0, deg0 = dir

        glPushMatrix()
        glTranslate(-pos[0]*self.MOVE_OBJECT,-pos[1]*self.MOVE_OBJECT, -pos[2])

        glPushMatrix()
        glRotate(deg0, ax0[0], ax0[1], ax0[2])
        glCallList(hull.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(1)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(-e_pos[0]*2, -e_pos[1]*2, -e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(2)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(-e_pos[0]*2, -e_pos[1]*2, -e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(3)
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(-e_pos[0]*2, -e_pos[1]*2, -e_pos[2]*2)
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
