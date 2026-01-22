from rcc_non_linear import RectConcreteMander
from rcc_non_linear import RectSection

import openseespy.opensees as ops
ops.wipe()
ops.model('basic', '-ndm', 2, '-ndf', 3)

mander = RectConcreteMander(4.5, 48, 24, 2, 0.5, 3, 68, 0.12)

# ops.uniaxialMaterial('Concrete01', 1, *mander.confined_props())
# ops.uniaxialMaterial('Concrete01', 2, *mander.unconfined_props())
# ops.uniaxialMaterial('ReinforcingSteel', 3, 68, 95, 29000, 29000*0.043, 0.005, 0.1)

# section = RectSection(48, 24, 2, 29000, 3, 1.5, 3, 1.5, 4, 1.5, 0.5, 1, 1, 2, 3)
# section.plot()