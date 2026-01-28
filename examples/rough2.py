from rcc_non_linear import Model
from rcc_non_linear.utils.helper import plot_response, plot_response_multi
col_props = {
    'fc': 5.5,
    'B': 20, 'H': 30, 'L': 150,
    'cover': 1.5,
    'nBarsTop': 5, 'dbTop': 1,
    'nBarsBot': 5, 'dbBot': 1,
    # 'nBarsInt': 6, 'dbInt': 0.984,
    'fy': 68, 'fu': 95, 'Es': 29000, 'e_sh': 0.0115, 'e_ult': 0.12,
    'dh':0.375, 'sh':3, 'fyh':68, 'esm':0.12,
    'nx': 2, 'ny':2,
    'P_axial': 0,
}

model = Model(col_props)

results_df, bilinear_df, yield_step = model.run_pushover_analysis()
print(bilinear_df)