# Original Hydra files

Paths below are relative to the original `odt-hyd` workspace. The original
files remain unchanged; this contribution contains portable copies and
examples extracted from that deployment.

| Original file | Role | Contribution file |
| --- | --- | --- |
| `openrvdas/local/modules/transforms/water_density_transform.py` | OpenRVDAS transform, input caching, metadata | `logger/transforms/water_density_transform.py` |
| `openrvdas/local/modules/utils/seawater_density.py` | Pure Python density equation | `logger/utils/seawater_density.py` |
| `openrvdas/local/tests/test_water_density_transform.py` | Helper and transform tests; optional TEOS-10 grid comparison | `tests/test_water_density_transform.py` |
| `openrvdas/local/tests/requirements-dev.txt` | Optional gsw and NumPy dependencies | `requirements-dev.txt` |
| `openrvdas/local/tools/derive_seawater_density.py` | Offline validation and exploratory refitting | `tools/derive_seawater_density.py`, limited to runtime validation |
| `openrvdas/local/devices/SVP.yaml` | AML sound-speed/temperature record format and units | `examples/SVP.yaml` |
| `openrvdas/local/hyd_devices.yaml` | Maps the `svp` instrument to `SVP_SoundSpeed` and `SVP_WaterTemp` | `examples/svp_devices.yaml`, relevant mapping only |
| `openrvdas/local/hyd_logger_config.yaml` | SVP ingestion; density logger; cache, InfluxDB, file and UDP outputs; operating modes | `examples/water_density.yaml`, portable stdin/stdout example |
| `openrvdas/local/templates/udp_logger_templates.yaml` | Shared raw SVP UDP ingestion, timestamping, logging and forwarding | Uses standard OpenRVDAS modules; deployment template not copied |
| `openrvdas/local/templates/parser_templates.yaml` | Shared parsing into cached SVP fields | Uses standard OpenRVDAS modules; deployment template not copied |

The density transform directly depends on OpenRVDAS's
`logger/transforms/derived_data_transform.py` and `logger/utils/das_record.py`,
and transitively on the core {Transform} class and its record utilities.
These are supplied by OpenRVDAS, not vendored in this contribution.

The Hydra deployment additionally uses {UDPReader}, {SplitTransform},
{StripTransform}, {TimestampTransform}, {PrefixTransform}, {ParseTransform},
{CachedDataReader}, {CachedDataWriter}, {InfluxDBWriter}, {ComposedWriter},
{FormatTransform}, {LogfileWriter}, and {UDPWriter}. They belong to the
surrounding logging pipeline, not the density calculation. The contribution's
example uses {TextFileReader}, {ParseTransform}, {FormatTransform}, and
{TextFileWriter} to demonstrate the transform without external services.

Package imports replace Hydra-specific path setup, and the transform
requires the {BaseModule} API from recent OpenRVDAS. Three helper debug
prints are removed; the offline tool validates the retained Table 6
equation without exploratory refitting;
tests fail on broken OpenRVDAS imports; and attribution, licensing,
documentation, and generic examples are added. Runtime coefficients are unchanged.
