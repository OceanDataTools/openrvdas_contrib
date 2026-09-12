#!/usr/bin/env python3
"""Cache sound speed and temperature and emit surface-density DASRecords.

Adapted from logger/transforms/true_winds_transform.py.
See ../../THIRD_PARTY_NOTICES.md for attribution.
"""
import logging
import time
from typing import Union

from logger.utils.das_record import DASRecord, to_das_record_list
from logger.transforms.derived_data_transform import DerivedDataTransform
from contrib.inkfish.seawater_density.logger.utils.seawater_density import surface_density


class WaterDensityTransform(DerivedDataTransform):
    """Compute surface seawater density (kg/m^3) from sound speed and temperature."""

    def __init__(self,
                 sound_speed_field,
                 temp_field,
                 density_name,
                 update_on_fields=None,
                 max_field_age=None,
                 data_id=None,
                 metadata_interval=None,
                 **kwargs):
        """Configure input fields, output naming, and optional emission limits.

        sound_speed_field: Sound-speed input field (m/s).
        temp_field: In-situ temperature input field (deg C).
        density_name: Density output field (kg/m^3).
        update_on_fields: Input fields that trigger output; empty means every record.
        max_field_age: Per-input age limits in seconds; unset or zero disables a limit.
        data_id: Optional output record identifier.
        metadata_interval: Wall-clock seconds between metadata; unset or zero disables it.
        kwargs: Options passed to DerivedDataTransform.
        """
        super().__init__(**kwargs)

        self.sound_speed_field = sound_speed_field
        self.temp_field = temp_field
        self.density_name = density_name

        self.update_on_fields = update_on_fields or []
        self.max_field_age = max_field_age or {}

        self.data_id = data_id
        self.metadata_interval = metadata_interval
        self.last_metadata_send = 0

        self.sound_speed_val = None
        self.temp_val = None
        self.sound_speed_val_time = 0
        self.temp_val_time = 0

    def fields(self):
        """Input fields this transform consumes."""
        return [self.sound_speed_field, self.temp_field]

    def _metadata(self):
        """Metadata for the derived density field."""
        return {
            self.density_name: {
                'description': 'Derived surface seawater density from %s and %s'
                % (self.sound_speed_field, self.temp_field),
                'units': 'kg/m^3',
                'device': 'WaterDensityTransform',
                'device_type': 'DerivedWaterDensityTransform',
                'device_type_field': self.density_name,
            }
        }

    def transform(self, record: Union[dict, DASRecord]):
        """Return derived records for valid inputs, or delegate unsupported types."""
        if not self.can_process_record(record):
            return self.digest_record(record)

        results = []
        for das_record in to_das_record_list(record):
            # An empty trigger list permits output on every record.
            update = not self.update_on_fields

            timestamp = das_record.timestamp
            if not timestamp:
                logging.info('DASRecord is missing timestamp - skipping')
                continue

            fields = das_record.fields
            if self.sound_speed_field in fields:
                if timestamp >= self.sound_speed_val_time:
                    self.sound_speed_val = fields.get(self.sound_speed_field)
                    self.sound_speed_val_time = timestamp
                    if self.sound_speed_field in self.update_on_fields:
                        update = True

            if self.temp_field in fields:
                if timestamp >= self.temp_val_time:
                    self.temp_val = fields.get(self.temp_field)
                    self.temp_val_time = timestamp
                    if self.temp_field in self.update_on_fields:
                        update = True

            if self._values_too_old(timestamp):
                continue

            if not update:
                logging.debug('No update needed')
                continue

            density = surface_density(self.temp_val, self.sound_speed_val)
            if density is None:
                logging.info('Got invalid water density from T=%s, c=%s',
                             self.temp_val, self.sound_speed_val)
                continue

            density_fields = {self.density_name: density}

            now = time.time()
            if self.metadata_interval and \
               now - self.metadata_interval > self.last_metadata_send:
                metadata = {'fields': self._metadata()}
                self.last_metadata_send = now
            else:
                metadata = None

            results.append(DASRecord(timestamp=timestamp, fields=density_fields,
                                     metadata=metadata, data_id=self.data_id))

        logging.debug('Sending %d water density results.', len(results))
        return results

    def _values_too_old(self, timestamp):
        """Check for missing inputs or ages exceeding enabled limits."""
        if None in (self.sound_speed_val, self.temp_val):
            logging.debug('Not all required values for water density are present')
            return True

        for field, val_time in ((self.sound_speed_field, self.sound_speed_val_time),
                                (self.temp_field, self.temp_val_time)):
            max_age = self.max_field_age.get(field)
            if max_age and timestamp - val_time > max_age:
                logging.debug('%s too old - max age %g, age %g',
                              field, max_age, timestamp - val_time)
                return True
        return False
