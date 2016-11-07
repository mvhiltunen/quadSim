import numpy as np
import random, time
import constants as C


class Machine:
    def __init__(self):

        self.V_log = [np.array([0.0,0.0,0.0], np.float64)]
        self.A_apx = np.array([0.0, 0.0, 0.0], np.float64)

        self.z = np.array([0.0, 0.0, 1.0], np.float64)
        self.x = np.array([1.0, 0.0, 0.0], np.float64)
        self.y = np.array([0.0, 1.0, 0.0], np.float64)
        self.g = -self.z*C.g

        self.E1_pos0 = np.array([0.0,(0.8+C.R1),0.0])
        self.E2_pos0 = np.array([0.0,-(0.8+C.R1),0.0])
        self.E3_pos0 = np.array([(0.8+C.R2),0.0,0.0])
        self.E4_pos0 = np.array([-(0.8+C.R2),0.0,0.0])

        self.E1_pos = self.E1_pos0.copy()
        self.E2_pos = self.E2_pos0.copy()
        self.E3_pos = self.E3_pos0.copy()
        self.E4_pos = self.E4_pos0.copy()

        self.P = np.array([0.0,0.0,1.0], np.float64)
        self.V = np.array([0.0,0.0,0.0], np.float64)
        self.W = np.array([0.0,0.0,0.0], np.float64)

        self.ROT_M = C.rotation_matrix(self.z, 0.0)

        self.E1_dir = C.unitize(np.array([0.0, 0.0, 1.0]))
        self.E2_dir = C.unitize(np.array([0.0, 0.0, 1.0]))
        self.E3_dir = C.unitize(np.array([0.0, 0.0, 1.0]))
        self.E4_dir = C.unitize(np.array([0.0, 0.0, 1.0]))

        adjust = 1.0
        self.E1_pwr = 0.153 * adjust
        self.E2_pwr = 0.153 * adjust
        self.E3_pwr = 0.1452 * adjust
        self.E4_pwr = 0.1452 * adjust

        self.ticks = 0
        self.on = False
        self.simulation_time = time.time()
        self.previous_check = time.time()
        self.dt = 0.012

    def reset_time(self):
        self.simulation_time = time.time()


    def physics_tick(self, dt=None):
        self.ticks += 1
        if dt:
            self.simulation_time += dt
            t = dt
        else:
            t = time.time() - self.simulation_time
            t = min(t, 0.05)

        self.P += t*self.V
        if self.P[2] < 0.0:
            self.P[2] = 0.0
            self.V = self.V*0.9

        T1 = C.get_thrust(1, self.E1_pwr)
        T2 = C.get_thrust(1, self.E2_pwr)
        T3 = C.get_thrust(2, self.E3_pwr)
        T4 = C.get_thrust(2, self.E4_pwr)

        F1 = T1 * self.E1_dir
        F2 = T2 * self.E2_dir
        F3 = T3 * self.E3_dir
        F4 = T4 * self.E4_dir

        I1 = F1 * t
        I2 = F2 * t
        I3 = F3 * t
        I4 = F4 * t
        I = I1+I2+I3+I4

        self.V += I/C.M
        self.V += self.g * t
        if self.P[2] <= 0.0:
            self.V[2] = max(0.0, self.V[2])


        self.ROT_M = np.dot(C.rotation_matrix(self.W, C.get_len(self.W)*t),   self.ROT_M)

        self.E1_pos = np.dot(self.ROT_M, self.E1_pos0)
        self.E2_pos = np.dot(self.ROT_M, self.E2_pos0)
        self.E3_pos = np.dot(self.ROT_M, self.E3_pos0)
        self.E4_pos = np.dot(self.ROT_M, self.E4_pos0)

        TQ1 = C.get_torq(self.E1_pos, F1)
        TQ2 = C.get_torq(self.E2_pos, F2)
        TQ3 = C.get_torq(self.E3_pos, F3)
        TQ4 = C.get_torq(self.E4_pos, F4)
        TQ = TQ1 + TQ2 + TQ3 + TQ4
        tq = C.get_len(TQ)
        if tq:
            eTQ = C.unitize(TQ)
            J = C.get_len(np.cross(eTQ,self.y)) * C.M/2 * (C.R1+0.8)**2
            J += C.get_len(np.cross(eTQ,self.x)) * C.M/2 * (C.R2+0.8)**2
            delta_L = t * TQ
            delta_w = delta_L/J
            self.W += delta_w

        self.reset_rotation_matrix_length()

        tests = 1
        if tests:
            self.E1_dir = C.unitize(np.array([-0.27 * np.cos(self.ticks * 0.02 + 1.5), 0.0, 1.0]))
            self.E2_dir = C.unitize(np.array([0.27 * np.cos(self.ticks * 0.02 + 1.5), 0.0, 1.0]))



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




    def unitize_engine_directions(self):
        self.E1_dir = C.unitize(self.E1_dir)
        self.E2_dir = C.unitize(self.E2_dir)
        self.E3_dir = C.unitize(self.E3_dir)
        self.E4_dir = C.unitize(self.E4_dir)

    def reset_rotation_matrix_length(self):
        axle0, angle0 = C.axis_angle(self.ROT_M)
        self.ROT_M = C.rotation_matrix(C.unitize(axle0), angle0)


    def get_hull_pos_and_ax_angle(self):
        ax, angle = C.axis_angle(self.ROT_M)
        angle = angle*57.30659025
        return self.P, (ax, angle)


    def get_engine_pos_and_ax_angle(self, engine_i):
        if engine_i == 1:
            pos = self.E1_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.E1_dir)
            angle = angle*57.30659025
        elif engine_i == 2:
            pos = self.E2_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.E2_dir)
            angle = angle*57.30659025
        elif engine_i == 3:
            pos = self.E3_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.E3_dir)
            angle = angle*57.30659025
        elif engine_i == 4:
            pos = self.E4_pos
            axis, angle = C.get_ax_angle_for_dirs(self.z, self.E4_dir)
            angle = angle*57.30659025
        return pos, (axis, angle)


    def get_full_state(self):
        d = {}
        d["P"] = self.P
        d["V"] = self.V
        d["W"] = self.W
        d["ROT_M"] = self.ROT_M
        d["A_apx"] = self.A_apx
        d["E1_pos"] = self.E1_pos
        d["E1_dir"] = self.E1_dir
        d["E1_pwr"] = self.E1_pwr
        d["E2_pos"] = self.E2_pos
        d["E2_dir"] = self.E2_dir
        d["E2_pwr"] = self.E2_pwr
        d["E3_pos"] = self.E3_pos
        d["E3_dir"] = self.E3_dir
        d["E3_pwr"] = self.E3_pwr
        d["E4_pos"] = self.E4_pos
        d["E4_dir"] = self.E4_dir
        d["E4_pwr"] = self.E4_pwr
        return d

    def get_draw_info(self):
        d = {}
        d["hull_pos"], d["hull_ax_angle"] = self.get_hull_pos_and_ax_angle()
        d["E1_pos"], d["E1_ax_angle"] = self.get_engine_pos_and_ax_angle(1)
        d["E2_pos"], d["E2_ax_angle"] = self.get_engine_pos_and_ax_angle(2)
        d["E3_pos"], d["E3_ax_angle"] = self.get_engine_pos_and_ax_angle(3)
        d["E4_pos"], d["E4_ax_angle"] = self.get_engine_pos_and_ax_angle(4)
        return d





if __name__ == '__main__':
    M = Machine()
    tt  = time.time()
    for i in range(10):
        M.physics_tick()



