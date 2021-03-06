import numpy as np
import random, time, sys
import constants as C
from multiprocessing import Process, Queue, Manager
import multiprocessing


class MachineP(Process):
    def __init__(self, command_queue=None, status_duct=None, control_queue=None, parameters=None):
        super(MachineP, self).__init__()
        self.command_queue = command_queue
        self.result_duct = status_duct
        self.control_queue = control_queue

        self.parameters = parameters

        _accuracy = np.float64
        self.accuracy = _accuracy
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
        self.A = np.array([0.0, 0.0, 0.0], _accuracy)
        self.extA = np.array([0.0, 0.0, 0.0], _accuracy)
        self.W = np.array([0.0,0.0,0.0], _accuracy)

        self.ROT_M = C.rotation_matrix(self.z, 0.0)
        self.REV_ROT_M = C.rotation_matrix(self.z, 0.0)

        self.inner_E1_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E2_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E3_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.inner_E4_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))

        self.external_E1_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E2_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E3_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.external_E4_dir = C.unitize(np.array([0.0, 0.0, 1.0], _accuracy))
        self.update_external_engine_directions()

        self.E1_pwr = 0.0
        self.E2_pwr = 0.0
        self.E3_pwr = 0.0
        self.E4_pwr = 0.0

        self.legal_commands = {"stop":True, "pause":True,"reset":True}
        self.tick = 0
        self.eval_tick = 0
        self.next_cmd_resolve_tick = 0
        self.next_timestep_eval_tick = 0
        self.next_update_tick = 0
        self.next_control_tick = 0
        self.on = False
        self.paused = False
        self.simulation_time = time.time()
        self.time_dilation = 1.0
        self.dt = 0.01
        self.half_dt = self.dt / 2
        self.min_dt = self.parameters["min_dt"]
        self.timestep_eval_frequency = self.parameters["timestep_eval_frequency"]
        self.update_frequency = self.parameters["update_frequency"]
        self.command_frequency = self.parameters["command_frequency"]
        self.control_frequency = self.parameters["control_frequency"]
        self.power_relaxation = (1.0 - self.parameters["control_sharpness"]) ** (1.0 / self.control_frequency)  #large
        self.power_relaxation_complement = 1.0 - self.power_relaxation #small
        self.engine_rotation_speed = self.parameters["engine_rotation_speed"]
        self.control_state = C.compose_nonparallel_control_state()
        self.timestep_eval_interval = 10
        self.update_interval = 2
        self.cmd_resove_interval = 4
        self.control_interval = 20
        self.offset_list = np.zeros(100, np.float32)
        self.waits = 0
        self.nowaits = 0
        self.testing = self.parameters["testing"]


    def run(self):
        C.highpriority()
        self.tick = 0
        self.eval_tick = 0
        self.timestep_eval_interval = int(1.0/ (self.timestep_eval_frequency * self.dt)) + 1
        self.simulation_time = time.time()
        self.on = True
        while self.on:
            offset = self.simulation_time - time.time()
            if offset > self.dt:
                time.sleep(offset*0.9)
            self.physics_tick(self.dt)
            if self.tick >= self.next_cmd_resolve_tick:
                self.resolve_commands()
            if self.tick >= self.next_update_tick:
                self.update_results()
            if self.tick >= self.next_timestep_eval_tick:
                self.update_timestep()
            if self.tick >= self.next_control_tick:
                self.resolve_control()
            while self.paused:
                time.sleep(0.1)
                self.resolve_commands()
        self.close()


    def reset(self):
        self.P = np.array([0.0, 0.0, 1.0], self.accuracy)
        self.V = np.array([0.0, 0.0, 0.0], self.accuracy)
        self.A = np.array([0.0, 0.0, 0.0], self.accuracy)
        self.extA = np.array([0.0, 0.0, 0.0], self.accuracy)
        self.W = np.array([0.0, 0.0, 0.0], self.accuracy)
        self.ROT_M = C.rotation_matrix(self.z, 0.0)


    def physics_tick(self, t):
        self.simulation_time += t
        t *= self.time_dilation
        self.tick += 1

        #Calculate Forces---------------------------
        T1 = C.get_thrust(1, self.E1_pwr)
        T2 = C.get_thrust(1, self.E2_pwr)
        T3 = C.get_thrust(2, self.E3_pwr)
        T4 = C.get_thrust(2, self.E4_pwr)

        F1 = T1 * self.external_E1_dir
        F2 = T2 * self.external_E2_dir
        F3 = T3 * self.external_E3_dir
        F4 = T4 * self.external_E4_dir

        Fdrag = C.get_drag(self.V, self.ROT_M)

        Ftot = F1+F2+F3+F4+Fdrag
        #if self.tick % 2000 == 0:
            #print "z:",np.dot(self.ROT_M, self.z)
            #print "A:",self.A
            #print "extA:",self.extA
            #print ""
        #--------------------------------------------

        #Calculate torques and rotation speed--------
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
        leng = C.get_len(self.W)+0.03
        shape_coeff = 1+(1-abs((self.W*self.z).sum()/leng))*4
        self.W *= max(0.95, (1 - shape_coeff*t*8.0*(leng**1.0)/C.M))
        #--------------------------------------------

        self.ROT_M = np.dot(C.rotation_matrix(self.W, C.get_len(self.W) * t), self.ROT_M)
        self.reset_rotation_matrix_length()
        self.REV_ROT_M = np.transpose(self.ROT_M)

        self.update_external_engine_positions()
        self.update_external_engine_directions()

        self.A = self.g + Ftot/C.M
        self.extA = np.dot(self.REV_ROT_M, self.A)
        self.V += self.A * t
        if self.P[2] <= 0.0:
            self.V[2] = max(0.0, self.V[2])

        self.P += (t * self.V)
        if self.P[2] < 0.0:
            self.P[2] = 0.0
            self.V *= 0.9



    def update_external_engine_positions(self):
        self.external_E1_pos = np.dot(self.ROT_M, self.inner_E1_pos)
        self.external_E2_pos = np.dot(self.ROT_M, self.inner_E2_pos)
        self.external_E3_pos = np.dot(self.ROT_M, self.inner_E3_pos)
        self.external_E4_pos = np.dot(self.ROT_M, self.inner_E4_pos)

    def update_external_engine_directions(self):
        self.external_E1_dir = C.unitize(np.dot(self.ROT_M, self.inner_E1_dir))
        self.external_E2_dir = C.unitize(np.dot(self.ROT_M, self.inner_E2_dir))
        self.external_E3_dir = C.unitize(np.dot(self.ROT_M, self.inner_E3_dir))
        self.external_E4_dir = C.unitize(np.dot(self.ROT_M, self.inner_E4_dir))

    def reset_rotation_matrix_length(self):
        axis, angle = C.axis_angle(self.ROT_M)
        self.ROT_M = C.rotation_matrix(axis, angle)
        #self.REV_ROT_M = C.rotation_matrix(axis, -angle)


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


    def get_full_state(self):
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

    def get_sensor_data(self):
        d = dict()
        d["a"] = self.extA #+np.random.rand(3)*0.002*self.extA
        d["h"] = self.P[2]
        d["gyro"] = self.W
        return d

    def update_results(self):
        d = self.get_draw_info()
        self.result_duct["state"] = d
        self.next_update_tick = self.tick + self.update_interval

    def stop(self):
        self.on = False

    def pause(self):
        self.paused = not self.paused
        if not self.paused:
            self.simulation_time = time.time()

    def resolve_commands(self):
        while not self.command_queue.empty():
            command = self.command_queue.get()
            if command[0] in self.legal_commands:
                self.__getattribute__(command[0])(*command[1])
        self.next_cmd_resolve_tick = self.tick + self.cmd_resove_interval

    def resolve_control(self):
        control_state = None
        while not self.control_queue.empty():
            control_state = self.control_queue.get()
        if control_state:
            self.control_state = control_state
        self.next_control_tick += self.control_interval
        self.execute_control()

    def execute_control(self):
        self.E1_pwr = self.power_relaxation * self.E1_pwr + self.power_relaxation_complement * self.control_state["E1_pwr"]
        self.E2_pwr = self.power_relaxation * self.E2_pwr + self.power_relaxation_complement * self.control_state["E2_pwr"]
        self.E3_pwr = self.power_relaxation * self.E3_pwr + self.power_relaxation_complement * self.control_state["E3_pwr"]
        self.E4_pwr = self.power_relaxation * self.E4_pwr + self.power_relaxation_complement * self.control_state["E4_pwr"]
        d_rot = self.engine_rotation_speed / self.control_frequency
        self.inner_E1_dir = C.rotate_towards_with_increment(self.inner_E1_dir, self.control_state["E1_dir"], d_rot)
        self.inner_E2_dir = C.rotate_towards_with_increment(self.inner_E2_dir, self.control_state["E2_dir"], d_rot)
        self.inner_E3_dir = C.rotate_towards_with_increment(self.inner_E3_dir, self.control_state["E3_dir"], d_rot)
        self.inner_E4_dir = C.rotate_towards_with_increment(self.inner_E4_dir, self.control_state["E4_dir"], d_rot)


    def update_timestep(self):
        self.eval_tick += 1
        #MEASURE OFFSET AND ADJUST DT
        offset = self.simulation_time - time.time()
        self.offset_list[self.eval_tick % 100] = abs(offset)
        if offset > 0:
            gain_coeff = abs(offset / self.dt)
            gain_coeff = min(0.9, gain_coeff)
            self.dt = max(self.min_dt, (1.0-gain_coeff)*self.dt)
        elif offset < 0:
            gain = offset / self.timestep_eval_interval
            gain_coeff = abs(gain / self.dt)
            gain_coeff = min(0.9, gain_coeff)           #PP
            self.dt *= (1.0 + gain_coeff)
        self.half_dt = self.dt / 2
        #UPDATE INTERVAL VALUES ACCORDING TO NEW DT
        self.update_interval = int(1.0/(self.update_frequency * self.dt))
        self.timestep_eval_interval = int(1.0/ (self.timestep_eval_frequency * self.dt)) + 1
        self.control_interval = int(1.0/ (self.control_frequency * self.dt)) + 1
        self.cmd_resove_interval = int(1.0/ (self.command_frequency * self.dt)) + 1

        self.next_timestep_eval_tick = self.tick + self.timestep_eval_interval
        if self.testing and self.eval_tick % 10 == 0:
            print "dt:",self.dt
            print "Offset:", offset   #remove
            print "update_interval:", self.update_interval
            print "V:", self.V
            print ""


    def kill_report(self):
        k_report = dict()
        avg_offset = sum(self.offset_list)/float(len(self.offset_list)) #remove
        k_report["avg_offset"] = avg_offset
        k_report["offset_list"] = self.offset_list
        k_report["dt"] = self.dt
        k_report["waits"] = self.waits
        k_report["nowaits"] = self.nowaits
        self.result_duct["kill_report"] = k_report
        for k in k_report:
            print k, k_report[k]

    def close(self):
        if self.parameters["testing"]:
            self.kill_report()
        sys.exit(1)


