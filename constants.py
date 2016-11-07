import numpy as np
import random, math, sys, os

#some shit
fullHD = np.array((1920, 1080), np.int32)

#naturals
g = 9.81
d_air = 1.50

ez = np.array([0.0,0.0,1.0])
#machine dependent
scale_factor = 1.0


M = 120*scale_factor
J = M*1.5
R1 = 1.20*scale_factor
R2 = 0.60*scale_factor
H1 = 0.40*scale_factor
L1 = 7.04*scale_factor
L2 = 4.40*scale_factor

E1_center = 80
E2_center = 80
E3_center = 80
E4_center = 80


face_area = 8.5170*scale_factor


max_power = 12000.0
efficiencies = {1:0.196, 2:0.137}
payload = 0.0
form_factor = 0.8

grav = g*np.array([0.0,0.0,-1.0])*M

identity = np.asarray([[1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0],
                       [0.0, 0.0, 1.0]], np.float64)

default_parameters = {"mode":"single",
                      "min_dt":0.00025,
                      "goal_fps":60,
                      "frametime_eval_time":0.1,
                      "update_time":0.01,
                      "dt_relaxation_coeff":0.9}


def unitize(v):
    leng = get_len(v)
    if leng == 0.0:
        return v
    return v/get_len(v)

def get_thrust(engine, power):
    return efficiencies[engine] * power * max_power

def get_area(v, attitude):
    e = v/get_len(v)
    a = attitude/get_len(attitude)
    return face_area * np.dot(e, a)

def get_len(a):
    return math.sqrt(np.dot(a, a))

def get_speed(v):
    return np.sqrt((v*v).sum())

def get_drag(v, attitude):
    return v*v*d_air*form_factor*0.5*get_area(v, attitude)

def get_torq(p, f):
    return np.cross(p,f)


def DAS_ROTATE(v, ax, d=None):  #THIS is a pretty tool.
    if get_len(ax) == 0.0:
        return v
    if d == None:
        d = get_len(ax)
    e_ax = unitize(ax)

    row1 = np.array([np.cos(d) + e_ax[0] * e_ax[0] * (1.0 - np.cos(d)), e_ax[0] * e_ax[1] * (1.0 - np.cos(d)) - e_ax[2] * np.sin(d), e_ax[0] * e_ax[2] * (1.0 - np.cos(d)) + e_ax[1] * np.sin(d)])

    row2 = np.array([e_ax[1] * e_ax[0] * (1.0 - np.cos(d)) + e_ax[2] * np.sin(d), np.cos(d) + e_ax[1] * e_ax[1] * (1.0 - np.cos(d)), e_ax[1] * e_ax[2] * (1.0 - np.cos(d)) - e_ax[0] * np.sin(d)])

    row3 = np.array([e_ax[2] * e_ax[0] * (1.0 - np.cos(d)) - e_ax[1] * np.sin(d), e_ax[2] * e_ax[1] * (1.0 - np.cos(d)) + e_ax[0] * np.sin(d), np.cos(d) + e_ax[2] * e_ax[2] * (1.0 - np.cos(d))])

    MM = np.array([  row1  ,
                     row2  ,
                     row3  ])

    return np.dot(MM, v)



def rotation_matrix(axis, theta):
    """
    Return the rotation matrix associated with counterclockwise rotation about
    the given axis by theta radians.
    """
    axis = np.asarray(axis).copy()
    leng = math.sqrt(np.dot(axis, axis))
    if leng == 0.0:
        return identity.copy()
    axis = axis/leng
    a = math.cos(theta/2.0)
    b, c, d = -axis*math.sin(theta/2.0)
    aa, bb, cc, dd = a*a, b*b, c*c, d*d
    bc, ad, ac, ab, bd, cd = b*c, a*d, a*c, a*b, b*d, c*d
    return np.array([[aa+bb-cc-dd, 2*(bc+ad), 2*(bd-ac)],
                     [2*(bc-ad), aa+cc-bb-dd, 2*(cd+ab)],
                     [2*(bd+ac), 2*(cd-ab), aa+dd-bb-cc]])


def axis_angle(matrix):
    '''
    asdfdasd
    '''
    axis = np.array([matrix[2,1]-matrix[1,2],  matrix[0,2]-matrix[2,0],  matrix[1,0]-matrix[0,1]  ])
    #theta0 = np.arcsin(get_len(axis)/2.0)    #theta measured in other ways. If you encounter problems, maybe this helps
    theta = np.arccos(  (np.trace(matrix)-1.0)/2.0  )

    return axis, theta



def get_ax_angle_for_dirs(Dir1, Dir2):
    angle = np.arccos(np.dot(Dir1, Dir2))
    angle = angle
    axis = np.cross(Dir1, Dir2)
    return axis, angle




def highpriority():
    """ Set the priority of the process to below-normal."""
    try:
        sys.getwindowsversion()
    except:
        isWindows = False
    else:
        isWindows = True

    if isWindows:
        # Based on:
        #   "Recipe 496767: Set Process Priority In Windows" on ActiveState
        #   http://code.activestate.com/recipes/496767/
        import win32api,win32process,win32con

        pid = win32api.GetCurrentProcessId()
        handle = win32api.OpenProcess(win32con.PROCESS_ALL_ACCESS, True, pid)
        #win32process.SetPriorityClass(handle, win32process.REALTIME_PRIORITY_CLASS)
        win32process.SetPriorityClass(handle, win32process.HIGH_PRIORITY_CLASS)
    else:
        import os
        os.nice(1)



def getResolution(coeff):
    rez = fullHD.copy()
    rez *= float(coeff)
    return rez[0], rez[1]






