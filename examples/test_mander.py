from rcc_non_linear.concrete_models.mander_model import RectConcreteMander
mander = RectConcreteMander(4.5, 48, 24, 2, 0.5, 3, 68, 0.12, 3, 4 )
print(mander.confined_props())
