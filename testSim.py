import constants
import numpy as np
import random, time














class Sim():
    def __init__(self):
        self.z = np.array([0.0, 0.0, 1.0])
        self.x = np.array([1.0, 0.0, 0.0])
        self.y = np.array([0.0, 1.0, 0.0])

        self.POS = np.array([0.0,0.0,0.0])
        self.DIR = np.array([0.0,0.0,1.0])
        self.ATT = np.array([0.0,0.0,0.0])

        self.V = np.array([0.0,0.0,0.0])
        self.W = np.array([0.0,0.0,0.0])


        self.tick = 0.0
        self.throttle = 0.0

    def tick_forward(self, t):
        self.tick += 1
        if random.random() < (1.0/(60*20)):
            self.V[2] -= 2

        self.POS = self.POS + self.V*t

        if self.POS[2] <= 0.0:
            self.V[0] = self.V[0] * 0.9
            self.V[1] = self.V[1] * 0.9
        self.POS[2] = max(0.0, self.POS[2])


        ## rotations
        '''
        self.W[0] += (random.random()-0.4)*2*t
        self.W[1] += (random.random()-0.5)*2*t
        self.W[2] += (random.random()-0.5)*2*t

        self.ATT += self.W*t
        self.DIR = constants.DAS_ROTATE(self.z, )

        ax = constants.unitize(self.ATT)
        d = constants.get_len(self.ATT)
        '''
        self.turn_to_x = np.array([0.0, 1.0, 0.0])
        self.turn_to_y = np.array([1.0, 0.0, 0.0])

        rx = self.turn_to_x
        ry = self.turn_to_y

        dH = self.POS[2] - 5
        vH = self.V[2]
        exH2 = self.POS[2] + vH * 2.0
        exH1 = self.POS[2] + vH * 1.0
        exH05 = self.POS[2] + vH * 0.5
        exH01 = self.POS[2] + vH * 0.1
        #exp = dH/vH


        if exH2 > 5:
            self.throttle *= 0.99 - abs(dH)*0.1

        if exH05 > 5:
           self.throttle *= 1.0 - abs(dH)*0.00

        if exH01 > 5:
           self.throttle *= 1.0 - abs(dH)*0.00

        if exH2 < 5:
            self.throttle *= 1.001 + abs(dH)*0.1
            if self.throttle < 0.5:
                self.throttle += 0.1

        if exH05 < 5:
           self.throttle *= 1.0 + abs(dH)*0.00

        if exH01 > 5:
           self.throttle *= 1.0 - abs(dH)*0.00

        if self.POS[0] > 1 and self.V[0] > -0.5:
            self.DIR = constants.DAS_ROTATE(self.DIR, -rx*0.06)

        if self.POS[0] < -1 and self.V[0] < 0.5:
            self.DIR = constants.DAS_ROTATE(self.DIR, rx*0.06)



        #self.DIR = np.array([0.5*np.cos(self.tick*0.03), 0.0,  1.0])

        #self.DIR = constants.unitize(np.array([0.22, 0.0, 1.0]))
        self.DIR = constants.unitize(self.DIR)


        self.throttle = min(1.0, self.throttle)
        dv = self.DIR*11.5*t*self.throttle

        self.V += dv
        self.V += -self.z*9.81*t

    def get_pos_and_att(self):
        dir = constants.unitize(self.DIR)
        deg = np.arccos(np.dot(dir, self.z))
        deg = deg * 57.30659025
        ax = np.cross(self.z, dir)
        if dir[2] < 0:
            deg += np.pi/2
        return self.POS, (deg, ax)


if __name__ == '__main__':
    S = Sim()
    tt  = time.time()
    t = 1.0/60
    for i in range(60*9):
        S.tick_forward(t)
    tt = time.time() - tt
    p, att = S.get_pos_and_att()
    print p
    print att
    print tt