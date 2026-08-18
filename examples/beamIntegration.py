"""
Example demonstrating the modular beam integration functionality.
Tests different integration rules:
- HingeRadau (Default plastic hinge)
- HingeMidpoint
- Lobatto (Gauss-Lobatto distributed plasticity)
- Legendre (Gauss-Legendre distributed plasticity)
"""

from rcc_non_linear import (
    Model,
    HingeRadau,
    HingeMidpoint,
    Lobatto,
    Legendre,
    NewtonCotes,
    Trapezoidal,
    CompositeSimpson,
)

def run_integration_comparison():
    base_props = {
        'fc': 6.1,
        'D': 48, 'L': 324, 'cover': 2,
        'nBars': 18, 'db': 1.41,
        'fy': 75.2, 'fu': 102.4, 'Es': 29000, 'Esh': 1247, 'e_sh': 0.005, 'e_ult': 0.122,
        'dh':0.888, 'sh':6, 'fyh':54.8, 'esm':0.125,
        'P_axial': 570,  'failure_criteria': ['rebar'],
        'nAng': 30, 'nRad':20, 'nRad_cover': 8
    }

    integrations = {
        "HingeRadau (default)": HingeRadau(),
        "HingeRadau (custom lp=20)": HingeRadau(lp_bottom=20.0),
        "HingeMidpoint": HingeMidpoint(),
        "Lobatto (5 points)": Lobatto(num_points=5),
        "Legendre (5 points)": Legendre(num_points=5),
        "NewtonCotes (5 points)": NewtonCotes(num_points=5),
    }

    for name, integration_obj in integrations.items():
        props = base_props.copy()
        props['integration'] = integration_obj
        
        print(f"\n--- Testing Integration: {name} ---")
        model = Model(props)
        results_df, bilinear_df, yield_step = model.run_pushover_analysis(dU=1.0)
        peak_force = max(results_df['forces'])
        max_disp = max(results_df['displacements'])
        print(f"Max Displacement: {max_disp:.2f} in, Peak Lateral Force: {peak_force:.2f} kips, Yield Step: {yield_step}")

if __name__ == "__main__":
    run_integration_comparison()
