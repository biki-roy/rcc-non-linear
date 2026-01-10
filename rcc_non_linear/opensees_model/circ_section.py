import matplotlib.pyplot as plt
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
        plt.show()


