"""
Example demonstrating reversed cyclic pushover analysis on a rectangular column.
Demonstrates multi-cycle repetitions at each drift level.
"""

from rcc_non_linear import Model, HingeRadau

def main():
    # 1. Define Rectangular Column Properties
    col_props = {
        'fc': 5.5,
        'B': 20,
        'H': 30,
        'L': 150,
        'cover': 1.5,
        'nBarsTop': 3,
        'dbTop': 1.0,
        'nBarsBot': 5,
        'dbBot': 1.27,
        'fy': 68,
        'fu': 95,
        'Es': 29000,
        'e_sh': 0.0115,
        'e_ult': 0.12,
        'dh': 0.375,
        'sh': 3,
        'fyh': 68,
        'esm': 0.12,
        'nx': 2,
        'ny': 2,
        'P_axial': 100,
        'failure_criteria': ['core', 'strength'],
        'core_crush_limit': 0.01,
        'divB': 15,
        'divD': 25,
        'integration': HingeRadau(),
    }

    print("Initializing Rectangular RCC Column Model...")
    model = Model(col_props)

    # 2. Define Drift Protocol with 2 cycles per drift level
    drift_peaks = [0.25, -0.25, 0.5, -0.5, 1.0, -1.0, 2.0, -2.0]

    print("\nRunning Reversed Cyclic Pushover Analysis (2 cycles per peak)...")
    cyclic_df = model.run_cyclic_analysis(
        drift_peaks=drift_peaks,
        num_cycles_per_peak=2,
        dU=0.05,
        self_wt=True,
        verbose=True
    )

    print("\n--- Results Summary ---")
    print(f"Total Steps: {len(cyclic_df)}")
    print(f"Max Positive Force: {cyclic_df['forces'].max():.2f} kips at disp = {cyclic_df.loc[cyclic_df['forces'].idxmax(), 'displacements']:.2f} in")
    print(f"Max Negative Force: {cyclic_df['forces'].min():.2f} kips at disp = {cyclic_df.loc[cyclic_df['forces'].idxmin(), 'displacements']:.2f} in")

if __name__ == '__main__':
    main()
