#!/usr/bin/env python3
"""Compare surface-density outputs with GSW on a temperature/salinity grid.

Uses P=0 dbar and reference salinity SP * 35.16504 / 35.
Reports RMS and maximum absolute errors without fitting coefficients.
"""
import gsw
import numpy as np

from contrib.inkfish.seawater_density.logger.utils.seawater_density import surface_density

UPS = 35.16504 / 35.0  # Practical salinity to reference salinity.


def build_reference_grid():
    """Return T, practical salinity, sound speed and density at P=0 dbar."""
    temperature, salinity = np.meshgrid(
        np.linspace(0.0, 40.0, 81), np.linspace(0.0, 40.0, 81))
    temperature = temperature.ravel()
    salinity = salinity.ravel()
    reference_salinity = salinity * UPS
    sound_speed = gsw.sound_speed_t_exact(reference_salinity, temperature, 0.0)
    density = gsw.rho_t_exact(reference_salinity, temperature, 0.0)
    return temperature, salinity, sound_speed, density


def main():
    """Print full-grid and open-ocean operating-regime error statistics."""
    temperature, salinity, sound_speed, reference = build_reference_grid()
    predicted = np.array([surface_density(t, c) for t, c in zip(temperature, sound_speed)])
    error = predicted - reference
    operating = (salinity >= 30.0) & (salinity <= 40.0) & (temperature <= 35.0)
    print(f'TEOS-10 surface grid: {temperature.size} points; gsw {gsw.__version__}; '
          f'numpy {np.__version__}')
    print('P=0 dbar; reference salinity = practical salinity * 35.16504 / 35')
    for label, values in [('T 0-40 C, SP 0-40', error),
                          ('T 0-35 C, SP 30-40', error[operating])]:
        rms = float(np.sqrt(np.mean(values ** 2)))
        maximum = float(np.max(np.abs(values)))
        print(f'{label}: RMS={rms:.6f}, max={maximum:.6f} kg/m^3')


if __name__ == '__main__':
    main()
