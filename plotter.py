from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter
import matplotlib.pyplot as plt
import numpy as np

fig = plt.figure()
ax = fig.gca(projection='3d')
X = np.arange(-5, 5, 0.25)
Y = np.arange(-5, 5, 0.25)
X, Y = np.meshgrid(X, Y)
R = np.sqrt(X**2 + Y**2)
Z = np.sin(R) * 1.4 + np.random.rand(40,40)*0.0

m = int(Z.min()-2)
M = int(Z.max()+2)
step = (float(M)-float(m))/40
XX = np.arange(m,M,step)
YY = np.arange(m,M,step)
XX, YY = np.meshgrid(XX, YY)
print XX
print YY
surf = ax.plot_surface(XX, YY, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
                       linewidth=0, antialiased=True)
#ax.set_zlim(-1.02, 1.201)

ax.zaxis.set_major_locator(LinearLocator(10))
ax.zaxis.set_major_formatter(FormatStrFormatter('%.02f'))

fig.colorbar(surf, shrink=0.5, aspect=5)

plt.show()
