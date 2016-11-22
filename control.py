import constants as C
import random, time ,math
import numpy as np
from multiprocessing import Process, Queue, Manager


class Controller:#Process?
    def __init__(self, status_duct, control_queue, parameters):
        self.params = parameters
        self.status_duct = status_duct
        self.control_queue = control_queue
        self.state = None
        self.motor_pwr_names = {0:"E0P", 1:"E1P", 2:"E2P", 3:"E3P"}
        self.motor_dir_names = {0:"E0D", 1:"E1D", 2:"E2D", 3:"E3D"}
        self.on = False
        self.frequency = self.params["control_frequency"]

    def start(self):
        self.on = True
        self.run()

    def stop(self):
        self.on = False

    def run(self):
        while self.on:
            #do shit
            time.sleep(self.interval)
            pass




    def set_motor_pwr(self, motor, pwr):
        self.control_queue.put( (self.motor_pwr_names[motor], pwr) )

    def set_motor_direction(self, motor, direction):
        self.control_queue.put( (self.motor_dir_names[motor], direction) )


    def giveState(self, state):
        pass

    def getState(self):
        pass

    def control_tick(self, t):
        pass


    def projected_speed_in(self, V, A, T):
        return V + A * T

    def extrapolate_position(self,P, V, A, T):
        extrap = P + V*T + 0.5*A*T*T
        return extrap

    def approximate_time_to(self, P, V, A, pos, dimension):
        delta = pos - P[dimension]
        v = V[dimension]
        a = A[dimension]
        s1 = (-v + np.sqrt(v**2 + 2.0*a*delta))/(a)
        s2 = (-v - np.sqrt(v**2 + 2.0*a*delta))/(a)
        if s1 > 0:
            return s1
        elif s2 > 0:
            return s2
        else:
            return False


    def rise(self, x, amount):
        if x <= 0.0:
            x = 0.01
        x *= (1.00 + amount)
        x = min(x, 1.0)
        return x


    def lower(self, x, amount):
        if x <= 0.0:
            return 0.0
        x /= (1.00 + amount)
        x = min(x, 1.0)
        return x

