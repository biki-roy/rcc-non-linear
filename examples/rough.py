from rcc_non_linear import Model
from rcc_non_linear.utils.helper import plot_response, plot_response_multi
col_props = {
    'fc': 4.728,
    'D': 23.622, 'L': 104.33, 'cover': 1,
    'nBars': 14, 'db': 0.787,
    'fy': 90.213, 'fu': 112.694, 'e_sh': 0.005, 'e_ult': 0.1,
    'dh':0.39, 'sh':2.36, 'fyh':77.74, 'esm':0.074,
    'P_axial': 170.85
}

# col_props = {
#     'fc': 6.1,
#     'D': 48, 'L': 324, 'cover': 2,
#     'nBars': 18, 'db': 1.41,
#     'fy': 75.2, 'fu': 102.4, 'Es': 29000, 'Esh': 1247, 'e_sh': 0.005, 'e_ult': 0.122,
#     'dh':0.888, 'sh':6, 'fyh':54.8, 'esm':0.125,
#     'P_axial': 570
# }

model = Model(col_props)
results_df, bilinear_df, yield_step = model.run_pushover_analysis(dU=0.01)
print(results_df)
print(bilinear_df)
model.create_report()