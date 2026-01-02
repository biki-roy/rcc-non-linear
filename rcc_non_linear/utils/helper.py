import numpy as np
from scipy.interpolate import griddata
def interpolate_z(df, x, y, method="linear", fallback="nearest"):
    '''Interpolate z for two independent variables x & y'''
    x_data = df.iloc[:, 0].values
    y_data = df.iloc[:, 1].values
    z_data = df.iloc[:, 2].values

    points = np.column_stack((x_data, y_data))

    xq = np.atleast_1d(x)
    yq = np.atleast_1d(y)
    query_points = np.column_stack((xq, yq))

    # Primary interpolation
    z_interp = griddata(points, z_data, query_points, method=method)

    # Fallback for points outside convex hull
    if fallback is not None:
        mask = np.isnan(z_interp)
        if np.any(mask):
            z_interp[mask] = griddata(
                points, z_data, query_points[mask], method=fallback
            )

    return z_interp[0].item() if z_interp.size == 1 else z_interp.item()
