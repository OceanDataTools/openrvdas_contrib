#!/usr/bin/env python3

import logging
import sys

sys.path.append('.')

from logger.utils import formats
from logger.utils.das_record import DASRecord
from logger.transforms.transform import Transform

################################################################################
#
class MaxMinTransform(Transform):
  """Transform that returns None unless values in passed DASRecord or
  dict are greater than/less than the largest/smallest values seen for
  their respective variables. Otherwise returns dict of colon-suffixed
  field names that have new max or min values. E.g.:

  max_min = MaxMinTransform()
  max_min.transform({'f1': 1, 'f2': 1.5}) -> {'f1:max':1, 'f1:min':1,
                                              'f2:max':1.5, 'f2:min':1.5}
  max_min.transform({'f1': 1, 'f2': 1.5}) -> {}
  max_min.transform({'f1': 1.1, 'f2': 1.4}) -> {'f1:max':1.1, 'f2:min':1.4,}

  Note: ignores fields that are not bool, int or float.
  """
  def __init__(self):
    """
    """
    super().__init__(input_format=formats.Python_Record,
                     output_format=formats.Text)
    self.max = {}
    self.min = {}

  ############################
  def transform(self, record):
    """Does record exceed any previously-observed bounds?"""
    if not record:
      return None

    if type(record) is DASRecord:
      fields = record.fields
    elif type(record) is dict:
      fields = record
    else:
      logging.warning('Input to MaxMinTransform must be either '
                      'DASRecord or dict. Received type "%s"', type(record))
      return None

    new_limits = {}
    
    for field, value in fields.items():
      # Max and Min only make sense for int, float and bool
      if not type(value) in [int, float, bool]:
        continue
      
      if not field in self.max or value > self.max[field]:
        self.max[field] = value
        new_limits[field + ':max'] = value
      if not field in self.min or value < self.min[field]:
        self.min[field] = value
        new_limits[field + ':min'] = value

    if not new_limits:
      return None

    if type(record) is DASRecord:
      if record.data_id:
        data_id = record.data_id + '_limits' if record.data_id else 'limits'
      return DASRecord(data_id=data_id,
                       message_type=record.message_type,
                       timestamp=record.timestamp,
                       fields=new_limits)

    return new_limits