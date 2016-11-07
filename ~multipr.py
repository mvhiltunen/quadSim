import time, random, sys
from multiprocessing import Process, Manager, Value, Array, Queue, Pipe
import numpy as np
import multiprocessing


class pProcess(Process):
    def __init__(self, transmitter, mode):
        super(pProcess, self).__init__()
        self.duct = transmitter
        self.mode = mode
        self.d = {"hull_p":np.array(range(3)), "hull_ax_angle":np.array(range(4))}
        for i in range(4):
            name = "E{}_ax_angle".format(i+1)
            d[name] = np.array(range(8))


    def run(self):
        T0 = time.time()
        if self.mode == "que":
            for i in range(1000):
                self.duct.put(self.d, False)
        elif self.mode == "value":
            for i in range(1000*(7+8*4)):
                self.duct.value = 123.4453232
        elif self.mode == "dict":
            for i in range(1000):
                self.duct["draw_info"] = self.d
        T1 = time.time()-T0
        print "time in Process with {0}:".format(self.mode), T1/1000.0
        sys.exit(1)

if __name__ == "__main__":
    manager = Manager()
    v = Value('d', 0)
    a = Array('d', [0]*10)
    d = manager.dict()
    Q = Queue(100000)

    Pq = pProcess(Q, "que")
    Pv = pProcess(v, "value")
    Pd = pProcess(d, "dict")

    Pq.start()
    time.sleep(0.6)
    Pv.start()
    time.sleep(0.6)
    Pd.start()
    time.sleep(0.6)


    print "actives: ", multiprocessing.active_children()
    for pr in multiprocessing.active_children():
        pr.terminate()
        pass
    time.sleep(0.1)
    #Pq.terminate()
    #Pv.terminate()
    #Pd.terminate()
    print "actives: ", multiprocessing.active_children()
    sys.exit()





