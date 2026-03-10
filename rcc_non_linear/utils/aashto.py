def get_Lp(L, db, fye):
    """Calculate the plastic hinge length (Lp) based on AASHTO specifications (ksi, in units)"""
    lp = max(0.08*L+ 0.15*db*fye, 0.3*db*fye)
    return lp

def get_idealized_displacements(L, Lp, phi_yi, phi_u):
    """Calculate idealized displacements at yield and ultimate based on curvature and plastic hinge length"""
    disp_yi = phi_yi * L**2 / 3
    disp_p = (phi_u - phi_yi) * Lp * (L - Lp/2)
    disp_u = disp_yi + disp_p
    return disp_yi, disp_u

if __name__ == "__main__":
    # Example usage
    L = 192
    db = 1.27  # in
    fye = 68.0  # ksi
    lp = get_Lp(L, db, fye)
    print(f"Calculated plastic hinge length (Lp): {lp:.2f} in")