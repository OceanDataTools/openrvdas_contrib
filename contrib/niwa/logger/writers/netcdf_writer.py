#!/usr/bin/env python3

import json
import logging
import numbers
import re
import sys

# requires pip install netCDF4
from netCDF4 import Dataset

from os.path import dirname, realpath
sys.path.append(dirname(dirname(dirname(realpath(__file__)))))
from logger.utils.das_record import DASRecord  # noqa: E402
from logger.utils import timestamp  # noqa: E402
from logger.writers.writer import Writer  # noqa: E402
from logger.writers.file_writer import FileWriter  # noqa: E402


class NetCDFWriter(Writer):
    """Write to netCDF files for the specified filebase, with datestamp appended. If filebase
    is a <regex>:<filebase> dict, write records to every filebase whose
    regex appears in the record.
    """
    # Based on the LogfileWriter
    def __init__(self, filebase=None, flush=True,
                 time_format=timestamp.TIME_FORMAT,
                 date_format=timestamp.DATE_FORMAT,
                 split_char=' ', suffix='', header=None,
                 header_file=None, rollover_hourly=False,
                 quiet=False):
        """Write timestamped records to a filebase. The filebase will
        have the current date appended, in keeping with R2R format
        recommendations (http://www.rvdata.us/operators/directory). When the
        timestamped date on records rolls over to next day, create a new file
        with the new date suffix.

        If filebase is a dict of <string>:<filebase> pairs, The writer will
        attempt to match a <string> in the dict to each record it receives.
        It will write the record to the filebase corresponding to the first
        string it matches (Note that the order of comparison is not
        guaranteed!). If no strings match, the record will be written to the
        standalone filebase provided.

        Four formats of records can be written by a NetCDFWriter:
            1. A string prefixed by a timestamp
            2. A DASRecord
            3. A dict that has a 'timestamp' key
            4. A list of any of the above

        ```
        filebase        A filebase string to write to or a dict mapping
                        <string>:<filebase>.

        flush           If True (default), flush after every write() call

        date_fomat      A strftime-compatible string, such as '%Y-%m-%d';
                        defaults to whatever's defined in
                        utils.timestamps.DATE_FORMAT.

        split_char      Delimiter between timestamp and rest of message

        suffix          string to apply to the end of the log filename

        header          Add the specified header string to each file.

        header_file     Add the content of the specified file to each file.

        rollover_hourly Set files to truncate by hour.  By default files will
                        truncate by day

        quiet           If True, don't complain if a record doesn't match
                        any mapped prefix
        ```
        """
        self.filebase = filebase
        self.flush = flush
        self.time_format = time_format
        self.date_format = date_format
        self.split_char = split_char
        self.suffix = suffix
        self.header = header
        self.header_file = header_file
        self.rollover_hourly = rollover_hourly
        self.quiet = quiet

        # If our filebase is a dict, we're going to be doing our
        # fancy pattern->filebase mapping.
        self.do_filebase_mapping = isinstance(self.filebase, dict)

        if self.do_filebase_mapping:
            # Do our matches faster by precompiling
            self.compiled_filebase_map = {
                pattern: re.compile(pattern) for pattern in self.filebase
            }
        self.current_filename = {}
        self.writer = {}

    ############################
    def write(self, record):
        if record is None:
            return
        if record == '':
            return

        # If we've got a list, hope it's a list of records. Recurse,
        # calling write() on each of the list elements in order.
        if isinstance(record, list):
            for single_record in record:
                self.write(single_record)
            return

        # Look for the timestamp
        if isinstance(record, DASRecord):  # If DASRecord or structured dict,
            ts = record.timestamp

        elif isinstance(record, dict):
            ts = record.get('timestamp', None)
            if ts is None:
                if not self.quiet:
                    logging.error('NetCDFWriter.write() - bad timestamp: "%s"', record)
                return

        elif isinstance(record, str):  # If str, it better begin with time string
            #TODO: LW - make this work
            try:  # Try to extract timestamp from record
                time_str = record.split(self.split_char)[0]
                ts = timestamp.timestamp(time_str, time_format=self.time_format)
            except ValueError:
                if not self.quiet:
                    logging.error('NetCDFWriter.write() - bad timestamp: "%s"', record)
                    return
        else:
            if not self.quiet:
                logging.error(f'NetCDFWriter received badly formatted record. Must be DASRecord, '
                              f'dict, or timestamp-prefixed string. Received: "{record}"')
            return

        # Now parse ts into hour and date strings
        hr_str = self.rollover_hourly and \
            timestamp.date_str(ts, date_format='_%H00') or ""
        date_str = timestamp.date_str(ts, date_format=self.date_format)
        time_str = date_str + hr_str + self.suffix
        logging.debug('NetCDFWriter time_str: %s', time_str)

        # Figure out where we're going to write
        if self.do_filebase_mapping:
            matched_patterns = [self.write_if_match(record, pattern, time_str)
                                for pattern in self.filebase]
            if True not in matched_patterns:
                if not self.quiet:
                    logging.warning(f'No patterns matched in NetCDFWriter '
                                    f'options for record "{record}"')
        else:
            pattern = 'fixed'  # just an arbitrary fixed pattern
            filename = self.filebase + '-' + time_str
            self.write_filename(record, pattern, filename)

    ############################
    def write_if_match(self, record, pattern, time_str):
        """If the record matches the pattern, write to the matching filebase."""
        if isinstance(record, DASRecord):  # If DASRecord or structured dict,
            if record.data_id != pattern:
                return None

        elif isinstance(record, dict):
            if record.get("data_id") != pattern:
                return None

        filebase = self.filebase.get(pattern)
        if filebase is None:
            logging.error(f'System error: found no filebase matching pattern "{pattern}"!')
            return None

        filename = filebase + '-' + time_str
        self.write_filename(record, pattern, filename)
        return True

    ############################
    def write_filename(self, record, pattern, filename):
        """Write record to filename. If it's the first time we're writing to
        this filename, create the appropriate FileWriter and insert it into
        the map for the relevant pattern."""

        # Are we currently writing to this file? If not, open/create it.
        if not filename == self.current_filename.get(pattern, None):
            
            logging.info('NetCDFWriter opening new file: %s', filename)
            self.current_filename[pattern] = filename
            self.writer[pattern] = Dataset(f"{filename}.nc", "w", format="NETCDF4")
        
        # open in appending mode
        self.writer[pattern] = Dataset(f"{filename}.nc", "a", format="NETCDF4")
        # Now, if our logic is correct, should *always* have a matching_writer
        matching_writer = self.writer.get(pattern)
        self.write_data(matching_writer, record)


    ###
    # NetCDF object looks like:
    #
    # {
    #   "dimensions": {
    #                   "time": [xxxxxx, yyyyyy, zzzzzz]
    #                 },
    #   "variables": {
    #                   "value_1": [1, 2, 3, 4],
    #                   "value_2": [2.2, 2.2, 3.2, 4.2]
    #                }
    # }
    #
    #
    ###
    def write_data(self, writer, record):

        dimensions = writer.dimensions
        variables = writer.variables
        
        if not dimensions.get("time"):
            # needs to be a time dimension before writing any values
            writer.createDimension("time")
            # f8 = 64 bit floating point - https://unidata.github.io/netcdf4-python/#variables-in-a-netcdf-file
            writer.createVariable("time", "f8", "time")

        time_var = variables.get("time")

        if isinstance(record, DASRecord):  # If DASRecord or structured dict,
            time_var[len(time_var)] = record.timestamp
            fields = record.fields
            field_keys = fields.keys()

        elif isinstance(record, dict):
            time_var[len(time_var)] = record.get("timestamp")
            fields = record.get("fields")
            field_keys = fields.keys()

        else:
            logging.error(f"Got unsupported record type: {type(record)}")


        for field in field_keys:
            existing_variable = variables.get(field)
            value = fields[field]

            if not existing_variable:
                writer.createDimension(field)
                if isinstance(value, numbers.Number):
                    # 64 bit floating point
                    existing_variable = writer.createVariable(field, "f8", field)
                else:
                    # a variable length string field to hold any data type
                    # using the "time" dimension
                    existing_variable = writer.createVariable(field, str, field)

            existing_values = len(existing_variable)    
        
            if isinstance(existing_variable.datatype, numbers.Number):
                existing_variable[existing_values] = value
            else:
                existing_variable[existing_values] = str(value)

        writer.close()