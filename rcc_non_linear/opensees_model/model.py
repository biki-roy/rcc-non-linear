import math
import os
from rcc_non_linear.concrete_models.mander_model import RectConcreteMander, CircConcreteMander, SteelMander
from rcc_non_linear.opensees_model.rect_section import RectSection
from rcc_non_linear.opensees_model.circ_section import CircSection
from rcc_non_linear.utils.helper import caltrans_bilinear 
from rcc_non_linear.utils.report import create_markdown_report, md_to_pdf_reportlab

class Model:
    def __init__(self, props: dict):
        """
        Initialize a reinforced concrete column model.
        -----------
        props : dict
            Dictionary containing geometric, material, reinforcement, and axial load on the column excluding self-weight. The model supports both rectangular and
            circular cross-sections, which are automatically detected based on
            the provided keys.

            Required general properties:
            - fc : Unconfined concrete compressive strength
            - L  : Column length
            - cover : Concrete cover

            Geometry definition (one of the following must be provided):
            - Rectangular section:
                B : Width of section (normal to the direction of lateral load)
                H : Depth of section (along the direction of lateral load)
            - Circular section:
                D : Diameter of section

            Longitudinal reinforcement:
            - Circular section:
                nBars : Number of longitudinal bars
                db    : Diameter of longitudinal bars
            - Rectangular section:
                nBarsTop, dbTop : Number and diameter of top bars
                nBarsBot, dbBot : Number and diameter of bottom bars
                nBarsInt, dbInt : Intermediate bars (default=0)
                nx: Number of transverse bar legs in x-direction (default = 2) 
                ny: Number of transverse bar legs in y-direction (default = 2) 

            Longitudinal reinforcement properties:
            - fy : Longitudinal reinforcement yield strength
            - fu : Longitudinal reinforcement ultimate strength
            - Es   : Elastic modulus of steel (default = 29000)
            - Esh  : Strain hardening modulus (default = 0.043 × Es)
            - e_sh : Strain at onset of hardening (default = 0.005)
            - e_ult: Ultimate strain (default = 0.1)

            Transverse reinforcement properties:
            - dh : Transverse reinforcement diameter
            - sh : Transverse reinforcement spacing
            - fyh : Yield strength (default = 68)
            - fuh : Ultimate strength (default = 95)
            - esm : Ultimate strain (default = 0.1)

            Loading:
            - P_axial : Applied axial load (default = 0.0)

            Discretization parameters:
            - Circular: nAng (default = 30), nRad (default = 20), nRad_cover (default = 8)
            - Rectangular: div (default = 30), divD (default = 30), divCover (default = 5)
        """
        # Geometry & materials
        self.fc = props["fc"]
        self.D = props.get("D", None)     # diameter for circular section
        self.B = props.get("B", None)    # width for rectangular section  
        self.H = props.get("H", None)   #depth for rectangular section
        self.L = props["L"]         # length of the column

        self.section_type = "rectangular" if self.B and self.H else "circular"

        self.cover = props["cover"]      # concrete cover   

        if self.section_type == "circular":
            self.nBars = props["nBars"]
            self.db = props["db"]
            self.nAng = props.get("nAng", 30)
            self.nRad = props.get("nRad", 20)
            self.nRad_cover= props.get("nRad_cover", 8)
            self.rupture_limit = props.get("rupture_limit", 0.2)
        elif self.section_type == "rectangular":
            self.nBarsTop = props["nBarsTop"]
            self.dbTop = props["dbTop"]
            self.nBarsBot = props["nBarsBot"]
            self.dbBot = props["dbBot"]
            self.nBarsInt = props.get("nBarsInt", 0)
            self.dbInt = props.get("dbInt", 0)
            self.nx = props.get("nx", 2)   # number of transverse bars in x direction
            self.ny = props.get("ny", 2)   # number of transverse bars in y direction
            self.divB = props.get("divB", 30)
            self.divD = props.get("divD", 30)
            self.divCover = props.get("divCover", 5)
          
        else:
            raise ValueError("Either B and H (rectangular) or D (circular) must be provided.")

        self.fy = props["fy"]
        self.fu = props["fu"]
        self.Es = props.get("Es", 29000)   # default modulus of elasticity
        self.Esh = props.get("Esh", 0.043 * self.Es)   # default strain hardening modulus
        self.e_sh = props.get("e_sh", 0.005)
        self.e_ult = props.get("e_ult", 0.1)

        self.dh = props["dh"]
        self.sh = props["sh"]
        self.fyh = props.get("fyh", 68)   # default transverse reinforcement yield strength
        self.fuh = props.get("fuh", 95)   # default transverse reinforcement ultimate strength
        self.esm = props.get("esm", 0.1)  # default transverse reinforcement ultimate strain
        self.P_axial = props.get("P_axial", 0.0)  # axial load

        self.core_tag, self.cover_tag, self.bar_tag = 1, 2, 3  # material tags
        self.fib_sec_tag, self.elastic_sec_tag = 1, 2
        self.failure_criteria = props.get("failure_criteria" , ["core","rebar","strength" ])
        
        # Derived
        self.Ec = 57 * math.sqrt(self.fc * 1000)

        if self.section_type == "circular":
            self.Ag = math.pi * (self.D**2) / 4
            self.As = self.nBars * math.pi * (self.db**2) / 4
            self.Iz = math.pi * ((self.D/2) ** 4) / 4
        else:
            self.Ag = self.B * self.H
            self.As = (self.nBarsTop + self.nBarsBot + self.nBarsInt) * math.pi * (self.dbTop**2) / 4
            self.Iz = (self.B * self.H**3) / 12.0

        db = self.db if self.section_type == "circular" else max(self.dbTop, self.dbBot)
        self.lp = max(0.08 * self.L + 0.15 * self.fy * db, 0.3*db*self.fy)
        self.m_phi_done = False
        self.create_model()        

    def create_model(self):
        import openseespy.opensees as ops
        ops.wipe()
        ops.model('basic', '-ndm', 2, '-ndf', 3)
        self.define_materials()
        self.define_section()

    def define_materials(self):
        import openseespy.opensees as ops
        if self.section_type == "circular":
            material = CircConcreteMander(
                fc_prime=self.fc, D=self.D, cover=self.cover,
                dh=self.dh, sh=self.sh,
                fyh=self.fyh, esm=self.esm
            )   
        else:
            material = RectConcreteMander(
                fc_prime=self.fc,
                B=self.B, H=self.H, cover=self.cover,
                dh=self.dh, sh=self.sh,
                fyh=self.fyh, esm=self.esm,
                nx=self.nx, ny=self.ny
            )
            self.k_confinement = material.k
        self.confined_props = material.confined_props()
        self.unconfined_props = material.unconfined_props()
        ops.uniaxialMaterial('Concrete01', self.core_tag, *self.confined_props)
        ops.uniaxialMaterial('Concrete01', self.cover_tag, *self.unconfined_props)
        ops.uniaxialMaterial('ReinforcingSteel', self.bar_tag, self.fy, self.fu, self.Es, self.Esh, self.e_sh, self.e_ult)
        self.concrete = material
        self.steel = SteelMander(self.fy, self.fu, self.Es, self.Esh, self.e_sh, self.e_ult)
    
    def define_section(self):
        if self.section_type == "circular":
            self.fib_section = CircSection(self.D, self.cover, self.Ec,
                                           self.nBars, self.db, self.dh, 
                                           self.fib_sec_tag, self.core_tag, self.cover_tag, self.bar_tag, self.nAng, self.nRad, self.nRad_cover)
            self.core_h = self.fib_section.R_core
            self.bar_h = self.fib_section.R_bar
        else:
            self.fib_section = RectSection(
                B=self.B, H=self.H, cover=self.cover, Ec=self.Ec,
                nBarsTop=self.nBarsTop, dbTop=self.dbTop,
                nBarsBot=self.nBarsBot, dbBot=self.dbBot,
                nBarsInt=self.nBarsInt, dbInt=self.dbInt,
                dh=self.dh,
                sec_tag=self.fib_sec_tag, core_material=self.core_tag,
                cover_material=self.cover_tag, bar_material=self.bar_tag,
                divB = self.divB, divD = self.divD, divCover = self.divCover
            )
            self.core_h = self.fib_section.core_h
            self.bar_h = self.fib_section.bar_h
        
    def plot_fib_section(self, save_path=None):
        self.fib_section.plot()       # draw the figure
        import matplotlib.pyplot as plt
        if save_path:                 # if a path is provided
            plt.savefig(save_path, bbox_inches='tight')  # save current figure
            plt.close()               # close figure to free memory
        else:
            plt.show()                # just display interactively

    def run_M_phi_analysis(self, maxK=0.01, dK=0.00001):
        from rcc_non_linear.opensees_model.m_phi import moment_curvature_analysis
        self.create_model()  
        results_df, yield_step = moment_curvature_analysis(self, maxK, dK)
        bilinear_df = caltrans_bilinear(results_df, yield_step)
        self.k_eff = self.get_stiffness_modifier(bilinear_df)
        self.m_phi_done = True
        self.df_m_phi, self.df_m_phi_idealized = results_df, bilinear_df
        return results_df, bilinear_df, yield_step

    def get_stiffness_modifier(self, bilinear_df):
        phiY, mY = bilinear_df.iloc[1, 0], bilinear_df.iloc[1, 1]
        I_eff = mY/(phiY*self.Ec)
        return I_eff/ self.Iz

    def run_pushover_analysis(self, maxU=None, dU=0.05, self_wt=True):
        if maxU is None: maxU = 0.2 * self.L
        from rcc_non_linear.opensees_model.pushover import pushover_analysis
        if not self.m_phi_done:
            self.run_M_phi_analysis()
        self.create_model()  
        results_df, yield_step = pushover_analysis(self, maxU, dU, self_wt)
        bilinear_df = caltrans_bilinear(results_df, yield_step)
        bilinear_df["drift %"] = bilinear_df["displacements"] *100 / self.L 
        self.df_pushover, self.df_pushover_idealized = results_df, bilinear_df
        return results_df, bilinear_df, yield_step

    def create_report(self, filename="RC_Column_Report", out_dir=None, generate_pdf=True):
        """
        Create Markdown and PDF report.
        """
        # Markdown
        md_path = create_markdown_report(self, filename=filename+".md", out_dir=out_dir)
        
        if generate_pdf:
            pdf_path = md_to_pdf_reportlab(self, pdf_file=os.path.join(out_dir or "results", filename+".pdf"))
            return pdf_path

        return md_path

