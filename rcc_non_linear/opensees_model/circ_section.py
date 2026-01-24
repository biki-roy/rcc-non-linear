import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import math

class CircSection:
    def __init__(self, D, cover, Ec, 
                 nBars, db,
                 dh, 
                 sec_tag, core_material, cover_material, bar_material, nAng, nRad, nRad_cover):
        import opsvis as opsv
        self.D, self.cover = D, cover
        self.nBars, self.db = nBars, db
        self.dh = dh
        self.sec_tag = sec_tag
        self.core_tag = core_material
        self.cover_tag = cover_material
        self.bar_tag = bar_material

        self.nAng, self.nRad, self.nRad_cover = nAng, nRad, nRad_cover

        self.R_core = D / 2 - cover - dh / 2
        self.R_bar = D / 2 - cover - dh - db / 2
        self.Ab = math.pi * (db / 2.0) ** 2

        G = Ec / (2 * (1 + 0.2))
        J = 2 * math.pi * (D/2 ** 4) / 4
        GJ = G * J

        self.fib_sec = [
            ['section', 'Fiber', self.sec_tag, '-GJ', GJ],
            ['patch', 'circ', self.core_tag, self.nAng, self.nRad, 0.0, 0.0, 0.0, self.R_core, 0.0, 360.0],
            ['patch', 'circ', self.cover_tag, self.nAng, self.nRad_cover, 0.0, 0.0, self.R_core, self.D/2, 0.0, 360.0],
            ['layer', 'circ', self.bar_tag, self.nBars, self.Ab, 0.0, 0.0, self.R_bar, 0.0, 360.0]
        ]
        opsv.fib_sec_list_to_cmds(self.fib_sec)


    def plot(self):
        """
        Plots the fiber section using ops_vis.
        """
        import opsvis as opsv
        opsv.plot_fiber_section(self.fib_sec, fillflag=1, matcolor=['gold', 'lightgrey', 'red'])
        plt.title("Circular Column Fiber Section")
        plt.axis('equal')
        # plt.show()

def symmetric_angles(nBars):
  ang = 2 * np.pi / nBars
  theta = [0]
  k = 1
  while len(theta) < nBars:
    theta.append(k * ang)
    if len(theta) < nBars:
        theta.append(-k * ang)
    k += 1
  return np.array(theta)

def circular_column_bar_fibers(r_bar, nBars):
    theta = symmetric_angles(nBars)

    y = r_bar * np.cos(theta)
    z = r_bar * np.sin(theta)

    return pd.DataFrame({
        'bar_id': np.arange(1, nBars + 1),
        'y': y,
        'z': z
    })
    # data = []
    # bar_id = 1

    # for yi, zi in zip(y, z):
    #     # keep only upper half bars (including neutral axis)
    #     if yi >= 0.0:
    #         data.append([bar_id, yi, zi])
    #         bar_id += 1

    # return pd.DataFrame(
    #     data,
    #     columns=["bar_id", "y", "z"]
    # )

def circular_column_core_fibers(r_core, nAng, nRad):
    dr = r_core / nRad
    dtheta = 2.0 * np.pi / nAng
    core_area = np.pi * r_core**2

    fiber_id = 1
    data = []

    for i in range(1, nRad + 1):  # radial rings (inside → outside)
        r_inner = (i - 1) * dr
        r_outer = i * dr
        
        # exact area of one fiber
        fiber_area = 0.5 * (r_outer**2 - r_inner**2) * dtheta
        
        # centroid radius (mid-radius version, as in your code)
        r_centroid = (i - 0.5) * dr
        
        for j in range(1, nAng + 1):  # angular sectors
            theta = (j - 0.5) * dtheta
            
            y = r_centroid * np.sin(theta)
            z = r_centroid * np.cos(theta)
            
            area_ratio = fiber_area / core_area
            data.append([fiber_id, y, z, area_ratio])
            fiber_id += 1

    return pd.DataFrame(
        data,
        columns=["fiber_id", "y", "z", "area_ratio"]
    )



