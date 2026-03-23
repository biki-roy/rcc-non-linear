import pandas as pd
from pathlib import Path
from helper import get_excel_file_path
from rcc_non_linear.utils.aashto import get_idealized_displacements
from rcc_non_linear import Model
import re

workbook_name="rectangular_column.xlsx"
file_path = Path(get_excel_file_path(workbook_name=workbook_name))

output_dir = file_path.parent / "results_actual"
# Create folder if it does not exist
output_dir.mkdir(exist_ok=True)
# print(output_dir)

columns_df = pd.read_excel(file_path, sheet_name="data")

# Initialize list to collect results
results_push = []
results_mPhi = []
results_push_mPhi = []

for i, row in columns_df.iterrows():
    safe_column_name = re.sub(r'[/():<>"|?*\\]', '_', row['Column'])
    print(f"\n=== Running pushover for column {i+1}/{len(columns_df)} ({safe_column_name})===")

    if row["Counts"] not in [26]:
        row['analysis_actual'] = 0

    if row['analysis_actual'] == 0:
        results_push.append({'d0': None, 'V0': None, 'dy': None, 'Vy': None, 'du': None, 'Vp': None, 'failure_mode': None})
        results_mPhi.append({'phi0': None, 'M0': None, 'phi_y': None, 'M_y': None, 'phi_u': None, 'M_u': None, 'failure_mode': None})
        results_push_mPhi.append({'d0_': None, 'V0_': None, 'dy_': None, 'Vy_': None, 'du_': None, 'Vp_': None, 'failure_mode': None})
        print("⚠️ Skipping analysis as 'analysis_actual' is 0.")
        continue
    # Create model object
    col_props = col_props = {'fc':row['fc'], 'B':row['B'], 'H':row['H'], 'L':row['L'], 'cover':row['cover'], 'nBarsTop': int(row['nBarsTop']), 'dbTop': row['dbTop'], 'nBarsBot': int(row['nBarsBot']), 'dbBot': row['dbBot'], 'nBarsInt': int(row['nBarsInt']), 'dbInt': row['dbInt'], 'fy': row['fy'], 'fu': row['fu'], 'e_sh': 0.005, 'e_ult': row['e_ult'], 'dh':row['dh'], 'sh':row['sh'], 'fyh':row['fyh'],'fuh':row['fuh'], 'esm':row['esm'], 'nx': row['nx'], 'ny': row['ny'], 'P_axial': row['P_axial'], 'divB': int(row['divB']), 'divD': int(row['divD']), 'divCover': int(row['divCover'])}
    
    col = Model(col_props)
    # Run analyses
    results_mPhi_df, bilinear_mPhi_df, yield_step_mPhi = col.run_M_phi_analysis(dK = 0.0001)
    mode_mPhi = getattr(col, 'failure_mode_mPhi', None)
    results_mPhi.append({
        'phi0': 0, 'M0': 0,
        'phi_y': bilinear_mPhi_df['curvatures'][2], 'M_y': bilinear_mPhi_df['moments'][2], 'phi_u': bilinear_mPhi_df['curvatures'][3], 'M_u': bilinear_mPhi_df['moments'][3] ,'failure_mode': mode_mPhi if mode_mPhi is not None else 'None',
    })
    disp_i, disp_u = get_idealized_displacements(col.L, col.lp, bilinear_mPhi_df['curvatures'][2], bilinear_mPhi_df['curvatures'][3])
    results_push_mPhi.append({
        'd0_': 0, 'V0_': 0,
        'dy_': disp_i/row['L']*100, 'Vy_': bilinear_mPhi_df['moments'][2]/col.L,
        'du_': disp_u/row['L']*100, 'Vp_': bilinear_mPhi_df['moments'][3]/col.L,
        'failure_mode': mode_mPhi if mode_mPhi is not None else 'None'
    })
    results_push_df, bilinear_push_df, yield_step_push = col.run_pushover_analysis(dU=0.25)
    # Store results in summary table
    mode = getattr(col, 'failure_mode_pushover', None)
    results_push.append({
        'd0': 0, 'V0': 0,
        'dy': bilinear_push_df['displacements'][2] *100 /row['L'], 'Vy': bilinear_push_df['forces'][2], 'du': bilinear_push_df['displacements'][3] *100 /row['L'], 'Vp': bilinear_push_df['forces'][3] ,'failure_mode': mode if mode is not None else 'None',
    })

    col.create_report(f"{row['Counts']}_{row['Author']}_{safe_column_name}", output_dir)

# Convert all summaries into a dataframe
results_push_df = pd.DataFrame(results_push)
results_mPhi_df = pd.DataFrame(results_mPhi)
results_push_mPhi_df = pd.DataFrame(results_push_mPhi)

# Append summary_df to columns_df
merged_df = pd.concat([columns_df,  results_mPhi_df, results_push_mPhi_df, results_push_df], axis=1)

# Save to CSV
merged_df.to_csv(output_dir / f"{workbook_name.strip('.xlsx')}_results.csv", index=False)
print("✅ Results saved to results.csv")


