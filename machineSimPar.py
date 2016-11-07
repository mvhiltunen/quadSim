import numpy as np
import random, time
import constants as C
from multiprocessing import Process, Queue, Value, Array, RawValue, Manager
import multiprocessing

class MachineP(Process):
    def __init__(self, command_queue=None, status_duct=None, parameters=None):
        super(MachineP, self).__init__()
        self.command_queue = command_queue
        self.result_duct = status_duct
        self.parameters = parameters
        if type(status_duct) == multiprocessing.managers.DictProxy:
            self.transmit_mode = "dict"
        elif type(status_duct) == multiprocessing.queues.Queue:
            self.transmit_mode = "queue"

        _accuracy = np.float64
        self.V_log = [np.array([0.0,0.0,0.0], _accuracy)]
        self.A_apx = np.array([0.0, 0.0, 0.0], _accuracy)

        self.z = np.array([0.0, 0.0, 1.0], _accuracy)
        self.x = np.array([1.0, 0.0, 0.0], _accuracy)
        self.y = np.array([0.0, 1.0, 0.0], _accuracy)
        self.g = -self.z*C.g

        self.inner_E1_pos = np.array([0.0, (0.8 + C.R1), 0.0], _accuracy)
        self.inner_E2_pos = np.array([0.0, -(0.8 + C.R1), 0.0], _accuracy)
        self.inner_E3_pos = np.array([(0.8 + C.R2), 0.0, 0.0], _accuracy)
        self.inner_E4_pos = np.array([-(0.8 + C.R2), 0.0, 0.0], _accuracy)

        self.external_E1_pos = self.inner_E1_pos.copy()
        self.external_E2_pos = self.inner_E2_pos.copy()
        self.external_E3_pos = self.inner_E3_pos.copy()
        self.external_E4_pos = self.inner_E4_pos.copy()

        self.P = np.array([0.0,0.0,1.0], _accuracy)
        self.V = np.array([0.0,0.0,0.0], _accuracy)
        self.W = np.array([0.0,0.0,0.0], _accuracy)

        self.ROT_M = C.rotation_matrix(self.z, 0.0)

        self.inner_E1_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E2_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E3_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E4_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))

        self.external_E1_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E2_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E3_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E4_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.update_external_engine_directions()

        adjust = 1.00
        self.E1_pwr = 0.153 * adjust
        self.E2_pwr = 0.153 * adjust
        self.E3_pwr = 0.1452 * adjust
        self.E4_pwr = 0.1452 * adjust

        self.legal_commands = {"stop":True,
                               "pause":True,
                               "set_up":True,
                               "steer":True,
                               "give_full_state":True}
        self.ticks = 0
        self.eval_tick = 0
        self.next_command_resolve = 0
        self.next_frametime_eval = 0
        self.next_update = 0
        self.on = False
        self.paused = False
        self.simulation_time = time.time()
        self.dt = 0.01
        self.half_dt = self.dt / 2
        self.min_dt = 0.003
        self.frametime_eval_time = 0.1
        self.update_time = 0.01
        if self.parameters:
            self.min_dt = self.parameters["min_dt"]
            self.frametime_eval_time = self.parameters["frametime_eval_time"]
            self.update_time = self.parameters["update_time"]
        self.frametime_eval_interval = 10
        self.update_interval = 2
        self.command_resove_interval = 4
        self.offset_list = np.zeros(100, np.float32)
        self.testing = True


        self.waits = 0
        self.nowaits = 0


    def physics_tick(self, t):
        self.simulation_time += t
        self.ticks += 1

        #Calculate Forces-------------------------
        T1 = C.get_thrust(1, self.E1_pwr)
        T2 = C.get_thrust(1, self.E2_pwr)
        T3 = C.get_thrust(2, self.E3_pwr)
        T4 = C.get_thrust(2, self.E4_pwr)

        F1 = T1 * self.external_E1_dir
        F2 = T2 * self.external_E2_dir
        F3 = T3 * self.external_E3_dir
        F4 = T4 * self.external_E4_dir

        I1 = F1 * t
        I2 = F2 * t
        I3 = F3 * t
        I4 = F4 * t
        I = I1+I2+I3+I4
        #------------------------------------------

        #Calculate torques and rotation speed------
        TQ1 = C.get_torq(self.external_E1_pos, F1)
        TQ2 = C.get_torq(self.external_E2_pos, F2)
        TQ3 = C.get_torq(self.external_E3_pos, F3)
        TQ4 = C.get_torq(self.external_E4_pos, F4)
        TQ = TQ1 + TQ2 + TQ3 + TQ4
        tq = C.get_len(TQ)
        if tq:
            eTQ = C.unitize(TQ)
            J = C.get_len(np.cross(eTQ,self.y)) * C.M/2 * (C.R1+0.8)**2
            J += C.get_len(np.cross(eTQ,self.x)) * C.M/2 * (C.R2+0.8)**2
            delta_L = t * TQ
            delta_w = delta_L/J
            self.W += delta_w
        #------------------------------------------

        self.ROT_M = np.dot(C.rotation_matrix(self.W, C.get_len(self.W) * t), self.ROT_M)
        self.reset_rotation_matrix_length()

        self.update_external_engine_positions()

        self.update_external_engine_directions()

        self.V += I / C.M
        self.V += self.g * t
        if self.P[2] <= 0.0:
            self.V[2] = max(0.0, self.V[2])

        self.P += t * self.V
        if self.P[2] < 0.0:
            self.P[2] = 0.0
            self.V *= 0.9

        tests = 1
        if tests:
            #if random.random() > 0.999:
                #print "dir:",self.external_E1_dir
                #print "V:", self.V
            self.inner_E1_dir = C.unitize(np.array([0.27 * np.cos(self.ticks * self.dt + 1.5*2), 0.0, 1.0]))
            self.inner_E2_dir = C.unitize(np.array([0.27 * np.cos(self.ticks * self.dt + 1.5*2), 0.0, 1.0]))



    def projected_speed_in(self, T):
        return self.V + self.A_apx * T

    def extrapolate_position(self, T):
        extrap = self.P + self.V*T + 0.5*self.A_apx*T*T
        return extrap

    def approximate_time_to(self, pos, dimension):
        delta = pos - self.P[dimension]
        v = self.V[dimension]
        a = self.A_apx[dimension]
        s1 = (-v + np.sqrt(v**2 + 2.0*a*delta))/(a)
        s2 = (-v - np.sqrt(v**2 + 2.0*a*delta))/(a)
        if s1 > 0:
            return s1
        elif s2 > 0:
            return s2
        else:
            return False

    def adjust_total_engine_power(self, coeff):
        self.E1_pwr = self.rise(self.E1_pwr, coeff)
        self.E2_pwr = self.rise(self.E2_pwr, coeff)
        self.E3_pwr = self.rise(self.E3_pwr, coeff)
        self.E4_pwr = self.rise(self.E4_pwr, coeff)


    def rise(self, x, amount=None):
        if not amount:
            amount = self.dt
        if x <= 0.0:
            x = 0.01
        x *= (1.00 + amount)
        x = min(x, 1.0)
        return x

    def lower(self, x, amount=None):
        if not amount:
            amount = self.dt
        if x <= 0.0:
            return 0.0
        x /= (1.00 + amount)
        x = min(x, 1.0)
        return x

    def update_external_engine_positions(self):
        self.external_E1_pos = np.dot(self.ROT_M, self.inner_E1_pos)
        self.external_E2_pos = np.dot(self.ROT_M, self.inner_E2_pos)
        self.external_E3_pos = np.dot(self.ROT_M, self.inner_E3_pos)
        self.external_E4_pos = np.dot(self.ROT_M, self.inner_E4_pos)

    def update_external_engine_directions(self):
        self.external_E1_dir = np.dot(self.ROT_M, self.inner_E1_dir)
        self.external_E2_dir = np.dot(self.ROT_M, self.inner_E2_dir)
        self.external_E3_dir = np.dot(self.ROT_M, self.inner_E3_dir)
        self.external_E4_dir = np.dot(self.ROT_M, self.inner_E4_dir)

    def reset_rotation_matrix_length(self):
        axis, angle = C.axis_angle(self.ROT_M)
        self.ROT_M = C.rotation_matrix(axis, angle)


    def get_hull_pos_and_ax_angle(self):
        ax, angle = C.axis_angle(self.ROT_M)
        angle *= 57.30659025
        return self.P, (ax, angle)


    def get_engine_pos_and_ax_angle(self, engine_i):
        if engine_i == 1:
            pos = self.external_E1_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.external_E1_dir)
            angle = angle*57.30659025
        elif engine_i == 2:
            pos = self.external_E2_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.external_E2_dir)
            angle = angle*57.30659025
        elif engine_i == 3:
            pos = self.external_E3_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.external_E3_dir)
            angle = angle*57.30659025
        elif engine_i == 4:
            pos = self.external_E4_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.external_E4_dir)
            angle = angle*57.30659025
        return pos, (axis, angle)


    def send_full_state(self):
        d = dict()
        d["P"] = self.P
        d["V"] = self.V
        d["W"] = self.W
        d["ROT_M"] = self.ROT_M
        d["A_apx"] = self.A_apx
        d["E1_pos"] = self.external_E1_pos
        d["E1_dir"] = self.inner_E1_dir
        d["E1_pwr"] = self.E1_pwr
        d["E2_pos"] = self.external_E2_pos
        d["E2_dir"] = self.inner_E2_dir
        d["E2_pwr"] = self.E2_pwr
        d["E3_pos"] = self.external_E3_pos
        d["E3_dir"] = self.inner_E3_dir
        d["E3_pwr"] = self.E3_pwr
        d["E4_pos"] = self.external_E4_pos
        d["E4_dir"] = self.inner_E4_dir
        d["E4_pwr"] = self.E4_pwr
        return d


    def get_draw_info(self):
        d = dict()
        d["hull_pos"], d["hull_ax_angle"] = self.get_hull_pos_and_ax_angle()
        d["E1_pos"], d["E1_ax_angle"] = self.get_engine_pos_and_ax_angle(1)
        d["E2_pos"], d["E2_ax_angle"] = self.get_engine_pos_and_ax_angle(2)
        d["E3_pos"], d["E3_ax_angle"] = self.get_engine_pos_and_ax_angle(3)
        d["E4_pos"], d["E4_ax_angle"] = self.get_engine_pos_and_ax_angle(4)
        return d

    def update_results(self):
        d = self.get_draw_info()
        if self.transmit_mode == "dict":
            self.result_duct["draw_info"] = d
        elif self.transmit_mode == "queue":
            self.result_duct.put(d, False)
        self.next_update = self.ticks + self.update_interval

    def stop(self):
        self.on = False

    def pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.simulation_time = time.time()

    def resolve_commands(self):
        while not self.command_queue.empty():
            command = self.command_queue.get()
            self.execute_cmd(command)
        self.next_command_resolve = self.ticks+self.command_resove_interval

    def execute_cmd(self, command):
        if command[0] in self.legal_commands:
            self.__getattribute__(command[0])(*command[1])


    def run(self):
        C.highpriority()
        self.ticks = 0
        self.eval_tick = 0
        self.dt = 0.01
        self.min_dt = 0.00025               #PP
        self.update_time = 0.01             #PP
        self.frametime_eval_time = 0.1      #PP
        self.frametime_eval_interval = int(self.frametime_eval_time/self.dt)+1
        self.simulation_time = time.time()
        self.on = True
        self.half_dt = self.dt/2
        while self.on:
            offset = self.simulation_time - time.time()
            if offset > self.dt:
                self.waits += 1
                time.sleep(offset*0.9)
            else:
                self.nowaits += 1
            self.physics_tick(self.dt)
            if self.ticks >= self.next_command_resolve:
                self.resolve_commands()
            if self.ticks >= self.next_update:
                self.update_results()
            if self.ticks >= self.next_frametime_eval:
                self.update_frametime()
            while self.paused:
                time.sleep(0.1)
                self.resolve_commands()

        self.kill_report()


    def update_frametime(self):
        self.eval_tick += 1
        #MEASURE OFFSET AND ADJUST DT
        offset = self.simulation_time - time.time()
        self.offset_list[self.eval_tick % 100] = abs(offset)
        if offset > 0:
            gain_coeff = abs(offset / self.dt)
            gain_coeff = min(0.9, gain_coeff)
            self.dt = max(self.min_dt, (1.0-gain_coeff)*self.dt)
        elif offset < 0:
            gain = offset / self.frametime_eval_interval
            gain_coeff = abs(gain / self.dt)
            gain_coeff = min(0.9, gain_coeff)           #PP
            self.dt *= (1.0 + gain_coeff)
        self.half_dt = self.dt / 2
        #UPDATE INTERVAL VALUES ACCORDING TO NEW DT
        self.update_interval = int(self.update_time / self.dt)
        self.command_resove_interval = self.update_interval * 2
        self.frametime_eval_interval = int(self.frametime_eval_time/self.dt)+1
        self.next_frametime_eval = self.ticks + self.frametime_eval_interval
        if self.eval_tick % 10 == 0 and self.testing:
            print "dt:",self.dt
            print "Offset:", offset   #remove
            print "update_interval:", self.update_interval
            print ""


    def kill_report(self):
        k_report = dict()
        avg_offset = sum(self.offset_list)/float(len(self.offset_list)) #remove
        k_report["avg_offset"] = avg_offset
        k_report["offset_list"] = self.offset_list
        k_report["dt"] = self.dt
        k_report["waits"] = self.waits
        k_report["nowaits"] = self.nowaits
        if self.transmit_mode == "dict":
            self.result_duct["kill_report"] = k_report
        elif self.transmit_mode == "queue":
            self.result_duct.put(k_report, False)



if __name__ == '__main__':
    machine_parameters ={"frametime_eval_time":0.1,
                         "min_dt":0.00025,
                         "update_time":0.01,
                         "max_gain_coeff":0.9}
    manager = Manager()
    status = manager.dict()
    status_que = Queue(1000)
    command_que = Queue(100)
    kill_cmd = ["stop", []]

    machine = MachineP(command_queue=command_que, status_duct=status, parameters=machine_parameters)
    print "start parallelisation..."
    machine.start()
    time.sleep(21)
    command_que.put(kill_cmd)
    time.sleep(0.1)
    k_report = status["kill_report"]
    print "Kill report:"
    for p in k_report.items():
        print p
    print "Finished"



















