import pandas as pd
from pathlib import Path
from helper import get_excel_file_path
from rcc_non_linear import Model

workbook_name="circular_column.xlsx"
file_path = Path(get_excel_file_path(workbook_name=workbook_name))

output_dir = file_path.parent / "results"
# Create folder if it does not exist
output_dir.mkdir(exist_ok=True)
# print(output_dir)

columns_df = pd.read_excel(file_path, sheet_name="data")

# Initialize list to collect results
summary_data = []

for i, row in columns_df.iterrows():
    print(f"\n=== Running pushover for column {i+1}/{len(columns_df)} ===")
    if row['analysis_actual'] == 0:
        summary_data.append({'d0': None, 'V0': None, 'dy': None, 'Vy': None, 'du': None, 'Vp': None, 'failure_mode': None})
        continue
    # Create model object
    col_props = {'fc':row['fc'], 'D':row['D'], 'L':row['L'],
                 'cover':row['cover'], 'nBars': int(row['nBars']), 'db': row['db'], 'fy': row['fy'], 'fu': row['fu'], 'e_sh': 0.005, 'e_ult': row['eps_ult'], 'dh':row['dh'], 'sh':row['sh'], 'fyh':row['fyh'], 'esm':row['esm'], 'P_axial': row['P_axial'], 'nAng': 30, 'nRad':20, 'nRad_cover': 8}
    col = Model(col_props)
    # Run analyses
    results_df, bilinear_df, yield_step = col.run_pushover_analysis(dU=0.01)
    # Store results in summary table
    mode = getattr(col, 'failure_mode_pushover', None)
    summary_data.append({
        'd0': 0, 'V0': 0,
        'dy': bilinear_df['displacements'][2] *100 /row['L'], 'Vy': bilinear_df['forces'][2], 'du': bilinear_df['displacements'][3] *100 /row['L'], 'Vp': bilinear_df['forces'][3] ,'failure_mode': mode if mode is not None else 'None',
    })

    col.create_report(f"{row['Counts']}_{row['Author']}_{row['Column']}", output_dir)
    
    if i>1: break

# Convert all summaries into a dataframe
summary_df = pd.DataFrame(summary_data)

# Append summary_df to columns_df
merged_df = pd.concat([columns_df, summary_df], axis=1)

# Save to CSV
merged_df.to_csv(output_dir / f"{workbook_name.strip('.xlsx')}_results.csv", index=False)
print("✅ Results saved to results.csv")


