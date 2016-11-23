import time, random, sys
import numpy as np
import multiprocessing
import Queue


def quehandle(que):
    tt = time.time()
    for i in range(10000):
        a = que.get()
        que.put(random.random())
    tt = time.time() - tt
    print tt


if __name__ == '__main__':
    print "multipr"
    que = multiprocessing.Queue(100)
    que.put(0)
    p = multiprocessing.Process(target=quehandle, args=(que,))
    p.start()
    p.join()
    print "linear"
    time.sleep(0.05)
    que = Queue.Queue(100)
    que.put(120)
    quehandle(que)






