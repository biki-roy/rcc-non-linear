import math
from rcc_non_linear.concrete_models.mander_model import RectConcreteMander, CircConcreteMander
from rcc_non_linear.opensees_model.rect_section import RectSection
from rcc_non_linear.opensees_model.circ_section import CircSection
from rcc_non_linear.utils.helper import caltrans_bilinear 

class Model:
    def __init__(self, props: dict):
        """
        props: dictionary containing column properties
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
        elif self.section_type == "rectangular":
            self.nBarsTop = props["nBarsTop"]
            self.dbTop = props["dbTop"]
            self.nBarsBot = props["nBarsBot"]
            self.dbBot = props["dbBot"]
            self.nBarsInt = props.get("nBarsInt", 0)
            self.dbInt = props.get("dbInt", 0)
            self.nx = props.get("nx", 2)   # number of transverse bars in x direction
            self.ny = props.get("ny", 2)   # number of transverse bars in y direction
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
        self.confined_props = material.confined_props()
        self.unconfined_props = material.unconfined_props()
        ops.uniaxialMaterial('Concrete01', self.core_tag, *self.confined_props)
        ops.uniaxialMaterial('Concrete01', self.cover_tag, *self.unconfined_props)
        ops.uniaxialMaterial('ReinforcingSteel', self.bar_tag, self.fy, self.fu, self.Es, self.Esh, self.e_sh, self.e_ult)
    
    def define_section(self):
        if self.section_type == "circular":
            self.fib_section = CircSection(self.D, self.cover, self.Ec,
                                           self.nBars, self.db, self.dh, 
                                           self.fib_sec_tag, self.core_tag, self.cover_tag, self.bar_tag)
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
                cover_material=self.cover_tag, bar_material=self.bar_tag
            )
            self.core_h = self.fib_section.core_h
            self.bar_h = self.fib_section.bar_h
        
    def plot_fib_section(self):
        self.fib_section.plot()

    # def create_element(self, analysis_type: str):
    #     import openseespy.opensees as ops
    #     ops.node(1, 0.0, 0.0)
    #     ops.node(2, 0.0, 0.0) if analysis_type=="moment-curvature" else ops.node(2, self.L, 0.0)
    #     ops.fix(1, 1, 1, 1)
    #     ops.mass(2, 1.0, 1.0, 1.0)

    def run_M_phi_analysis(self, maxK=0.01, dK=0.00001):
        from rcc_non_linear.opensees_model.m_phi import moment_curvature_analysis
        self.create_model()  
        results_df, yield_step = moment_curvature_analysis(self, maxK, dK)
        bilinear_df = caltrans_bilinear(results_df, yield_step)
        return results_df, bilinear_df, yield_step


    def run_pushover_analysis(self, maxU=40, dU=0.05):
        from rcc_non_linear.opensees_model.pushover import pushover_analysis
        self.create_model()  
        results_df, yield_step = pushover_analysis(self, maxU, dU)
        bilinear_df = caltrans_bilinear(results_df, yield_step)
        return results_df, bilinear_df, yield_step

