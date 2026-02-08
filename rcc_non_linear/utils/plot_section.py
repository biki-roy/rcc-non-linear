import openseespy.opensees as ops
import numpy as np
import matplotlib.pyplot as plt
from matplotlib.patches import Circle, Polygon, Wedge
import matplotlib.patches as mpatches
from matplotlib.lines import Line2D 

# from .settings import *


# plot_fiber_section is inspired by plotSection matlab function
# written by D. Vamvatsikos available at
# http://users.ntua.gr/divamva/software.html (plotSection.zip)

def plot_fiber_section_damage(model, 
    fib_sec_list,
    fillflag=1,
    matcolor=['gold', 'lightgrey', 'red'],
    matcolor_dict=False,
    crushed_color='cyan',
    ruptured_color='red'
):
    """Plot fiber cross-section.

    Args:
        fib_sec_list (list): list of lists in the format similar to the parameters
            for the section, layer, patch, fiber OpenSees commands

        fillflag (int): 1 - filled fibers with color specified in matcolor
            list, 0 - no color, only the outline of fibers

        matcolor (list): sequence of colors for various material tags
            assigned to fibers

    Examples:
        ::

            fib_sec_1 = [['section', 'Fiber', 1, '-GJ', 1.0e6],
                         ['patch', 'quad', 1, 4, 1,  0.032, 0.317, -0.311, 0.067, -0.266, 0.005, 0.077, 0.254],  # noqa: E501
                         ['patch', 'quad', 1, 1, 4,  -0.075, 0.144, -0.114, 0.116, 0.075, -0.144, 0.114, -0.116],  # noqa: E501
                         ['patch', 'quad', 1, 4, 1,  0.266, -0.005,  -0.077, -0.254,  -0.032, -0.317,  0.311, -0.067]  # noqa: E501
                         ]
            opsv.fib_sec_list_to_cmds(fib_sec_1)
            matcolor = ['r', 'lightgrey', 'gold', 'w', 'w', 'w']
            opsv.plot_fiber_section(fib_sec_1, matcolor=matcolor)
            plt.axis('equal')
            # plt.savefig('fibsec_rc.png')
            plt.show()

    Notes:
        ``fib_sec_list`` can be reused by means of a python helper function
            ``opsvis.fib_sec_list_to_cmds(fib_sec_list_1)``

    See also:
        ``opsvis.fib_sec_list_to_cmds()``
    """

    crushed_cores = getattr(model, "crushed_cores", None) or set()
    ruptured_bars = getattr(model, "ruptured_bars", None) or set()


    crushed_coords = set()
    if crushed_cores is not None:
        for _, r in model.core_fibers.iterrows():
            if r["fiber_id"] in crushed_cores:
                crushed_coords.add((round(r["z"], 6), round(r["y"], 6)))

    ruptured_coords = set()
    bar_fibers = getattr(model, "bar_fibers", None)
    if bar_fibers is not None and ruptured_bars:
        for _, r in bar_fibers.iterrows():
            if r["bar_id"] in ruptured_bars:
                ruptured_coords.add((round(r["y"], 6), round(r["z"], 6)))


    fig, ax = plt.subplots()
    ax.set_xlabel('z')
    ax.invert_xaxis()  # To make z-axis positive to the left
    ax.set_ylabel('y')
    ax.grid(False)
    fiber_id = 0   # for concrete fibers
    bar_id = 0     # for rebars


    for item in fib_sec_list:

        if item[0] == 'layer':
            matTag = item[2]
            if item[1] == 'straight':
                n_bars = item[3]
                As = item[4]
                Iy, Iz, Jy, Jz = item[5], item[6], item[7], item[8]
                r = np.sqrt(As / np.pi)
                Y = np.linspace(Iy, Jy, n_bars)
                Z = np.linspace(Iz, Jz, n_bars)
                for zi, yi in zip(Z, Y):

                    key = (round(yi, 6), round(zi, 6))
                    fc = 'red' if key in ruptured_coords else 'k'

                    bar = Circle((zi, yi), r, ec='k', fc=fc, zorder=10)
                    ax.add_patch(bar)
                    bar_id += 1

            if item[1] == 'circ':
                n_bars, As = item[3], item[4]
                yC, zC, arc_radius = item[5], item[6], item[7]
                if len(item) > 8:
                    a0_deg, a1_deg = item[8], item[9]
                    if ((a1_deg - a0_deg) >= 360. and n_bars > 0):
                        a1_deg = a0_deg + 360. - 360. / n_bars
                else:
                    a0_deg, a1_deg = 0., 360. - 360. / n_bars

                a0_rad, a1_rad = np.pi * a0_deg / 180., np.pi * a1_deg / 180.
                r_bar = np.sqrt(As / np.pi)
                thetas = np.linspace(a0_rad, a1_rad, n_bars)
                Y = yC + arc_radius * np.cos(thetas)
                Z = zC + arc_radius * np.sin(thetas)
                for zi, yi in zip(Z, Y):
                    key = (round(yi, 6), round(zi, 6))
                    fc = ruptured_color if key in ruptured_coords else 'k'

                    bar = Circle((zi, yi), r_bar, ec='k', fc=fc, zorder=10)
                    ax.add_patch(bar)


        if (item[0] == 'patch' and (item[1] == 'quad' or item[1] == 'quadr' or
                                    item[1] == 'rect')):
            matTag, nIJ, nJK = item[2], item[3], item[4]
            if matcolor_dict:
                if matTag in matcolor_dict.keys():
                    face_color = matcolor_dict[matTag]
                else:
                    print(f'opsvis warning! matTag: {matTag} not found in matcolor_dict; white is used\n')
                    face_color = 'w'
            else:
                if len(matcolor) < matTag:
                    print(f'opsvis warning! matTag: {matTag} exceeds matcolor length; white is used\n')
                    face_color = 'w'
                else:
                    face_color = matcolor[matTag - 1]

            if item[1] == 'quad' or item[1] == 'quadr':
                Iy, Iz, Jy, Jz = item[5], item[6], item[7], item[8]
                Ky, Kz, Ly, Lz = item[9], item[10], item[11], item[12]

            if item[1] == 'rect':
                Iy, Iz, Ky, Kz = item[5], item[6], item[7], item[8]
                Jy, Jz, Ly, Lz = Ky, Iz, Iy, Kz

            # check for convexity (vector products)
            outIJxIK = (Jy-Iy)*(Kz-Iz) - (Ky-Iy)*(Jz-Iz)
            outIKxIL = (Ky-Iy)*(Lz-Iz) - (Ly-Iy)*(Kz-Iz)
            # check if I, J, L points are colinear
            outIJxIL = (Jy-Iy)*(Lz-Iz) - (Ly-Iy)*(Jz-Iz)
            # outJKxJL = (Ky-Jy)*(Lz-Jz) - (Ly-Jy)*(Kz-Jz)

            if outIJxIK <= 0 or outIKxIL <= 0 or outIJxIL <= 0:
                print('\nWarning! Patch quad is non-convex or counter-clockwise defined or has at least 3 colinear points in line')  # noqa: E501

            IJz, IJy = np.linspace(Iz, Jz, nIJ+1), np.linspace(Iy, Jy, nIJ+1)
            JKz, JKy = np.linspace(Jz, Kz, nJK+1), np.linspace(Jy, Ky, nJK+1)
            LKz, LKy = np.linspace(Lz, Kz, nIJ+1), np.linspace(Ly, Ky, nIJ+1)
            ILz, ILy = np.linspace(Iz, Lz, nJK+1), np.linspace(Iy, Ly, nJK+1)

            if fillflag:
                Z = np.zeros((nIJ+1, nJK+1))
                Y = np.zeros((nIJ+1, nJK+1))

                for j in range(nIJ+1):
                    Z[j, :] = np.linspace(IJz[j], LKz[j], nJK+1)
                    Y[j, :] = np.linspace(IJy[j], LKy[j], nJK+1)

                tol = 1e-6  # tolerance for matching core fibers
                for j in range(nIJ):
                    for k in range(nJK):
                        zy = np.array([
                            [Z[j, k], Y[j, k]],
                            [Z[j, k+1], Y[j, k+1]],
                            [Z[j+1, k+1], Y[j+1, k+1]],
                            [Z[j+1, k], Y[j+1, k]]
                        ])
                        z_mid = zy[:, 0].mean()
                        y_mid = zy[:, 1].mean()
                        # if centroid matches any crushed fiber
                        fc = face_color
                        for cz, cy in crushed_coords:
                            if abs(z_mid - cz) < tol and abs(y_mid - cy) < tol:
                                fc = crushed_color
                                break
                        poly = Polygon(zy, closed=True, ec='k', fc=fc)
                        ax.add_patch(poly)

            else:
                # horizontal lines
                for az, bz, ay, by in zip(IJz, LKz, IJy, LKy):
                    plt.plot([az, bz], [ay, by], 'b-', zorder=1)

                # vertical lines
                for az, bz, ay, by in zip(JKz, ILz, JKy, ILy):
                    plt.plot([az, bz], [ay, by], 'b-', zorder=1)

        if item[0] == 'patch' and item[1] == 'circ':
            matTag, nc, nr = item[2], item[3], item[4]
            if matcolor_dict:
                if matTag in matcolor_dict.keys():
                    face_color = matcolor_dict[matTag]
                else:
                    print(f'opsvis warning! matTag: {matTag} not found in matcolor_dict; white is used\n')
                    face_color = 'w'
            else:
                if len(matcolor) < matTag:
                    print(f'opsvis warning! matTag: {matTag} exceeds matcolor length; white is used\n')
                    face_color = 'w'
                else:
                    face_color = matcolor[matTag - 1]

            yC, zC, ri, re = item[5], item[6], item[7], item[8]
            a0, a1 = item[9], item[10]

            dr = (re - ri) / nr
            dth = (a1 - a0) / nc

            for j in range(nr):
                rj = ri + j * dr
                rj1 = rj + dr

                for i in range(nc):
                    thi =  a0 + i * dth
                    thi1 = thi + dth
                    if crushed_cores and fiber_id in crushed_cores:
                        fc = crushed_color
                    else:
                        fc = face_color
                    theta_mid = np.deg2rad(thi + 0.5 * dth)
                    # approximate fiber centroid
                    z_mid = zC + (rj + 0.5 * dr) * np.cos(theta_mid)
                    y_mid = yC + (rj + 0.5 * dr) * np.sin(theta_mid)

                    key = (round(z_mid, 6), round(y_mid, 6))
                    fc = crushed_color if key in crushed_coords else face_color

                    wedge = Wedge((zC, yC), rj1, thi, thi1, width=dr, ec='k',
                                lw=1, fc=fc)
                    ax.add_patch(wedge)

                    fiber_id += 1

    # --- Legend handles ---
    legend_handles = []

    # Core fibers
    core_patch = mpatches.Patch(facecolor=matcolor[0], edgecolor='k', label='Core Fiber')
    legend_handles.append(core_patch)

    # Cover fibers (assuming second color in matcolor list)
    cover_patch = mpatches.Patch(facecolor=matcolor[1], edgecolor='k', label='Cover Fiber')
    legend_handles.append(cover_patch)

    # Bar fibers (circular marker)
    bar_marker = Line2D([0], [0], marker='o', color='k', label='Bar Fiber',
                        markerfacecolor='k', markersize=10, linestyle='None')
    legend_handles.append(bar_marker)

    # Crushed core fibers
    if crushed_coords:
        crushed_patch = mpatches.Patch(facecolor=crushed_color, edgecolor='k', label='Crushed Core')
        legend_handles.append(crushed_patch)

    # Fractured rebars
    if ruptured_coords:
        ruptured_marker = Line2D([0], [0], marker='o', color='k', label='Fractured Rebar',
                             markerfacecolor=ruptured_color, markersize=10, linestyle='None')
        legend_handles.append(ruptured_marker)

    # Add legend to axes
    ax.legend(handles=legend_handles,
            loc='upper left',             # legend location
            bbox_to_anchor=(1.05, 1),    # move outside plot
            borderaxespad=0.,
            frameon=True)
    plt.tight_layout()
    ax.axis('equal')
    return fig, ax
