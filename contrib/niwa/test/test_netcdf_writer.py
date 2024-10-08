#!/usr/bin/env python3

import logging
import sys
import tempfile
import unittest

from netCDF4 import Dataset

from logger.utils import timestamp

sys.path.append('.')
from logger.utils.das_record import DASRecord  # noqa: E402
from contrib.niwa.logger.writers.netcdf_writer import NetCDFWriter  # noqa: E402

SAMPLE_DATA_DICT = [
    {'timestamp': 1691410658.0, 'fields': {'F1': 4.26, 'F2': 121736.82}},
    {'timestamp': 1691410659.0, 'fields': {'F1': 5.26, 'F2': 121735.82}},
    {'timestamp': 1691410660.0, 'fields': {'F1': 6.26, 'F2': 121734.82}},
    {'timestamp': 1691410661.0, 'fields': {'F1': 7.26, 'F2': 121733.82}},
]
SAMPLE_DATA_DICT_STR = """{"timestamp": 1691410658.0, "fields": {"F1": 4.26, "F2": 121736.82}}
{"timestamp": 1691410659.0, "fields": {"F1": 5.26, "F2": 121735.82}}
{"timestamp": 1691410660.0, "fields": {"F1": 6.26, "F2": 121734.82}}
{"timestamp": 1691410661.0, "fields": {"F1": 7.26, "F2": 121733.82}}
"""

# flake8: noqa: E501
SAMPLE_DATA_DASRECORD_STR = """{"data_id": "test", "message_type": null, "timestamp": 1691410658.0, "fields": {"F1": 4.26, "F2": 121736.82}, "metadata": {}}
{"data_id": "test", "message_type": null, "timestamp": 1691410659.0, "fields": {"F1": 5.26, "F2": 121735.82}, "metadata": {}}
{"data_id": "test", "message_type": null, "timestamp": 1691410660.0, "fields": {"F1": 6.26, "F2": 121734.82}, "metadata": {}}
{"data_id": "test", "message_type": null, "timestamp": 1691410661.0, "fields": {"F1": 7.26, "F2": 121733.82}, "metadata": {}}
"""

SAMPLE_DATA_DICT_MONTHLY = [
    {'timestamp': 1691410658.0, 'fields': {'F1': 4.26, 'F2': 131736.82}},
    {'timestamp': 1694413659.0, 'fields': {'F1': 5.26, 'F2': 131735.82}},
    {'timestamp': 1696417660.0, 'fields': {'F1': 6.26, 'F2': 131734.82}},
    {'timestamp': 1699420661.0, 'fields': {'F1': 7.26, 'F2': 131733.82}},
]

SAMPLE_DATA_DICT_HOURLY = [
    {'timestamp': 1691410658.0, 'fields': {'F1': 4.26, 'F2': 141736.82}},
    {'timestamp': 1691413659.0, 'fields': {'F1': 5.26, 'F2': 141735.82}},
    {'timestamp': 1691417660.0, 'fields': {'F1': 6.26, 'F2': 141734.82}},
    {'timestamp': 1691420661.0, 'fields': {'F1': 7.26, 'F2': 141733.82}},
]


class TestNetCDFWriter(unittest.TestCase):

    def open_netcdf_file(self, filepath):
        return Dataset(f"{filepath}", "r", format="NETCDF4")


    ############################
    def test_write_dict(self):
        with tempfile.TemporaryDirectory() as tmpdirname:

            filebase = tmpdirname + '/logfile'

            writer = NetCDFWriter(filebase)
            writer.write(SAMPLE_DATA_DICT)

            with self.open_netcdf_file(filebase + '-2023-08-07.nc') as outfile:
                expected_dimensions = ["time", "F1", "F2",]
                expected_variables = ["time", "F1", "F2",]

                self.assertEqual(list(outfile.dimensions.keys()), expected_dimensions)
                self.assertEqual(list(outfile.variables.keys()), expected_variables)
                
                record_count = 0
                for record in SAMPLE_DATA_DICT:
                    self.assertEqual(record["timestamp"], outfile.variables.get("time")[record_count])
                    self.assertEqual(record["fields"]["F1"], outfile.variables.get("F1")[record_count])
                    self.assertEqual(record["fields"]["F2"], outfile.variables.get("F2")[record_count])

                    record_count+=1

    ############################
    def test_write_das_record(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            filebase = tmpdirname + '/logfile'

            writer = NetCDFWriter(filebase)
            for record in SAMPLE_DATA_DICT:
                writer.write(DASRecord(timestamp=record['timestamp'],
                                       data_id='test',
                                       fields=record['fields']))

            with self.open_netcdf_file(filebase + '-2023-08-07.nc') as outfile:
                expected_dimensions = ["time", "F1", "F2",]
                expected_variables = ["time", "F1", "F2",]

                self.assertEqual(list(outfile.dimensions.keys()), expected_dimensions)
                self.assertEqual(list(outfile.variables.keys()), expected_variables)
                
                record_count = 0
                for record in SAMPLE_DATA_DICT:
                    self.assertEqual(record["timestamp"], outfile.variables.get("time")[record_count])
                    self.assertEqual(record["fields"]["F1"], outfile.variables.get("F1")[record_count])
                    self.assertEqual(record["fields"]["F2"], outfile.variables.get("F2")[record_count])

                    record_count+=1

                

    ############################
    def test_map_write(self):
        with tempfile.TemporaryDirectory() as tmpdirname:
            filebase = {
                'AAA': tmpdirname + '/logfile_A',
                'BBB': tmpdirname + '/logfile_B',
                'CCC': tmpdirname + '/logfile_C',
            }

            expected_values = {
                'AAA': [SAMPLE_DATA_DICT[0], SAMPLE_DATA_DICT[3],],
                'BBB': [SAMPLE_DATA_DICT[1],],
                'CCC': [SAMPLE_DATA_DICT[2],]
            }

            writer = NetCDFWriter(filebase=filebase)

            bad_line = 'there is no timestamp here'
            with self.assertLogs(logging.getLogger(), logging.ERROR) as cm:
                writer.write(bad_line)
            error = f'ERROR:root:NetCDFWriter.write() - bad timestamp: "{bad_line}"'
            self.assertEqual(cm.output, [error])

            writer.write(DASRecord(timestamp=SAMPLE_DATA_DICT[0]['timestamp'],
                                    data_id='AAA',
                                    fields=SAMPLE_DATA_DICT[0]['fields']))
            writer.write(DASRecord(timestamp=SAMPLE_DATA_DICT[1]['timestamp'],
                                    data_id='BBB',
                                    fields=SAMPLE_DATA_DICT[1]['fields']))
            writer.write(DASRecord(timestamp=SAMPLE_DATA_DICT[2]['timestamp'],
                                    data_id='CCC',
                                    fields=SAMPLE_DATA_DICT[2]['fields']))
            writer.write(DASRecord(timestamp=SAMPLE_DATA_DICT[3]['timestamp'],
                                    data_id='AAA',
                                    fields=SAMPLE_DATA_DICT[3]['fields']))


            for (data_id, filepath) in filebase.items():
                with self.open_netcdf_file(filepath + '-2023-08-07.nc') as outfile:
                    expected_dimensions = ["time", "F1", "F2",]
                    expected_variables = ["time", "F1", "F2",]

                    self.assertEqual(list(outfile.dimensions.keys()), expected_dimensions)
                    self.assertEqual(list(outfile.variables.keys()), expected_variables)
                    
                    expected_records = expected_values.get(data_id)

                    record_count = 0
                    for record in expected_records:
                        self.assertEqual(record["timestamp"], outfile.variables.get("time")[record_count])
                        self.assertEqual(record["fields"]["F1"], outfile.variables.get("F1")[record_count])
                        self.assertEqual(record["fields"]["F2"], outfile.variables.get("F2")[record_count])

                        record_count+=1


    def test_rollover_format_monthly(self):
         with tempfile.TemporaryDirectory() as tmpdirname:

            filebase = tmpdirname + '/logfile'

            writer = NetCDFWriter(filebase, rollover_format='%Y-%m')
            writer.write(SAMPLE_DATA_DICT_MONTHLY)

            record_count = 0
            for record in SAMPLE_DATA_DICT_MONTHLY:

                with self.open_netcdf_file(filebase + f'-2023-{str(8 +record_count).zfill(2)}.nc') as outfile:
                    expected_dimensions = ["time", "F1", "F2",]
                    expected_variables = ["time", "F1", "F2",]

                    self.assertEqual(list(outfile.dimensions.keys()), expected_dimensions)
                    self.assertEqual(list(outfile.variables.keys()), expected_variables)

                    self.assertEqual(record["timestamp"], outfile.variables.get("time")[0])
                    self.assertEqual(record["fields"]["F1"], outfile.variables.get("F1")[0])
                    self.assertEqual(record["fields"]["F2"], outfile.variables.get("F2")[0])

                record_count+=1


    def test_rollover_format_hourly(self):
         with tempfile.TemporaryDirectory() as tmpdirname:

            filebase = tmpdirname + '/logfile'

            writer = NetCDFWriter(filebase, rollover_format='%Y-%m-%d_%H00')
            writer.write(SAMPLE_DATA_DICT_HOURLY)

            record_count = 0
            for record in SAMPLE_DATA_DICT_HOURLY:

                with self.open_netcdf_file(filebase + f'-2023-08-07_1{2 +record_count}00.nc') as outfile:
                    expected_dimensions = ["time", "F1", "F2",]
                    expected_variables = ["time", "F1", "F2",]

                    self.assertEqual(list(outfile.dimensions.keys()), expected_dimensions)
                    self.assertEqual(list(outfile.variables.keys()), expected_variables)

                    self.assertEqual(record["timestamp"], outfile.variables.get("time")[0])
                    self.assertEqual(record["fields"]["F1"], outfile.variables.get("F1")[0])
                    self.assertEqual(record["fields"]["F2"], outfile.variables.get("F2")[0])

                record_count+=1


if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('-v', '--verbosity', dest='verbosity',
                        default=0, action='count',
                        help='Increase output verbosity')
    args = parser.parse_args()

    LOGGING_FORMAT = '%(asctime)-15s %(message)s'
    logging.basicConfig(format=LOGGING_FORMAT)

    LOG_LEVELS = {0: logging.WARNING, 1: logging.INFO, 2: logging.DEBUG}
    args.verbosity = min(args.verbosity, max(LOG_LEVELS))
    logging.getLogger().setLevel(LOG_LEVELS[args.verbosity])

    unittest.main(warnings='ignore')
