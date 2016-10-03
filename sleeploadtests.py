import time

def func(t):
    while True:
        time.sleep(t)
        L = list(range(200))
        S = sum(L)



if __name__ == '__main__':
    func(0.001)  #0.001 not visible effect. 0.0001 significant load at shitty laptop cpu
