import time, random, sys
from multiprocessing import Process, Manager, Value, Array, Queue, Pipe
import numpy as np
import multiprocessing

def proxy(instance):
    instance.run2()


class pProcess(Process):
    def __init__(self, state, mode):
        super(pProcess, self).__init__()
        self.state = state
        self.mode = mode
        self.pwr_names = ["E1_pwr","E2_pwr","E3_pwr","E4_pwr"]
        self.dir_names = ["E1_dir","E2_dir","E3_dir","E4_dir"]
        self.D = {}
        self.L = []
        for name in self.dir_names:
            self.D[name] = np.array([random.random(),random.random(),random.random()])
            self.L.append(np.array([random.random(),random.random(),random.random()]))

    def run1(self):
        T0 = time.time()
        for i in xrange(10000):
            for name in self.pwr_names:
                self.state[name].value = random.random()
            for name in self.dir_names:
                self.state[name][0] = random.random()
                self.state[name][1] = random.random()
                self.state[name][2] = random.random()
        T = time.time()-T0
        print T/10000.0
        sys.exit(1)

    def run2(self):
        T0 = time.time()
        for i in xrange(10000):
            self.state["info"] = self.D
        T = time.time()-T0
        print T/10000.0
        sys.exit(1)

    def run3(self):
        T0 = time.time()
        for i in xrange(100000):
            self.D["info"] = self.D
        T = time.time()-T0
        print T/100000.0
        sys.exit(1)

    def run4(self):
        T0 = time.time()
        for i in xrange(100000):
            self.state.put(self.L)
        T = time.time()-T0
        print T/100000.0
        sys.exit(1)


    def run(self):
        if self.mode == 1:
            self.run1()
        elif self.mode == 2:
            self.run2()
        elif self.mode == 3:
            self.run3()
        elif self.mode == 4:
            self.run4()

def compose_control_state():
    D = {}
    D["E1_pwr"] = multiprocessing.Value('d')
    D["E2_pwr"] = multiprocessing.Value('d')
    D["E3_pwr"] = multiprocessing.Value('d')
    D["E4_pwr"] = multiprocessing.Value('d')
    D["E1_dir"] = multiprocessing.Array('d', 3)
    D["E2_dir"] = multiprocessing.Array('d', 3)
    D["E3_dir"] = multiprocessing.Array('d', 3)
    D["E4_dir"] = multiprocessing.Array('d', 3)
    return D


def addOne(name, V, lock):
    V.value += 1
    time.sleep(0.01)
    V.value += 1


def func(val):
    for i in range(50):
        val.value += 1


state0 = compose_control_state()
que = Queue(1000)


def putQue():
    que.put(state0)

if __name__ == '__main__':
    import timeit

    state = compose_control_state()
    m = Manager()
    dstate = m.dict()
    dstate["info"] = {}
    qstate = Queue(10000)
    time.sleep(0.1)
    p1 = pProcess(state, 1)
    p2 = pProcess(dstate, 2)
    p3 = pProcess(dstate, 3)
    p4 = pProcess(qstate, 4)
    #p = Process(target=proxy, args=(pProcess(dstate),))
    print "1"
    p1.start()
    p1.join()
    print "2"
    p2.start()
    p2.join()
    print "3"
    p3.start()
    p3.join()






