from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import numpy as np
import noise

class SurfPlot:
    def __init__(self, data_grid, scale=None):
        #super(SurfPlot, self).__init__()
        self.data = data_grid
        self.shape = data_grid.shape
        self.scale = scale
        self.datamin = min(self.data.flatten())
        self.datamax = max(self.data.flatten())
        if not self.scale:
            m = self.datamin - 0.08*abs(self.datamin)
            M = self.datamax + 0.08*abs(self.datamax)
            self.scale = (m, M ,(M-m)/20.0)
        self.X = np.arange(0, self.shape[0])
        self.Y = np.arange(0, self.shape[1])
        self.XX, self.YY = np.meshgrid(self.X, self.Y)


    def do(self):
        fig = plt.figure()
        ax = fig.gca(projection="3d")
        surf = ax.plot_surface(self.XX, self.YY,self.data, rstride=1, cstride=1,
                               cmap=cm.coolwarm, linewidth=0, antialiased=False)
        ax.set_zlim(self.scale[0], self.scale[1])

        ax.zaxis.set_major_locator(LinearLocator(10))
        ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

        fig.colorbar(surf, shrink=0.5, aspect=5)
        plt.show()


if __name__ == '__main__':
    D = np.zeros((150,150), np.float32)
    for i in range(150):
        for j in range(150):
            x = i/20.0
            y = j/25.0
            D[i][j] = noise.pnoise2(x,y, octaves=4)

    S = SurfPlot(D, (-1,2,1))
    S.do()
