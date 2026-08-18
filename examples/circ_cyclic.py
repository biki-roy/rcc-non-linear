"""
Example demonstrating reversed cyclic pushover analysis on a circular bridge column.
Generates full hysteretic loops for a user-prescribed drift protocol.
"""

from rcc_non_linear import Model, HingeRadau

def main():
    # 1. Define Column Properties
    col_props = {
        'fc': 6.1,
            'D': 48, 'L': 324, 'cover': 2,
            'nBars': 18, 'db': 1.41,
            'fy': 75.2, 'fu': 102.4, 'Es': 29000, 'Esh': 1247, 'e_sh': 0.005, 'e_ult': 0.122,
            'dh':0.888, 'sh':6, 'fyh':54.8, 'esm':0.125,
            'P_axial': 570,
    }

    print("Initializing RCC Column Model...")
    model = Model(col_props)

    # 2. Define Drift Protocol (in % or as ratios)
    # e.g., 0.25%, -0.25%, 0.5%, -0.5%, 1%, -1%, 2%, -2%, 3%, -3%
    drift_peaks = [0.25, -0.25, 0.5, -0.5, 1.0, -1.0, 2.0, -2.0, 3.0, -3.0]

    print(f"\nRunning Reversed Cyclic Pushover Analysis...")
    print(f"Drift Peaks (%): {drift_peaks}")

    # 3. Run Cyclic Analysis
    cyclic_df = model.run_cyclic_analysis(
        drift_peaks=drift_peaks,
        num_cycles_per_peak=1,
        dU=0.1,             # Displacement step size (in)
        self_wt=True,
        verbose=True
    )

    print("\n--- Cyclic Analysis Results Summary ---")
    print(f"Total Steps Recorded: {len(cyclic_df)}")
    print(f"Max Positive Disp: {cyclic_df['displacements'].max():.2f} in (Peak Force: {cyclic_df['forces'].max():.2f} kips)")
    print(f"Max Negative Disp: {cyclic_df['displacements'].min():.2f} in (Peak Force: {cyclic_df['forces'].min():.2f} kips)")

    # 4. Extract Backbone Curves
    backbone_both = model.get_cyclic_backbone(envelope='both')
    backbone_pos = model.get_cyclic_backbone(envelope='positive')
    print(f"\nExtracted Backbone Points: {len(backbone_both)} key peak points.")

    # 5. Save or Plot Hysteresis Loop with Backbone Curve
    try:
        import matplotlib.pyplot as plt
        plt.figure(figsize=(9, 6))
        plt.plot(cyclic_df['displacements'], cyclic_df['forces'], color='#93C5FD', lw=1.2, alpha=0.85, label='Hysteretic Loops')
        plt.plot(backbone_both['displacements'], backbone_both['forces'], color='#DC2626', lw=2.2, linestyle='--', marker='o', markersize=4, label='Backbone Envelope')
        
        plt.axhline(0, color='gray', linestyle=':', linewidth=0.8)
        plt.axvline(0, color='gray', linestyle=':', linewidth=0.8)
        plt.title('Circular RC Column Cyclic Response & Backbone Envelope', fontsize=13, fontweight='bold', pad=12)
        plt.xlabel('Top Lateral Displacement (in)', fontsize=11)
        plt.ylabel('Base Shear Force (kips)', fontsize=11)
        plt.grid(True, linestyle=':', alpha=0.6)
        plt.legend(frameon=True, facecolor='white', framealpha=0.9)
        plt.tight_layout()
        plt.savefig('cyclic_hysteresis_backbone.png', dpi=300)
        print("Plot with Backbone saved to 'cyclic_hysteresis_backbone.png'")
    except Exception as e:
        print(f"Plotting skipped: {e}")

if __name__ == '__main__':
    main()
