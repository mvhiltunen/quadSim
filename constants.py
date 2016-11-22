import numpy as np
import random, math, sys, os
import multiprocessing

def inverse_dict(d):
    dd = {}
    for i in d:
        dd[d[i]] = i
    return dd

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
drag_coeff = 0.7
drag_constant = -0.75*drag_coeff*face_area

max_power = 12000.0
efficiencies = {1:0.196, 2:0.137}
payload = 0.0

grav = g*np.array([0.0,0.0,-1.0])*M

identity = np.asarray([[1.0, 0.0, 0.0],
                       [0.0, 1.0, 0.0],
                       [0.0, 0.0, 1.0]], np.float64)

default_parameters = {"mode":"parallel",
                      "min_dt":0.00025,
                      "goal_fps":60,
                      "timestep_eval_frequency":10.0,
                      "update_frequency":100.0,
                      "control_frequency":50.0,
                      "control_sharpness":97.0,
                      "MOVE_OBJECT":False,
                      "MOVE_FLOOR":False,
                      "dt_relaxation_coeff":0.9,
                      "testing":False}

control_keys_to_codes = {"W":87, "A":65, "S":83, "D":68, "UP":16777235, "DOWN":16777237,
                     "RIGHT":16777236, "LEFT":16777234, "SPACE":32, "CTRL":16777249}
control_codes_to_keys = inverse_dict(control_keys_to_codes)

main_keys_to_codes = {"P":80,"C":67}
main_codes_to_keys = inverse_dict(main_keys_to_codes)



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

def get_area_M(v, ROT_M):
    e = unitize(v)
    z = np.dot(ROT_M, ez)
    return face_area * np.dot(e, z)

def get_rel_facing_M(v, ROT_M):
    e = unitize(v)
    z = np.dot(ROT_M, ez)
    return max(np.dot(e, z), 0.04)

def get_len(a):
    return math.sqrt(np.dot(a, a))

def get_speed(v):
    return np.sqrt((v*v).sum())

def get_drag(v, ROT_M):
    return v*v*drag_constant*get_rel_facing_M(v, ROT_M)

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

def rotate_vector(V1, V2, )



def highpriority():
    """ Set the priority of the process to above-normal."""
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

def compose_control_state():
    D = {}
    D["E1_pwr"] = multiprocessing.Value('d')
    D["E2_pwr"] = multiprocessing.Value('d')
    D["E3_pwr"] = multiprocessing.Value('d')
    D["E4_pwr"] = multiprocessing.Value('d')
    D["E1_dir"] = multiprocessing.Array('d', 3)
    D["E2_dir"] = multiprocessing.Array('d', 3)
    D["E3_dir"] = multiprocessing.Array('d', 3)
    D["E4_dir"] = multiprocessing.Array('d', 3)
    return D


def getResolution(coeff):
    rez = fullHD.copy()
    rez *= float(coeff)
    return rez[0], rez[1]






