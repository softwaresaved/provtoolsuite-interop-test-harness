"""Test classes for prov.interop.harness classes.
"""
# Copyright (c) 2015 University of Southampton
#
# Permission is hereby granted, free of charge, to any person
# obtaining a copy of this software and associated documentation files
# (the "Software"), to deal in the Software without restriction,
# including without limitation the rights to use, copy, modify, merge,
# publish, distribute, sublicense, and/or sell copies of the Software,
# and to permit persons to whom the Software is furnished to do so,
# subject to the following conditions: 
#
# The above copyright notice and this permission notice shall be
# included in all copies or substantial portions of the Software. 
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND,
# EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF
# MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND
# NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS
# BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN
# ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN
# CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.  

import inspect
import os
import shutil
import tempfile
import unittest
import yaml

from prov.interop import standards
from prov.interop.component import CommandLineComponent
from prov.interop.component import ConfigurableComponent
from prov.interop.component import ConfigError
from prov.interop.converter import Converter
from prov.interop.harness import HarnessConfiguration
from prov.interop.provpy.comparator import ProvPyComparator
import prov.interop.harness as harness

def get_sample_configuration():
  """Return sample HarnessConfiguration-compliant dict.

  :returns: configuration
  :rtype: dict
  """
  config = {}
  config[HarnessConfiguration.TEST_CASES] = "test-cases"
  comparators = {}
  comparator = {}
  comparator[ProvPyComparator.EXECUTABLE] = "python"
  script = "prov-compare"
  comparator[ProvPyComparator.ARGUMENTS] = [
    script,
    "-f", ProvPyComparator.FORMAT1,
    "-F", ProvPyComparator.FORMAT2,
    ProvPyComparator.FILE1,
    ProvPyComparator.FILE2]
  comparator[ProvPyComparator.FORMATS] = [standards.PROVX, standards.JSON]
  comparator[HarnessConfiguration.CLASS] = \
      ProvPyComparator.__module__ + "." + ProvPyComparator.__name__
  comparators[ProvPyComparator.__name__] = comparator
  config[HarnessConfiguration.COMPARATORS] = comparators
  return config

class HarnessConfigurationTestCase(unittest.TestCase):

  def setUp(self):
    self.harness = HarnessConfiguration()
    self.config = get_sample_configuration()
    
  def test_init(self):
    self.assertEqual({}, self.harness.configuration)
    self.assertEqual("", self.harness.test_cases)
    self.assertEqual({}, self.harness.comparators)
    self.assertEqual({}, self.harness.format_comparators)

  def test_configure(self):
    self.harness.configure(self.config)
    self.assertEqual(self.config, self.harness.configuration)
    self.assertEqual("test-cases", self.harness.test_cases)
    # Check comparators
    comparators = self.harness.comparators
    self.assertEqual(1, len(comparators))
    self.assertTrue(ProvPyComparator.__name__ in comparators)
    comparator = comparators[ProvPyComparator.__name__]
    self.assertIsInstance(comparator, ProvPyComparator)
    # Check comparators indexed by format
    comparators = self.harness.format_comparators
    self.assertEqual(2, len(comparators))
    for format in [standards.PROVX, standards.JSON]:
      self.assertTrue(format in comparators)
      format_comparator = comparators[format]
      self.assertIsInstance(format_comparator, ProvPyComparator)
      self.assertEqual(comparator, format_comparator)

  def test_configure_no_test_cases(self):
    del self.config[HarnessConfiguration.TEST_CASES]
    with self.assertRaises(ConfigError):
      self.harness.configure(self.config)

  def test_configure_no_comparators(self):
    del self.config[HarnessConfiguration.COMPARATORS]
    with self.assertRaises(ConfigError):
      self.harness.configure(self.config)

  def test_configure_zero_comparators(self):
    self.config[HarnessConfiguration.COMPARATORS] = {}
    with self.assertRaises(ConfigError):
      self.harness.configure(self.config)

  def test_configure_comparator_config_error(self):
    del self.config[HarnessConfiguration.COMPARATORS][
      ProvPyComparator.__name__][ProvPyComparator.EXECUTABLE]
    with self.assertRaises(ConfigError):
      self.harness.configure(self.config)

class HarnessConfigurationModuleTestCase(unittest.TestCase):

  def setUp(self):
    self.config = get_sample_configuration()
    (_, self.yaml) = tempfile.mkstemp(suffix=".yaml")
    with open(self.yaml, 'w') as yaml_file:
      yaml_file.write(yaml.dump(self.config, default_flow_style=False))

  def tearDown(self):
    if self.yaml != None and os.path.isfile(self.yaml):
      os.remove(self.yaml)

  def test_configure_harness_from_file(self):
    harness.configure_harness_from_file(self.yaml)

  def test_configure_harness_from_env(self):
    os.environ[harness.CONFIGURATION_FILE] = self.yaml
    harness.configure_harness_from_file()

  def test_configure_harness_from_default(self):
    default_file = os.path.join(os.getcwd(),
                                harness.DEFAULT_CONFIGURATION_FILE)
    shutil.move(self.yaml, default_file)
    self.yaml = default_file
    harness.configure_harness_from_file()

  def test_configure_harness_from_file_missing_file(self):
    with self.assertRaises(IOError):
      harness.configure_harness_from_file("nosuchfile.yaml")

  def test_configure_harness_from_file_non_yaml_file(self):
    with open(self.yaml, 'w') as yaml_file:
      yaml_file.write("This is an invalid YAML file")
      with self.assertRaises(ConfigError):
        harness.configure_harness_from_file(self.yaml)