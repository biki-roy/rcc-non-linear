import os
import datetime
import pandas as pd
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import matplotlib.pyplot as plt
from reportlab.platypus import Image

# ---------------------- Helper: DataFrame to Table Data ----------------------
def df_to_table_data(df, show_index=True):
    """
    Convert pandas DataFrame to list of lists suitable for ReportLab Table
    """
    if df.empty:
        return [["Empty DataFrame"]]
    
    df_copy = df.copy()
    if show_index:
        df_copy.insert(0, "Index", df_copy.index)
    
    headers = list(df_copy.columns)
    data = [headers]
    
    for _, row in df_copy.iterrows():
        row_data = []
        for i, val in enumerate(row.values):
            # If first column is index, convert to integer
            if show_index and i == 0:
                row_data.append(f"{int(val)}")
            elif isinstance(val, float):
                row_data.append(f"{val:.6f}")
            else:
                row_data.append(str(val))
        data.append(row_data)
    return data

# ---------------------- Markdown Report Generator ----------------------
def create_markdown_report(model, filename="RC_Column_Report.md", out_dir=None):
    """
    Generate Markdown report including geometry, materials, derived properties,
    reinforcement, M-phi and pushover tables.
    """
    if out_dir is None:
        out_dir = os.path.join(os.getcwd(), "results")
    os.makedirs(out_dir, exist_ok=True)
    filepath = os.path.join(out_dir, filename)
    
    lines = []
    lines.append(f"# RC Column Nonlinear Analysis Report")
    lines.append(f"**Generated on:** {datetime.datetime.now():%Y-%m-%d %H:%M:%S}\n")

    # Geometry
    lines.append("## 1. Column Geometry")
    lines.append(f"- Section type: {model.section_type}")
    lines.append(f"- Column length, L = {model.L:.2f}")
    lines.append(f"- Concrete cover = {model.cover:.2f}")
    if model.section_type == "circular":
        lines.append(f"- Diameter, D = {model.D:.2f}")
    else:
        lines.append(f"- Width, B = {model.B:.2f}")
        lines.append(f"- Depth, H = {model.H:.2f}")
    lines.append("")

    # Derived Section Properties
    lines.append("## 2. Derived Section Properties")
    lines.append(f"- Gross area, Ag = {model.Ag:.2f}")
    lines.append(f"- Steel area, As = {model.As:.2f}")
    lines.append(f"- Moment of inertia, Iz = {model.Iz:.2f}")
    lines.append(f"- Plastic hinge length, lp = {model.lp:.2f}")
    if hasattr(model, "k_eff"):
        lines.append(f"- Effective stiffness modifier, k_eff = {model.k_eff:.4f}")
    lines.append("")

    # Material Properties
    lines.append("## 3. Material Properties")
    lines.append(f"- Concrete f'c = {model.fc:.2f}")
    lines.append(f"- Concrete Ec = {model.Ec:.2f}")
    lines.append(f"- Steel fy = {model.fy:.2f}, fu = {model.fu:.2f}, Es = {model.Es:.2f}")
    lines.append(f"- Strain hardening modulus Esh = {model.Esh:.2f}\n")

    # Reinforcement
    lines.append("## 4. Reinforcement Details")
    if model.section_type == "circular":
        lines.append(f"- Number of bars = {model.nBars}, diameter = {model.db}")
    else:
        lines.append(f"- Top bars = {model.nBarsTop} (dia {model.dbTop})")
        lines.append(f"- Bottom bars = {model.nBarsBot} (dia {model.dbBot})")
        if model.nBarsInt > 0:
            lines.append(f"- Interior bars = {model.nBarsInt} (dia {model.dbInt})")
    lines.append("")

    # M-Phi Analysis
    if hasattr(model, "df_m_phi"):
        lines.append("## 5. Moment-Curvature Analysis")
        lines.append(f"- Number of steps: {len(model.df_m_phi)}")
        lines.append("\n### 5.1 First 10 and Last 10 Steps")
        lines.append(df_to_markdown_str(model.df_m_phi))
        if hasattr(model, "df_m_phi_idealized"):
            lines.append("\n### 5.2 Idealized Points")
            df_ideal = model.df_m_phi_idealized.copy()
            df_ideal.insert(0, "Points", ["Origin", "Yield", "Idealized Yield", "Ultimate"])
            lines.append(df_to_markdown_str(df_ideal, show_index=False))

    # Pushover Analysis
    if hasattr(model, "df_pushover"):
        lines.append("## 6. Pushover Analysis")
        lines.append(f"- Number of steps: {len(model.df_pushover)}")
        lines.append("\n### 6.1 First 10 and Last 10 Steps")
        lines.append(df_to_markdown_str(model.df_pushover))
        if hasattr(model, "df_pushover_idealized"):
            lines.append("\n### 6.2 Idealized Points")
            df_ideal = model.df_pushover_idealized.copy()
            df_ideal.insert(0, "Points", ["Origin", "Yield", "Idealized Yield", "Ultimate"])
            lines.append(df_to_markdown_str(df_ideal, show_index=False))

    # Write Markdown
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))

    return filepath

# ---------------------- Helper: Convert DF to Markdown string ----------------------
def df_to_markdown_str(df, max_rows=10, float_fmt=".6f", show_index=True):
    """
    Convert DataFrame to Markdown table string
    """
    if df.empty:
        return "_Empty DataFrame_"
    
    n = len(df)
    df_copy = df.copy()
    if show_index:
        df_copy.insert(0, "Index", df_copy.index)
    
    headers = list(df_copy.columns)
    lines = ["| " + " | ".join(headers) + " |", "|" + "|".join(["---"]*len(headers)) + "|"]

    def fmt_val(i, v):
        if isinstance(v, float):
            return format(v, float_fmt)
        return str(v)

    # Head rows
    for _, row in df_copy.head(max_rows).iterrows():
        lines.append("| " + " | ".join([fmt_val(i, v) for i, v in enumerate(row.values)]) + " |")
    
    # Ellipsis if many rows
    if n > 2*max_rows:
        lines.append("| ... | " * len(headers) + "|")
    
    # Tail rows
    for _, row in df_copy.tail(max_rows).iterrows():
        lines.append("| " + " | ".join([fmt_val(i, v) for i, v in enumerate(row.values)]) + " |")

    return "\n".join(lines)

# ---------------------- PDF Report using ReportLab ----------------------
def md_to_pdf_reportlab(model, pdf_file="RC_Column_Report.pdf"):
    """
    Generate readable PDF report using ReportLab.
    Tables, idealized points, and derived properties included.
    """
    out_dir = os.path.dirname(pdf_file)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)

    doc = SimpleDocTemplate(pdf_file, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    # Header
    story.append(Paragraph("RC Column Nonlinear Analysis Report", styles['Title']))
    story.append(Paragraph(f"Generated on: {datetime.datetime.now():%Y-%m-%d %H:%M:%S}", styles['Normal']))
    story.append(Spacer(1, 12))

    # Geometry
    story.append(Paragraph("1. Column Geometry", styles['Heading2']))
    geom_lines = [
        f"Section type: {model.section_type}",
        f"Column length, L = {model.L:.2f}",
        f"Concrete cover = {model.cover:.2f}"
    ]
    if model.section_type == "circular":
        geom_lines.append(f"Diameter, D = {model.D:.2f}")
    else:
        geom_lines.append(f"Width, B = {model.B:.2f}")
        geom_lines.append(f"Depth, H = {model.H:.2f}")
    for line in geom_lines:
        story.append(Paragraph(line, styles['Normal']))
    story.append(Spacer(1, 12))

    # Derived properties
    story.append(Paragraph("2. Derived Section Properties", styles['Heading2']))
    derived_lines = [
        f"Gross area, Ag = {model.Ag:.2f}",
        f"Steel area, As = {model.As:.2f}",
        f"Moment of inertia, Iz = {model.Iz:.2f}",
        f"Plastic hinge length, lp = {model.lp:.2f}"
    ]
    if hasattr(model, "k_eff"):
        derived_lines.append(f"Effective stiffness modifier, k_eff = {model.k_eff:.4f}")
    for line in derived_lines:
        story.append(Paragraph(line, styles['Normal']))
    story.append(Spacer(1, 12))

    # Materials
    story.append(Paragraph("3. Material Properties", styles['Heading2']))
    mat_lines = [
        f"Concrete f'c = {model.fc:.2f}",
        f"Concrete Ec = {model.Ec:.2f}",
        f"Steel fy = {model.fy:.2f}, fu = {model.fu:.2f}, Es = {model.Es:.2f}",
        f"Strain hardening modulus Esh = {model.Esh:.2f}"
    ]
    for line in mat_lines:
        story.append(Paragraph(line, styles['Normal']))
    story.append(Spacer(1, 12))

    # Reinforcement
    story.append(Paragraph("4. Reinforcement Details", styles['Heading2']))
    if model.section_type == "circular":
        story.append(Paragraph(f"Number of bars = {model.nBars}, diameter = {model.db}", styles['Normal']))
    else:
        story.append(Paragraph(f"Top bars = {model.nBarsTop} (dia {model.dbTop})", styles['Normal']))
        story.append(Paragraph(f"Bottom bars = {model.nBarsBot} (dia {model.dbBot})", styles['Normal']))
        if model.nBarsInt > 0:
            story.append(Paragraph(f"Interior bars = {model.nBarsInt} (dia {model.dbInt})", styles['Normal']))
    story.append(Spacer(1, 12))

    # ------------------- Fiber Section -------------------
    story.append(Paragraph("Reinforced Concrete Fiber Section", styles['Heading2']))
    plots_dir = os.path.join(os.path.dirname(pdf_file), "plots")
    os.makedirs(plots_dir, exist_ok=True)
    # Correct: Save directly inside the plot_fib_section method
    fiber_plot_path = os.path.join(plots_dir, "fiber_section.png")
    model.plot_fib_section(save_path=fiber_plot_path)  # this saves the figure correctly
    story.append(Image(fiber_plot_path, width=400, height=250))
    story.append(Spacer(1, 12))


    # M-Phi
    if hasattr(model, "df_m_phi"):
        story.append(Paragraph("5. Moment-Curvature Analysis", styles['Heading2']))
        story.append(Paragraph(f"Number of steps: {len(model.df_m_phi)}", styles['Normal']))
        story.append(Spacer(1, 6))
        df_table = pd.concat([model.df_m_phi.head(10), model.df_m_phi.tail(10)])
        table_data = df_to_table_data(df_table)
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT')
        ]))
        story.append(tbl)
        story.append(Spacer(1, 6))

        if hasattr(model, "df_m_phi_idealized"):
            story.append(Paragraph("Idealized Points", styles['Heading3']))
            df_ideal = model.df_m_phi_idealized.copy()
            df_ideal.insert(0, "Points", ["Origin", "Yield", "Idealized Yield", "Ultimate"])
            table_data = df_to_table_data(df_ideal, show_index=False)
            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT')
            ]))
            story.append(tbl)
            story.append(Spacer(1, 12))

    # -------------------- M-Phi Plot --------------------
    if hasattr(model, "df_m_phi") and not model.df_m_phi.empty:
        story.append(Paragraph("Moment-Curvature Curve", styles['Heading3']))

        plt.figure(figsize=(6,4))
        # Original M-phi curve
        plt.plot(model.df_m_phi['curvatures'], model.df_m_phi['moments'], 'b-o', label='M-φ Curve')

        # Idealized points if available
        if hasattr(model, "df_m_phi_idealized"):
            df_ideal = model.df_m_phi_idealized.copy()
            points_labels = ["Origin", "Yield", "Idealized Yield", "Ultimate"]
            plt.plot(df_ideal['curvatures'], df_ideal['moments'], 
                        color='red', marker='s', label='Idealized Points')


        plt.xlabel("Curvature")
        plt.ylabel("Moment")
        plt.title("Moment-Curvature")
        plt.grid(True)
        plt.legend()

        plots_dir = os.path.join(os.path.dirname(pdf_file), "plots")
        os.makedirs(plots_dir, exist_ok=True)
        mp_phi_plot_path = os.path.join(plots_dir, "moment_curvature.png")
        plt.savefig(mp_phi_plot_path, bbox_inches='tight')
        plt.close()

        story.append(Image(mp_phi_plot_path, width=400, height=250))
        story.append(Spacer(1, 12))

    # Pushover
    if hasattr(model, "df_pushover"):
        story.append(Paragraph("6. Pushover Analysis", styles['Heading2']))
        story.append(Paragraph(f"Number of steps: {len(model.df_pushover)}", styles['Normal']))
        story.append(Spacer(1, 6))
        df_table = pd.concat([model.df_pushover.head(10), model.df_pushover.tail(10)])
        table_data = df_to_table_data(df_table)
        tbl = Table(table_data, repeatRows=1)
        tbl.setStyle(TableStyle([
            ('GRID', (0,0), (-1,-1), 0.5, colors.black),
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('ALIGN', (0,0), (-1,-1), 'RIGHT')
        ]))
        story.append(tbl)
        story.append(Spacer(1, 6))

        if hasattr(model, "df_pushover_idealized"):
            story.append(Paragraph("Idealized Points", styles['Heading3']))
            df_ideal = model.df_pushover_idealized.copy()
            df_ideal.insert(0, "Points", ["Origin", "Yield", "Idealized Yield", "Ultimate"])
            table_data = df_to_table_data(df_ideal, show_index=False)
            tbl = Table(table_data, repeatRows=1)
            tbl.setStyle(TableStyle([
                ('GRID', (0,0), (-1,-1), 0.5, colors.black),
                ('BACKGROUND', (0,0), (-1,0), colors.grey),
                ('ALIGN', (0,0), (-1,-1), 'RIGHT')
            ]))
            story.append(tbl)
            story.append(Spacer(1, 12))

    # -------------------- Pushover Plot --------------------
    if hasattr(model, "df_pushover") and not model.df_pushover.empty:
        story.append(Paragraph("Pushover Curve", styles['Heading3']))

        plt.figure(figsize=(6,4))
        # Original pushover curve
        plt.plot(model.df_pushover['displacements'], model.df_pushover['forces'], 'r-o', label='Pushover Curve')

        # Idealized points if available
        if hasattr(model, "df_pushover_idealized"):
            df_ideal = model.df_pushover_idealized.copy()
            points_labels = ["Origin", "Yield", "Idealized Yield", "Ultimate"]
            plt.plot(df_ideal['displacements'], df_ideal['forces'], 
                        color='blue', marker='s', label='Idealized Points')


        plt.xlabel("Displacement")
        plt.ylabel("Force")
        plt.title("Pushover Curve")
        plt.grid(True)
        plt.legend()

        pushover_plot_path = os.path.join(plots_dir, "pushover.png")
        plt.savefig(pushover_plot_path, bbox_inches='tight')
        plt.close()

        story.append(Image(pushover_plot_path, width=400, height=250))
        story.append(Spacer(1, 12))

    doc.build(story)
    return pdf_file
