#!/usr/bin/env python3
"""Calculate surface seawater density from sound speed and in-situ temperature.

Uses Allen et al. (2025), Table 6 density coefficients at P=0 dbar.
Inputs are temperature in deg C and sound speed in m/s; output is kg/m^3.
See ../../THIRD_PARTY_NOTICES.md for the source and license.
"""

CW = 1402.388     # reference sound speed at P=0 dbar, T=0 deg C (m/s)
RHO0 = 1000.000   # reference density (kg/m^3)

# Allen et al. 2025, Table 6 (rho column), reduced to P=0.
# Paper material: CC BY 4.0; see ../../THIRD_PARTY_NOTICES.md.
_A = (-3.000886e+00, -2.620089e-03, -2.057901e-04, -2.021927e-06, 4.035600e-08)  # T^1,3,4,5,6
_D = (5.892674e-01, 3.540712e-05, -1.071977e-06, 1.097079e-08, -3.449155e-11)    # q^1,3,4,5,6
_E = (8.506913e-03, 2.284598e-03, 2.383278e-04, 5.244113e-06, -3.724088e-08)     # q   * T^1..T^5
_F = (-5.809403e-04, -1.043967e-04, -4.016505e-06)                               # q^2 * T^1..T^3
_G = (1.884874e-05, 1.373007e-06, 1.024091e-08)                                  # q^3 * T^1..T^3
_H = (-2.097771e-07, -4.245977e-09)                                              # q^4 * T^1..T^2
_I = (6.627039e-10,)                                                             # q^5 * T^1

# Optional rectangular input bounds; not a salinity check.
TEMP_RANGE = (0.0, 40.0)              # deg C
SOUND_SPEED_RANGE = (1400.0, 1570.0)  # m/s


def surface_density(temp_c, sound_speed):
    """Return density at P=0 dbar from temperature (deg C) and sound speed (m/s).

    Inputs are converted with float(); TypeError or ValueError returns None.
    Output is kg/m^3. No range or finite-value checks are applied.
    """
    try:
        t = float(temp_c)
        q = float(sound_speed) - CW
    except (TypeError, ValueError):
        return None

    a1, a3, a4, a5, a6 = _A
    d1, d3, d4, d5, d6 = _D
    e1, e3, e5, e7, e9 = _E
    f1, f3, f5 = _F
    g1, g3, g5 = _G
    h1, h3 = _H
    (i1,) = _I

    d_rho_t = a1*t + a3*t**3 + a4*t**4 + a5*t**5 + a6*t**6
    d_rho_c = d1*q + d3*q**3 + d4*q**4 + d5*q**5 + d6*q**6
    d_rho_tc = (q * (e1*t + e3*t**2 + e5*t**3 + e7*t**4 + e9*t**5)
                + q**2 * (f1*t + f3*t**2 + f5*t**3)
                + q**3 * (g1*t + g3*t**2 + g5*t**3)
                + q**4 * (h1*t + h3*t**2)
                + q**5 * (i1*t))
    return RHO0 + d_rho_t + d_rho_c + d_rho_tc


def in_valid_range(temp_c, sound_speed):
    """Check TEMP_RANGE and SOUND_SPEED_RANGE without inferring salinity."""
    try:
        t = float(temp_c)
        c = float(sound_speed)
    except (TypeError, ValueError):
        return False
    return (TEMP_RANGE[0] <= t <= TEMP_RANGE[1]
            and SOUND_SPEED_RANGE[0] <= c <= SOUND_SPEED_RANGE[1])


if __name__ == '__main__':
    for t, c in [(30.920, 1549.480), (15.0, 1507.0), (25.0, 1535.0)]:
        print(f"T={t:6.2f} C  c={c:8.2f} m/s  ->  rho = {surface_density(t, c):.3f} kg/m^3")
