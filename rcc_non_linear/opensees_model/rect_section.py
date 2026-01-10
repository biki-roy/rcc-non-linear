import numpy as np
import matplotlib.pyplot as plt
import math

class RectSection:    
    def __init__(self, B, H, cover, Ec, 
                 nBarsTop , dbTop, 
                 nBarsBot, dbBot,
                 nBarsInt, dbInt,
                 dh, 
                 sec_tag, core_material, cover_material, bar_material,
                 divB, divD, divCover):
        import opsvis as opsv
        self.B = B
        self.H = H
        self.cover = cover
        self.Ec = Ec
        self.nBarsTop = nBarsTop
        self.nBarsBot = nBarsBot
        self.nBarsInt = nBarsInt
        self.dbTop = dbTop
        self.dbBot = dbBot
        self.dbInt = dbInt
        self.sec_tag = sec_tag
        self.core_tag = core_material
        self.cover_tag = cover_material
        self.bar_tag = bar_material
        self.divB, self.divD, self.divCover = divB, divD, divCover

        self.AbarTop = math.pi * (dbTop / 2)**2
        self.AbarBot = math.pi * (dbBot / 2)**2
        self.AbarInt = math.pi * (dbInt / 2)**2
        
        #core dimensions
        self.core_h, self.core_b = H/2 - cover - dh/2, B/2 - cover - dh/2
        self.bar_h, self.bar_b = H/2 - cover - dh - dbTop/2, B/2 - cover - dh - dbTop/2

        G = self.Ec / (2 * (1 + 0.2))
        J = (self.B * self.H**3 + self.H * self.B**3) / 12.0
        GJ = G * J


        self.fib_sec = [['section', 'Fiber', sec_tag, '-GJ', GJ]]

        # Concrete Patches (Core and Cover)
        #patch('rect', matTag, numSubdivY, numSubdivZ, *crdsI, *crdsJ)
        self.fib_sec.append(['patch', 'rect', self.core_tag, self.divD, self.divB, -self.core_h, -self.core_b, self.core_h, self.core_b])       #core
        self.fib_sec.append(['patch', 'rect', self.cover_tag, self.divD, self.divCover, -self.core_h, -self.B/2, self.core_h, -self.core_b])       #right cover
        self.fib_sec.append(['patch', 'rect', self.cover_tag, self.divD, self.divCover, -self.core_h, self.core_b, self.core_h, self.B/2])     #left cover
        self.fib_sec.append(['patch', 'rect', self.cover_tag, self.divCover, self.divB, -self.H/2, -self.B/2, -self.core_h, self.B/2])    #bottom cover
        self.fib_sec.append(['patch', 'rect', self.cover_tag, self.divCover, self.divB, self.core_h, -self.B/2, self.H/2, self.B/2])   #top cover

        # Reinforcement Layers with specific areas
        # layer('straight', matTag, numFiber, areaFiber, *start, *end)
        # Top Layer
        self.fib_sec.append(['layer', 'straight', self.bar_tag, self.nBarsTop, self.AbarTop, self.bar_h, -self.bar_b, self.bar_h, self.bar_b])

        # Bottom Layer
        self.fib_sec.append(['layer', 'straight', self.bar_tag, self.nBarsBot, self.AbarBot, -self.bar_h, -self.bar_b, -self.bar_h, self.bar_b])

        # Intermediate Layers (Side bars)
        if self.nBarsInt > 0:
            # Assuming nBarsInt is the total number of bars between top and bottom layers
            # Distributed in pairs on the left and right faces
            num_rows = int(self.nBarsInt / 2)
            # Generate y-coordinates between top and bottom steel
            y_positions = np.linspace(self.bar_h, -self.bar_h, num_rows + 2)[1:-1]
            for y in y_positions:
                # Place 2 bars at this depth (one at -c_b and one at c_b)
                self.fib_sec.append(['layer', 'straight', self.bar_tag, 2, self.AbarInt, y, -self.bar_b, y, self.bar_b])

        # Execute Section Commands
        opsv.fib_sec_list_to_cmds(self.fib_sec)

    def plot(self):
        """
        Plots the fiber section using ops_vis.
        """
        # plt.figure(figsize=(6, 8))
        # matcolor: [Material 1 (Core), Material 2 (Cover), Material 3 (Steel)]
        import opsvis as opsv
        opsv.plot_fiber_section(self.fib_sec, fillflag=1, matcolor=['gold', 'lightgrey', 'red'])
        plt.title("Rectangular Column Fiber Section")
        plt.axis('equal')
        # plt.show()
