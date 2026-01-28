from rcc_non_linear import Model
from rcc_non_linear.utils.helper import plot_response, plot_response_multi
col_props = {
    'fc': 6.1,
    'D': 48, 'L': 324, 'cover': 2,
    'nBars': 18, 'db': 1.41,
    'fy': 75.2, 'fu': 102.4, 'Es': 29000, 'Esh': 1247, 'e_sh': 0.005, 'e_ult': 0.122,
    'dh':0.888, 'sh':6, 'fyh':54.8, 'esm':0.125,
    'P_axial': 570, 'failure_criteria':["core"], 'core_crush_limit': 0.05
}

model = Model(col_props)
# model.plot_fib_section()
results_df, bilinear_df, yield_step = model.run_pushover_analysis()
print(bilinear_df)
print("Crushed core IDs:", model.crushed_cores)

