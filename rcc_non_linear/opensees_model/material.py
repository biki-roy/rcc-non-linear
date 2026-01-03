from rcc_non_linear import RectConcreteMander, CircConcreteMander

class Material:
    def __init__(self, section_type, **kwargs):
        import openseespy.opensees as ops

        if section_type == "rect_mander":
            material = RectConcreteMander(**kwargs)
        elif section_type == "circ_mander":
            material = CircConcreteMander(**kwargs)
        else:
            raise ValueError(f"Unknown material type: {section_type}")
        self.confined_props = material.confined_props()
        self.unconfined_props = material.unconfined_props()
        ops.uniaxialMaterial('Concrete01', 1, *self.confined_props)
        ops.uniaxialMaterial('Concrete01', 2, *self.unconfined_props)
        ops.uniaxialMaterial('ReinforcingSteel', 3, kwargs['fyh'], 95, 29000, 29000*0.043, 0.005, 0.1)