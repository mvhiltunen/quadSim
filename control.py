import constants as C
import random, time ,math
import numpy as np


class Controller:
    def __init__(self):
        self.a = 0



    def control_tick(self, t):
        self.current_check = time.time()
        self.dt = self.current_check-self.previous_check
        DIR = np.dot(self.ROT_M, self.z)
        self.A_apx = self.A_apx*0.5 + (self.V-self.V_log[-1])*0.5
        self.V_log.append(self.V.copy())

        if False:
            if DIR[0] < 0:
                self.E4_pwr = self.rise(self.E4_pwr, DIR[0]*0.01)
                self.E3_pwr = self.lower(self.E3_pwr, DIR[0]*0.01)
            if DIR[0] > 0:
                self.E3_pwr = self.rise(self.E3_pwr, DIR[0]*0.01)
                self.E4_pwr = self.lower(self.E4_pwr, DIR[0]*0.01)

            if DIR[1] < 0:
                self.E2_pwr = self.rise(self.E2_pwr, DIR[1]*0.01)
                self.E1_pwr = self.lower(self.E1_pwr, DIR[1]*0.01)
            if DIR[1] > 0:
                self.E1_pwr = self.rise(self.E1_pwr, DIR[1]*0.01)
                self.E2_pwr = self.lower(self.E2_pwr, DIR[1]*0.01)

        Destination = 20.0
        Delta_T = 6.0
        Vmax = 8.0
        GapTime = 3.0
        CutDistance = Vmax*GapTime
        Delta_H = Destination - self.P[2]
        Pos_in_DT = self.extrapolate_position(Delta_T)
        if self.ticks%50 == 0:
            print "Current V", self.V
            print "Projecterd V", self.projected_speed_in(1.0)
            print "Current P", self.P
            print "Throttle:", self.E1_pwr

        pwr_coeff = 0
        tick = 0.5


        proj1 = self.projected_speed_in(6.0)
        check = 0
        if proj1[2] > Vmax:
            pwr_coeff -= tick
            check = 1
        if proj1[2] < -Vmax:
            pwr_coeff += tick
            check = 1

        if not check:
            if self.extrapolate_position(5.0)[2] > Destination:
                pwr_coeff -= tick

            if self.extrapolate_position(5.0)[2] < Destination:
                pwr_coeff += tick



        pwr_coeff = pwr_coeff*self.dt
        self.adjust_total_engine_power(pwr_coeff)
        self.previous_check = self.current_check



