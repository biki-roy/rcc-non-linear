from rcc_non_linear import Model
from rcc_non_linear.utils.helper import plot_response, plot_response_multi
col_props = {
    'fc': 6.1,
    'D': 48, 'L': 324, 'cover': 2,
    'nBars': 18, 'db': 1.41,
    'fy': 75.2, 'fu': 102.4, 'Es': 29000, 'e_ult': 0.122,
    'dh':0.883889, 'sh':6, 'fyh':54.8, 'esm':0.125, 
    'P_axial': 570
}

model = Model(col_props)

print(model.confined_props)
print(model.unconfined_props)
# print(model.fib_section)

#To plot the fiber section, use any of the following methods:
model.plot_fib_section()
# model.fib_section.plot()

#To run moment-curvature analysis:
results_df, bilinear_df, yield_step = model.run_M_phi_analysis()
print(f"Yield occurred at step: {yield_step}")
print(bilinear_df)
print(results_df.head())
# plot_response_multi(
#     dfs=[results_df.iloc[:, 0:2], bilinear_df],
#     names=["Original", "Bilinear"],
#     colors=["black", "red"],
#     x_label="Curvature",
#     y_label="Moment",
#     title="Curves Comparison"
# )
