import random
import numpy as np
import constants as C


def test1():
    '''
    rotated_vector = np.dot(ROT_MATRIX, vector)
    retains vecor length always
    '''
    print "start"
    for j in range(100):
        axis = np.array([random.random() - 0.5, random.random()- 0.5, random.random() - 0.5])
        deg = random.random()*12.19
        RM = C.rotation_matrix(axis, deg)
        for i in range(100):
            vec = np.array([random.random() - 0.5, random.random()- 0.5, random.random() - 0.5]) * (random.random()+2.4)
            r_vec = np.dot(RM, vec)
            delta_len = abs(C.get_len(vec) - C.get_len(r_vec))
            if delta_len > 0.00000001:
                print "error"
                print delta_len
                break

    print "success"

test1()