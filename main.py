#!/usr/bin/env python

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
        self.MOVE_OBJECT = False
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

        self.initializeMachine()

        self.goal_fps = 60.0
        self.goal_steptime = 1.0 / 120.0
        self.framecount = 0

        self.avg_frametime = 0.1
        self.avg_fps = 10.0
        self.TTime = time.time()

        timer = QtCore.QTimer(self)
        timer.timeout.connect(self.advance)
        timer.start(20)

    def initializeMachine(self):
        if self.mode == "single":
            self.machine = Machine()

        elif self.mode == "parallel":
            self.command_que = Queue(1000)
            self.manager = Manager()
            self.status_duct = self.manager.dict()
            self.machine = MachineP(command_queue=self.command_que ,result_duct=self.status_duct,parameters=self.params)


    def updateFPStime(self):
        newtime = time.time()
        frametime = (newtime-self.TTime)/self.framecount
        self.TTime = newtime
        self.avg_frametime = self.avg_frametime*0.5 + frametime*0.5
        self.avg_fps = self.avg_fps*0.5 + 0.5/frametime
        self.framecount = 0

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
        #glLightfv(GL_LIGHT0, GL_AMBIENT, (0.2, 0.2, 0.2, 1.0))
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

        tile_r = 10.39232
        draw_info = self.get_draw_info()
        downrange_x = draw_info["hull_pos"][0]*self.MOVE_FLOOR
        downrange_y = draw_info["hull_pos"][1]*self.MOVE_FLOOR
        glPushMatrix()
        glTranslate(0.0, 0.0, -0.1)
        self.drawFloor(tile=self.hextile_obj, R=10, tile_r=tile_r, pos_x=downrange_x, pos_y=downrange_y) #Floor of hexagonals
        glPopMatrix()

        glPushMatrix()
        glTranslate(0.0, 0.0, 0.0)
        self.drawMachine(draw_info, self.hull_obj, self.mainmotor_obj, self.sidemotor_obj)
        glPopMatrix()
        glPopMatrix()


    def resizeGL(self, width, height):
        side = min(width, height)
        print(width, height)
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
        if self.framecount > 20:
            self.updateFPStime()
        self.keyPressHandle()
        self.machine.physics_tick(self.avg_frametime)
        self.updateGL()

    def advance_machines(self):
        if self.mode == "single":
            self.machine.physics_tick(self.avg_frametime)


    def get_draw_info(self):
        if self.mode == "single":
            return self.machine.get_draw_info()
        elif self.mode == "parallel":
            return self.status_duct["draw_info"]
        else:
            return False

    def drawMachine(self, draw_info, hull, mainmotor, sidemotor):
        pos, ax_angle = draw_info["hull_pos"], draw_info["hull_ax_angle"]
        ax0, angle0 = ax_angle

        glPushMatrix()
        glTranslate(pos[0]*self.MOVE_OBJECT, pos[1]*self.MOVE_OBJECT, pos[2])

        glPushMatrix()
        glRotate(angle0, ax0[0], ax0[1], ax0[2])
        glCallList(hull.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = draw_info["E1_pos"], draw_info["E1_ax_angle"]
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = draw_info["E2_pos"], draw_info["E2_ax_angle"]
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(mainmotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        e_pos, e_ax_angle = draw_info["E3_pos"], draw_info["E3_ax_angle"]
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(sidemotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPushMatrix()
        #e_pos, e_ax_angle = machine.get_engine_pos_and_ax_angle(4)
        e_pos, e_ax_angle = draw_info["E4_pos"], draw_info["E4_ax_angle"]
        e_axis = e_ax_angle[0]
        e_angle = e_ax_angle[1]
        glTranslate(e_pos[0]*2, e_pos[1]*2, e_pos[2]*2)
        glRotate(e_angle, e_axis[0], e_axis[1], e_axis[2])
        glCallList(sidemotor.gl_list)
        #glCallList(stick_obj.gl_list)
        glPopMatrix()

        glPopMatrix()


    def drawFloor(self, tile, R, tile_r, pos_x, pos_y):
        tile_sep = tile_r * 1.1
        c30 = math.cos(0.5235987755)
        s30 = math.sin(0.5235987755)
        glPushMatrix()
        offset_x = pos_x % (2*tile_sep*c30)
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
                    glCallList(tile.gl_list)
                    glPopMatrix()
        glPopMatrix()



if __name__ == '__main__':
    params = {"mode":"single",
              "min_dt":0.00025}
    app = QtGui.QApplication(sys.argv)
    mainWin = SimWidget(params=params)
    mainWin.show()
    sys.exit(app.exec_())

