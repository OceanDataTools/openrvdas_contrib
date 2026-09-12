#!/usr/bin/env python3
"""Test density calculations, cached inputs, metadata, and TEOS-10 agreement.

The TEOS-10 test requires gsw and numpy; other tests require OpenRVDAS.
See ../THIRD_PARTY_NOTICES.md for the reference formula attribution.
"""
import unittest
from unittest.mock import patch

from contrib.inkfish.seawater_density.logger.utils.seawater_density import surface_density, CW, RHO0
from contrib.inkfish.seawater_density.logger.transforms.water_density_transform import (
    WaterDensityTransform)
from logger.utils.das_record import DASRecord

try:
    import gsw
    import numpy as np
    HAVE_GSW = True
except ImportError:
    HAVE_GSW = False

UPS = 35.16504 / 35.0  # practical -> reference salinity (paper convention)


class TestSeawaterDensityHelper(unittest.TestCase):
    def test_reference_point(self):
        # All correction terms vanish at T=0 and c=CW.
        self.assertAlmostEqual(surface_density(0.0, CW), RHO0, places=6)

    def test_sample_point(self):
        # Check a representative warm-water sample.
        self.assertAlmostEqual(surface_density(30.920, 1549.480), 1022.951, delta=0.01)

    def test_invalid_inputs(self):
        self.assertIsNone(surface_density(None, 1500.0))
        self.assertIsNone(surface_density(20.0, None))
        self.assertIsNone(surface_density('x', 'y'))

    @unittest.skipUnless(HAVE_GSW, 'gsw not installed (offline validation dep)')
    def test_validates_against_teos10_operating_regime(self):
        # Surface grid: SP 30-40, T 0-35 deg C.
        SP = np.linspace(30.0, 40.0, 41)
        T = np.linspace(0.0, 35.0, 71)
        TT, SS = np.meshgrid(T, SP)
        TT = TT.ravel()
        SS = SS.ravel()
        SR = SS * UPS
        c = gsw.sound_speed_t_exact(SR, TT, 0.0)
        rho_ref = gsw.rho_t_exact(SR, TT, 0.0)
        err = np.array([surface_density(t, ci) for t, ci in zip(TT, c)]) - rho_ref
        rms = float(np.sqrt(np.mean(err ** 2)))
        mx = float(np.max(np.abs(err)))
        # Bound RMS and maximum differences from GSW on this grid.
        self.assertLess(rms, 0.02, f'operating-regime RMS too high: {rms}')
        self.assertLess(mx, 0.07, f'operating-regime max err too high: {mx}')

    def test_matches_reference_formula(self):
        """Check the Table 6 density formula at P=0 dbar."""
        def reference(c, T):
            cw = 1402.388
            q = c - cw
            return (1000.0
                    + (-3.000886e+00 * T) + (-2.620089e-03 * T**3) + (-2.057901e-04 * T**4)
                    + (-2.021927e-06 * T**5) + (4.035600e-08 * T**6)
                    + (5.892674e-01 * q) + (3.540712e-05 * q**3) + (-1.071977e-06 * q**4)
                    + (1.097079e-08 * q**5) + (-3.449155e-11 * q**6)
                    + q * (8.506913e-03 * T + 2.284598e-03 * T**2 + 2.383278e-04 * T**3
                           + 5.244113e-06 * T**4 - 3.724088e-08 * T**5)
                    + q**2 * (-5.809403e-04 * T - 1.043967e-04 * T**2 - 4.016505e-06 * T**3)
                    + q**3 * (1.884874e-05 * T + 1.373007e-06 * T**2 + 1.024091e-08 * T**3)
                    + q**4 * (-2.097771e-07 * T - 4.245977e-09 * T**2)
                    + q**5 * (6.627039e-10 * T))
        for T, c in [(30.920, 1549.480), (15.0, 1507.0), (25.0, 1535.0),
                     (2.0, 1412.0), (0.0, 1402.388), (40.0, 1560.0), (10.0, 1480.0)]:
            self.assertAlmostEqual(surface_density(T, c), reference(c, T), places=6,
                                   msg=f'mismatch at T={T}, c={c}')


class TestWaterDensityTransform(unittest.TestCase):
    def _transform(self, **kw):
        kw.setdefault('sound_speed_field', 'SVP_SoundSpeed')
        kw.setdefault('temp_field', 'SVP_WaterTemp')
        kw.setdefault('density_name', 'SVP_WaterDensity')
        return WaterDensityTransform(**kw)

    def test_emits_density_from_svs_record(self):
        tx = self._transform(data_id='water_density')
        rec = DASRecord(timestamp=1_700_000_000.0, data_id='svp',
                        fields={'SVP_SoundSpeed': 1549.480, 'SVP_WaterTemp': 30.920})
        out = tx.transform(rec)
        self.assertTrue(out, 'expected a density record')
        das = out[0]
        self.assertIn('SVP_WaterDensity', das.fields)
        self.assertAlmostEqual(das.fields['SVP_WaterDensity'], 1022.951, delta=0.01)
        self.assertEqual(das.data_id, 'water_density')

    def test_waits_for_trigger_field(self):
        # Sound speed is the only output trigger.
        tx = self._transform(update_on_fields=['SVP_SoundSpeed'])
        out = tx.transform(DASRecord(timestamp=1_700_000_000.0, data_id='svp',
                                     fields={'SVP_WaterTemp': 30.920}))
        self.assertEqual(out, [], 'should not emit before the trigger field arrives')
        out = tx.transform(DASRecord(timestamp=1_700_000_001.0, data_id='svp',
                                     fields={'SVP_SoundSpeed': 1549.480}))
        self.assertTrue(out)
        self.assertIn('SVP_WaterDensity', out[0].fields)

    def test_no_output_when_value_missing(self):
        tx = self._transform()
        out = tx.transform(DASRecord(timestamp=1_700_000_000.0, data_id='svp',
                                     fields={'SVP_SoundSpeed': 1549.480}))
        self.assertEqual(out, [], 'should not emit with temperature still missing')

    def test_fields_method(self):
        tx = self._transform()
        self.assertEqual(tx.fields(), ['SVP_SoundSpeed', 'SVP_WaterTemp'])

    def test_suppresses_stale_temperature(self):
        tx = self._transform(max_field_age={'SVP_WaterTemp': 5})
        tx.transform(DASRecord(timestamp=100, fields={'SVP_WaterTemp': 30.920}))
        self.assertEqual(tx.transform(DASRecord(
            timestamp=106, fields={'SVP_SoundSpeed': 1549.480})), [])
        self.assertTrue(tx.transform(DASRecord(
            timestamp=107, fields={'SVP_WaterTemp': 30.920})))

    def test_older_record_does_not_replace_cached_value(self):
        tx = self._transform(update_on_fields=['SVP_SoundSpeed'])
        tx.transform(DASRecord(timestamp=100, fields={'SVP_WaterTemp': 30.920}))
        tx.transform(DASRecord(timestamp=99, fields={'SVP_WaterTemp': 10.0}))
        out = tx.transform(DASRecord(timestamp=101, fields={'SVP_SoundSpeed': 1549.480}))
        self.assertAlmostEqual(out[0].fields['SVP_WaterDensity'], 1022.951, delta=0.01)

    def test_accepts_cached_data_field_dictionary(self):
        tx = self._transform()
        out = tx.transform({'SVP_SoundSpeed': [(100, 1549.480)],
                            'SVP_WaterTemp': [(100, 30.920)]})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].timestamp, 100)
        self.assertAlmostEqual(out[0].fields['SVP_WaterDensity'], 1022.951, delta=0.01)

    def test_metadata_interval(self):
        tx = self._transform(metadata_interval=10)
        record = DASRecord(timestamp=100, fields={'SVP_SoundSpeed': 1549.480,
                                                  'SVP_WaterTemp': 30.920})
        with patch('contrib.inkfish.seawater_density.logger.transforms.'
                   'water_density_transform.time.time',
                   side_effect=[100, 105, 111]):
            first = tx.transform(record)[0]
            second = tx.transform(record)[0]
            third = tx.transform(record)[0]
        self.assertEqual(first.metadata['fields']['SVP_WaterDensity']['units'], 'kg/m^3')
        self.assertFalse(second.metadata)
        self.assertEqual(first.metadata, third.metadata)


if __name__ == '__main__':
    unittest.main()
