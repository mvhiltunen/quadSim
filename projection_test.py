from constants import unitize
import numpy as np
import random, math

def get_len(a):
    return np.sqrt((a*a).sum())

def get_random_normal(e):
    d = np.array([0.0,0.0,0.0])
    '''
    swp = 0
    if e[1] == 0:
        swp = 1
        e[0], e[1] = e[1], e[0]

    X = (e[2]/e[1])**2
    d[0] = 0.0
    d[1] = (X/(1+X))**0.5
    d[2] = (1-(d[1]**2))**0.5
    '''
    d[0] = 0.0
    d[1] = e[2]
    d[2] = -e[1]
    d = d/get_len(d)
    return d


def get_fixed_normal(e1, e2):
    n = np.cross(e1,e2)
    n = n/get_len(n)
    return n


def get_random_spot_on_disc(P, n1,n2, R):
    x = 0
    y = 0
    rr = 2
    while rr > 1:
        x = random.random()*2 -1
        y = random.random()*2 -1
        rr = (x*x+y*y)**0.5
    rx = x
    ry = y

    p = P + n1*rx + n2*ry
    return p, rx, ry


def get_xy_intersect_point(p, e):
    r = -(p[2]/e[2])
    x = p[0] + r*e[0]
    y = p[1] + r*e[1]
    return np.array((x,y))




def give_vector(x):
    v = np.array([random.random(),random.random(),random.random()])
    while 0 in v:
        v = np.array([random.random(),random.random(),random.random()])
    v = x* v/get_len(v)
    return v


def get_hypo_1(v):
    ev = v/get_len(v)
    return (1-ev[0])*(1-ev[1])


def get_hypo_2(v, v2): ##CORRECT
    ev = v/get_len(v)
    ev2 = v2/get_len(v2)
    return ev[2]

N_TESTS = 3
N_BEAMS = 70000
z = np.array([0.0,0.0,1.0])


def testi():


    for i in range(N_TESTS):
        v = give_vector(3)
        #v = np.array([0,0,1.0])
        ev = v/get_len(v)
        rev = -ev
        n1 = get_random_normal(v)


        n2 = get_fixed_normal(v, n1)

        IN_BIN = 0
        for j in range(N_BEAMS):
            p = get_random_spot_on_disc(v,n1,n2,1.0)[0]
            assert(np.dot(v,n1)<0.00001)
            assert(np.dot(v,n2)<0.00001)
            assert(np.dot(n1,n2)<0.00001)
            assert(-0.00001<get_len(rev)-1<0.00001)
            intersect = get_xy_intersect_point(p, rev)
            l = get_len(intersect)
            if l < 1:
                IN_BIN += 1

        ratio = IN_BIN/float(N_BEAMS)
        print v
        print "exp:",ratio, " Hypo2:",get_hypo_2(v, z)
        print ""


def draw():
    z = np.array([0.0,0.0,1.0])
    arr = np.zeros(shape=(50,50))
    v = give_vector(3)
    print v
    ev = v/get_len(v)
    rev = -ev
    n1 = get_random_normal(v)
    n2 = get_fixed_normal(v, n1)
    IN_BIN = 0
    for j in range(N_BEAMS):
        p, rx, ry = get_random_spot_on_disc(v,n1,n2,1.0)


        pix_x = int(round(rx*25.0))+24
        pix_y = int(round(ry*25.0))+24
        assert(np.dot(v,n1)<0.00001)
        assert(np.dot(v,n2)<0.00001)
        assert(np.dot(n1,n2)<0.00001)
        assert(-0.00001<get_len(rev)-1<0.00001)
        intersect = get_xy_intersect_point(p, rev)
        l = get_len(intersect)
        if l < 1:
            arr[pix_x,pix_y] = 1
    for a in arr:
        for b in a:
            if b:
                print "X",
            else:
                print " ",

        print " "


def DAS_ROTATE(v, a, d):

    row1 = np.array([np.cos(d)+a[0]*a[0]*(1.0-np.cos(d)),   a[0]*a[1]*(1.0-np.cos(d))-a[2]*np.sin(d),    a[0]*a[2]*(1.0-np.cos(d))+a[1]*np.sin(d)])

    row2 = np.array([a[1]*a[0]*(1.0-np.cos(d))+a[2]*np.sin(d),   np.cos(d)+a[1]*a[1]*(1.0-np.cos(d)),    a[1]*a[2]*(1.0-np.cos(d))-a[0]*np.sin(d)])

    row3 = np.array([a[2]*a[0]*(1.0-np.cos(d))-a[1]*np.sin(d),   a[2]*a[1]*(1.0-np.cos(d))+a[0]*np.sin(d),    np.cos(d)+a[2]*a[2]*(1.0-np.cos(d))])

    MM = np.array([  row1  ,
                     row2  ,
                     row3  ])

    return np.dot(MM, v)


def rotate():

    degx = np.pi/2
    degy = np.pi/2
    degz = 0.0

    MX = np.array( [[1.0,          0.0,          0.0],
                    [0.0,  np.cos(degx), -np.sin(degx)],
                    [0.0,  np.sin(degx),  np.cos(degx)]])

    MY = np.array( [[np.cos(degy),  0.0,  np.sin(degy)],
                    [0.0,          1.0,          0.0],
                    [-np.sin(degy), 0.0,  np.cos(degy)]])

    MZ = np.array( [[np.cos(degz),  -np.sin(degz),  0.0],
                    [np.sin(degz),  np.cos(degz),   0.0],
                    [0.0,           0.0,         1.0]])


    def rot_x(A, a):
        B = [A[0],  math.sin(a)*A[2]+math.cos(a)*A[1],  math.sin(a)*A[1]+math.cos(a)*A[2]]
        return B

    def rot_y(B, b):
        C = [math.sin(b)*B[2]+math.cos(b)*B[0],  B[1],  math.sin(b)*B[0]+math.cos(b)*B[2]]
        return C

    def rot_z(C, c):
        D = [math.sin(c)*C[1]+math.cos(c)*C[0],  math.sin(c)*C[0]+math.cos(c)*C[1],  C[2]]
        return D

    def ROTZ(V, deg):
        M = np.array( [[np.cos(deg),  -np.sin(deg),  0.0],
                       [np.sin(deg),  np.cos(deg),   0.0],
                       [0.0,           0.0,         1.0]])
        return np.dot(M, V)


    def ROTY(V, deg):
        M = np.array( [[np.cos(deg),  0.0,  np.sin(deg)],
                       [0.0,          1.0,          0.0],
                       [-np.sin(deg), 0.0,  np.cos(deg)]])
        return np.dot(M, V)

    def ROTX(V, deg):
        M = np.array( [[1.0,          0.0,          0.0],
                       [0.0,  np.cos(deg), -np.sin(deg)],
                       [0.0,  np.sin(deg),  np.cos(deg)]])
        return np.dot(M, V)


    d90 = np.pi/2
    A = np.array([0.0,0.0,1.0], np.float32)
    AA = np.swapaxes(A, 1, 0)
    AAA = np.array([[0.0],
                    [0.0],
                    [1.0]])
    a,b,c = [np.pi/2, np.pi/2, 0*np.pi/2]


    V1 = ROTZ(ROTY(ROTX(A, d90), d90), 0.0)

    R2 = MX.dot(MY)
    R22 = MZ.dot(MY.dot(MX))

    V2 = np.dot(R2, A)
    V22 = np.dot(R22, A)


    v = np.array([0.0,  0.0,  1.0])
    a = unitize(np.array([1.0,  1.0,  0.0]))
    d = np.pi/2
    V3 = DAS_ROTATE(v, a, d)



    print A
    print AAA
    print ""
    print ""
    print V1
    print ""
    print ""
    print V2
    print V22
    print ""
    print ""
    print V3

rotate()




















