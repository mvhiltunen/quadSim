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


def addOne(name, V, lock):
    V.value += 1
    time.sleep(0.01)
    V.value += 1


def func(val):
    for i in range(50):
        val.value += 1


if __name__ == '__main__':
    import time
    v = Value('f', 0)
    print "A"
    procs = [Process(target=func, args=(v,)) for i in range(10)]
    print "B"
    for p in procs: p.start()
    print "C"
    for p in procs: p.join()
    print "D"
    print v.value





