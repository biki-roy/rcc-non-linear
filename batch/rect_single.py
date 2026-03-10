from rcc_non_linear import Model
from pathlib import Path

col_props = {    
    'B': 23.62, 'H': 19.69, 'L': 104.33,
    'cover': 1.77,
    'nBarsTop': 5, 'dbTop': 0.787402,
    'nBarsBot': 5, 'dbBot': 0.787402,
    'nBarsInt': 6, 'dbInt': 0.787402,
    'fy': 90.89, 'fu': 112.162, 
    'Es': 29000, 'e_sh': 0.0216, 'e_ult': 0.13, 
    'dh':0.394, 'sh':2.36, 'fyh':77.74, 'esm':0.13,
    'nx': 3, 'ny':3,
   'fc': 4.728, 'P_axial': 182.1
}

model = Model(col_props)

results_df, bilinear_df, yield_step = model.run_M_phi_analysis()
print(bilinear_df)
out_dir = Path(__file__).parent / "results"
model.create_report(out_dir=out_dir)

