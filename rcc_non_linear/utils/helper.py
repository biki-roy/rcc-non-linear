import numpy as np
import pandas as pd
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


def caltrans_bilinear(df, yield_index):
    """
    Generate Caltrans-style bilinear idealization.
    - First branch: elastic slope up to yield, extended linearly until idealized yield
    - Second branch: horizontal (constant strength)
    - Area equality enforced beyond yield point.
    """
    cols = df.columns
    x = df.iloc[:, 0].to_numpy()
    y = df.iloc[:, 1].to_numpy()

    # Extract key points
    Dy, Vy = x[yield_index], y[yield_index]
    Du, Vu = x[-1], np.max(y)
    Ke = Vy / Dy  # elastic slope

    # Actual area beyond yield
    area_actual = np.trapz(y[yield_index:], x[yield_index:])

    # Function to compute area under bilinear idealized curve (beyond yield)
    def bilinear_area(Dp):
        # beyond yield: from Dy → Dp (still increasing linearly), then horizontal at Vp
        Vp = Vy + Ke * (Dp - Dy)
        area1 = 0.5 * (Vp + Vy) * (Dp - Dy)  # trapezoid under rising branch
        area2 = Vp * (Du - Dp)               # rectangular plateau
        return area1 + area2, Vp

    # Find Dp (plastic hinge start) such that areas match
    Dp_low, Dp_high = Dy, Du
    for _ in range(1000):
        Dp_mid = 0.5 * (Dp_low + Dp_high)
        area_mid, _ = bilinear_area(Dp_mid)
        if abs(area_mid - area_actual) < 1e-3:
            break
        if area_mid > area_actual:
            Dp_high = Dp_mid
        else:
            Dp_low = Dp_mid

    Dp = Dp_mid
    _, Vp = bilinear_area(Dp)

    # Construct bilinear coordinates
    x_bi = [0, Dy, Dp, Du]
    y_bi = [0, Vy, Vp, Vp]
    bilinear_df = pd.DataFrame({cols[0]: x_bi, cols[1]: y_bi})

    return bilinear_df

def plot_response(df, x_label=None, y_label=None, title="Response Curve"):
    import plotly.graph_objects as go

    x = df.iloc[:, 0]
    y = df.iloc[:, 1]

    x_label = x_label or df.columns[0]
    y_label = y_label or df.columns[1]

    fig = go.Figure(
        go.Scatter(
            x=x,
            y=y,
            mode="lines",
            line=dict(width=3),
            hovertemplate=f"{x_label}: %{{x:.4f}}<br>{y_label}: %{{y:.4f}}<extra></extra>",
        )
    )

    fig.update_layout(
        title=title,
        xaxis_title=x_label,
        yaxis_title=y_label,
        template="plotly_white",
        # hovermode="x unified",
    )

    fig.show()


def plot_response_multi(
    dfs,
    names=None,
    colors=None,
    x_label=None,
    y_label=None,
    title="Response Curve",
):
    import plotly.graph_objects as go

    fig = go.Figure()

    for i, df in enumerate(dfs):
        x = df.iloc[:, 0]
        y = df.iloc[:, 1]

        xl = x_label or df.columns[0]
        yl = y_label or df.columns[1]

        fig.add_trace(
            go.Scatter(
                x=x,
                y=y,
                mode="lines",
                name=names[i] if names else f"Trace {i+1}",
                line=dict(width=3, color=colors[i] if colors else None),
                hovertemplate=f"{xl}: %{{x:.4f}}<br>{yl}: %{{y:.4f}}<extra></extra>",
            )
        )

    fig.update_layout(
        title=title,
        xaxis_title=x_label or dfs[0].columns[0],
        yaxis_title=y_label or dfs[0].columns[1],
        template="plotly_white",
        # hovermode="x unified",
    )

    fig.show()

