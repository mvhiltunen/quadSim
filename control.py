import constants as C
import random, time ,math, sys
import numpy as np
from multiprocessing import Process, Queue, Manager


class Controller(Process):#Process?
    def __init__(self, status_duct, control_queue, parameters):
        super(Controller, self).__init__()
        self.params = parameters
        self.status_duct = status_duct
        self.control_queue = control_queue
        self.state = None
        self.saved = dict()
        self.control_state = C.compose_nonparallel_control_state()
        self.machine_state = self.status_duct["state"]
        self.x = np.array([1.0,0.0,0.0],np.float64)
        self.y = np.array([0.0,1.0,0.0],np.float64)
        self.z = np.array([0.0,0.0,1.0],np.float64)

        self.motor_pwr_names = {0:"E0P", 1:"E1P", 2:"E2P", 3:"E3P"}
        self.motor_dir_names = {0:"E0D", 1:"E1D", 2:"E2D", 3:"E3D"}
        self.on = False
        self.paused = False
        self.simtime = time.time()
        self.starttime = None
        self.frequency = self.params["control_frequency"]
        self.interval = 1.0/self.frequency

    def _run(self):
        '''main loop'''
        self.starttime = time.time()
        self.on = True
        while self.on:
            T = time.time()
            self.getState()
            self.control_tick()
            self.putState()
            t = time.time()-T
            time.sleep(self.interval-t)
            while self.paused:
                time.sleep(0.05)
                self.resolve_commands()

    def putState(self):
        '''push commands to machine'''
        self.control_queue.put(self.control_state)

    def getState(self):
        '''get machine state'''
        self.machine_state = self.status_duct["state"]



    def control_tick(self):
        '''Implement controls here'''
        #self.direction_tests()
        self.power(1.2)

    def float_to_y(self):
        self.control_state["E1_dir"] = C.unitize(self.z + self.y * 0.5)
        self.control_state["E2_dir"] = C.unitize(self.z + self.y * 0.5)
        self.control_state["E3_dir"] = C.unitize(self.z + self.x * 0.0)
        self.control_state["E4_dir"] = C.unitize(self.z + self.x * 0.0)
        self.control_state["E1_pwr"] = 0.153 * 0.03
        self.control_state["E2_pwr"] = 0.153 * 0.03
        self.control_state["E3_pwr"] = 0.1452 * 0.5
        self.control_state["E4_pwr"] = 0.1452 * 0.5

    def power(self, scale):
        self.control_state["E1_pwr"] = 0.153 * scale
        self.control_state["E2_pwr"] = 0.1535 * scale
        self.control_state["E3_pwr"] = 0.1452 * scale
        self.control_state["E4_pwr"] = 0.1452 * scale


    def direction_tests(self):
        second = str(int(time.time())/1)[-1]
        if second in ["0", "1"]:
            self.control_state["E1_dir"] = C.unitize(self.z + self.x * 0.5)
            self.control_state["E2_dir"] = C.unitize(self.z + self.x * 0.5)
            self.control_state["E3_dir"] = C.unitize(self.z + self.x * 0.5)
            self.control_state["E4_dir"] = C.unitize(self.z + self.x * 0.5)
        if second in ["2", "3"]:
            self.control_state["E1_dir"] = C.unitize(self.z - self.x * 0.5)
            self.control_state["E2_dir"] = C.unitize(self.z - self.x * 0.5)
            self.control_state["E3_dir"] = C.unitize(self.z - self.x * 0.5)
            self.control_state["E4_dir"] = C.unitize(self.z - self.x * 0.5)
        if second in ["4", "5"]:
            self.control_state["E1_dir"] = C.unitize(self.z + self.y * 0.5)
            self.control_state["E2_dir"] = C.unitize(self.z + self.y * 0.5)
            self.control_state["E3_dir"] = C.unitize(self.z + self.y * 0.5)
            self.control_state["E4_dir"] = C.unitize(self.z + self.y * 0.5)
        if second in ["6", "7"]:
            self.control_state["E1_dir"] = C.unitize(self.z - self.y * 0.5)
            self.control_state["E2_dir"] = C.unitize(self.z - self.y * 0.5)
            self.control_state["E3_dir"] = C.unitize(self.z - self.y * 0.5)
            self.control_state["E4_dir"] = C.unitize(self.z - self.y * 0.5)
        if second in ["8", "9"]:
            self.control_state["E1_dir"] = C.unitize(self.z)
            self.control_state["E2_dir"] = C.unitize(self.z)
            self.control_state["E3_dir"] = C.unitize(self.z)
            self.control_state["E4_dir"] = C.unitize(self.z)


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

    def reset_state(self):
        self.control_state = C.compose_nonparallel_control_state()

    def save_state(self, name):
        self.saved[name] = self.control_state.copy()

    def load_state(self, name):
        self.control_state = self.saved[name].copy()

    def run(self):
        self._run()
        sys.exit(1)

    def pause(self):
        self.paused = not self.paused
        if self.paused:
            pass
        else:
            self.simtime = time.time()

    def stop(self):
        self.on = False

