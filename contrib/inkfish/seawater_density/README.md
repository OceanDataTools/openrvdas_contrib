# Surface seawater density transform

{WaterDensityTransform} derives surface seawater density in kg/m³ from
sound speed in m/s and in-situ ITS-90 temperature in °C. It was developed for an
AML-1 RT SVS aboard R/V Hydra and can consume the same fields from other
sensors. The runtime helper is pure Python and adds no third-party
dependencies to an existing OpenRVDAS installation.

The calculation implements the **Table 6 density (ρ) coefficients of
[Allen et al. (2025)](https://doi.org/10.1002/lom3.10715), reduced to sea
pressure P = 0 dbar**. Zero sea pressure means atmospheric surface pressure.
It does not take pressure as an input or correct measurements taken at depth. See
[THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md) for the complete citation,
CC BY 4.0 attribution, and adaptation details.

## Files

| File | Purpose |
| --- | --- |
| `logger/transforms/water_density_transform.py` | OpenRVDAS transform |
| `logger/utils/seawater_density.py` | Pure Python calculation |
| `tests/test_water_density_transform.py` | Transform tests and optional TEOS-10 validation |
| `tools/derive_seawater_density.py` | Offline grid comparison against TEOS-10 |
| `requirements-dev.txt` | Optional gsw and NumPy dependencies |
| `examples/water_density.yaml` | Runnable stdin-to-stdout logger example |
| `examples/SVP.yaml` | Optional AML sensor format |
| `examples/svp_devices.yaml` | Optional sensor-to-field mapping |
| `LICENSE` | MIT license for the software contributions |
| `THIRD_PARTY_NOTICES.md` | Scientific source and OpenRVDAS attribution |
| `SOURCE_FILES.md` | Complete inventory of the original Hydra integration |

## Configuration

Place the `inkfish/` directory under `contrib/` in an OpenRVDAS checkout
and run from the repository root. The transform requires the {BaseModule}
API from recent OpenRVDAS. The core bundled with older `openrvdas_contrib`
checkouts predates that API. Validation used OpenRVDAS `dev` at commit
`fa9ca358fc70006fdfed6a05ab7ed75d0fc21494`.

Add the transform after parsing the sensor's input into a {DASRecord}:

```yaml
transforms:
  - class: WaterDensityTransform
    module: contrib.inkfish.seawater_density.logger.transforms.water_density_transform
    kwargs:
      sound_speed_field: SVP_SoundSpeed
      temp_field: SVP_WaterTemp
      density_name: SVP_WaterDensity
      data_id: water_density
      update_on_fields: [SVP_SoundSpeed]
      max_field_age:
        SVP_SoundSpeed: 5
        SVP_WaterTemp: 5
      metadata_interval: 10
```

The three field-name arguments are required. Input values may arrive
together or in separate timestamped records. The transform caches the
latest values, ignores older updates to each field, and emits a list of
derived {DASRecord} objects for supported record inputs. It also accepts
record dictionaries and the field dictionary format returned by {CachedDataReader}.

`update_on_fields` selects which of the two configured input fields trigger
output. Unrelated field names cannot trigger output. When unset or empty,
each processed record can emit output once both cached values are usable,
even if that record does not update either input.

`max_field_age` sets optional per-field limits in seconds, measured against
the incoming record timestamp. Unset or zero limits disable the age check.
Output is suppressed when an input is missing, cannot be converted with
`float()`, or exceeds an enabled age limit. Numeric strings are accepted.
Older field updates are ignored, but their records can still cause output
from cached values when `update_on_fields` is empty.

`data_id` labels the output record. `metadata_interval` attaches field
descriptions and units to the next successful output after the wall-clock
interval has elapsed. Unset or zero disables metadata. Both arguments
default to unset.

To try the AML example without network services:

```sh
printf '%s\n' 'svp 2026-06-03T00:00:00Z,1549.480,30.920' |
  python3 -m logger.listener.listen --config_file contrib/inkfish/seawater_density/examples/water_density.yaml
```

The output is a comma-separated timestamp and density of approximately
**1022.947 kg/m³**. In an existing parsed-data pipeline, the example sensor
definitions are optional: configure the transform with your own field
names and choose the usual OpenRVDAS writers.

## Validation and limits

Run the tests from the repository root:

```sh
python3 -m unittest discover -s contrib/inkfish/seawater_density/tests -v
```

The TEOS-10 comparison is skipped if the optional dependencies are absent.
To include it and run the offline report:

```sh
python3 -m pip install -r contrib/inkfish/seawater_density/requirements-dev.txt
python3 -m unittest discover -s contrib/inkfish/seawater_density/tests -v
python3 -m contrib.inkfish.seawater_density.tools.derive_seawater_density
```

The validation grid covers 0–40 °C and practical salinity 0–40 at P=0,
using reference salinity `SP * 35.16504 / 35`. The operating-regime test
covers 0–35 °C and practical salinity 30–40, and requires RMS error below
0.02 kg/m³ and maximum absolute error below 0.07 kg/m³ relative to GSW.
These are numerical comparisons against TEOS-10, not sensor accuracy
guarantees or validation at depth.

Validation with gsw 3.6.23 and NumPy 2.5.3 produced a full-grid RMS error
of 0.014631 kg/m³ (maximum 0.168692) and operating-regime RMS error of
0.012759 kg/m³ (maximum 0.055859) on the offline tool's 6,561-point grid.

The helper's `in_valid_range()` checks 0–40 °C and 1400–1570 m/s independently;
it does not establish physical salinity or validity of their combination.
The transform does not call it or enforce range or finite-number checks.
NaN values can propagate to output, and sufficiently large inputs can overflow.
Apply appropriate input quality controls in the surrounding logger.

## License

Original code and documentation contributed by Inkfish LLC. are provided
under the [MIT license](LICENSE). [THIRD_PARTY_NOTICES.md](THIRD_PARTY_NOTICES.md)
contains David Pablo Cohn's copyright and full MIT terms for the adapted
OpenRVDAS portions, along with the paper's CC BY 4.0 attribution.
Preserve both files when redistributing this contribution.
