import numpy as np
import random, math

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



def get_angle_ax_for_dirs(Dir1, Dir2):
    angle = np.arccos(np.dot(Dir1, Dir2))
    angle = angle
    ax = np.cross(Dir1, Dir2)
    return (angle, ax)






if __name__ == '__main__':
    v = np.array([1.0, 0.0 ,0.0])
    identity = rotation_matrix(v, 0.0)
    RM = identity.copy()

    ax = np.array([0.0, 1.0 ,1.0])
    deg = 0.01 * np.pi*2
    matrix0  = rotation_matrix(ax, deg)

    for i in range(19):
        RM = np.dot(matrix0, RM)
        if i%4 == 0:
            x,a = axis_angle(RM)
            RM = rotation_matrix(unitize(x)*(random.random()+1.0), a)
        rotated_v = np.dot(RM, v)

        #print "original v:", v
        print "original v leng:", get_len(v)
        #print "rotated_v:", rotated_v
        print "rotated_v leng:", get_len( rotated_v)












