"""Test classes for prov.interop.component classes.
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

import os
import shutil
import tempfile
import unittest
import yaml

from prov.interop.component import CommandLineComponent
from prov.interop.component import ConfigurableComponent
from prov.interop.component import ConfigError
from prov.interop.component import RestComponent
import prov.interop.component as component

class ConfigurableComponentTestCase(unittest.TestCase):

  def test_configure_empty(self):
    comp = ConfigurableComponent()
    comp.configure({})
    self.assertTrue(True)

  def test_configure_non_empty(self):
    comp = ConfigurableComponent()
    comp.configure({"a":"b", "c":"d", "e":["f", "g", 123]})
    self.assertTrue(True)

  def test_configure_non_dict_error(self):
    comp = ConfigurableComponent()
    with self.assertRaises(ConfigError):
      comp.configure(123)

  def test_check_configuration(self):
    ConfigurableComponent.check_configuration(
      {"a":"b", "c":"d", "e":"f"}, ["a", "c", "e"])
    self.assertTrue(True)

  def test_check_configuration_error(self):
    with self.assertRaises(ConfigError):
      ConfigurableComponent.check_configuration(
        {"a":"b", "c":"d", "e":"f"}, ["a", "c", "expectfail"])


class CommandLineComponentTestCase(unittest.TestCase):

  def test_init(self):
    command_line = CommandLineComponent()
    self.assertEquals("", command_line.executable)
    self.assertEquals([], command_line.arguments)

  def test_configure(self):
    command_line = CommandLineComponent()
    command_line.configure(
      {CommandLineComponent.EXECUTABLE: "b", 
       CommandLineComponent.ARGUMENTS: ["c", 1]})
    self.assertEquals("b", command_line.executable)
    self.assertEquals(["c", 1], command_line.arguments)

  def test_configure_non_dict_error(self):
    command_line = CommandLineComponent()
    with self.assertRaises(ConfigError):
      command_line.configure(123)

  def test_configure_no_executable(self):
    command_line = CommandLineComponent()
    with self.assertRaises(ConfigError):
      command_line.configure({CommandLineComponent.ARGUMENTS: ["c", 1]})

  def test_configure_no_arguments(self):
    command_line = CommandLineComponent()
    with self.assertRaises(ConfigError):
      command_line.configure({CommandLineComponent.EXECUTABLE: "b"})


class RestComponentTestCase(unittest.TestCase):

  def test_init(self):
    rest = RestComponent()
    self.assertEquals("", rest.url)

  def test_configure(self):
    rest = RestComponent()
    rest.configure({RestComponent.URL: "a"})
    self.assertEquals("a", rest.url)

  def test_configure_non_dict_error(self):
    rest = RestComponent()
    with self.assertRaises(ConfigError):
      rest.configure(123)

  def test_configure_no_url(self):
    rest = RestComponent()
    with self.assertRaises(ConfigError):
      rest.configure({})


class LoadConfigurationTestCase(unittest.TestCase):

  def setUp(self):
    self.config={"counter": 12345}
    (_, self.yaml) = tempfile.mkstemp(suffix=".yaml")
    with open(self.yaml, 'w') as yaml_file:
      yaml_file.write(yaml.dump(self.config, default_flow_style=False))
    self.env_var = "PROV_LOAD_CONFIG"
    self.default_file = os.path.join(os.getcwd(), "test_component.yaml")

  def tearDown(self):
    if self.yaml != None and os.path.isfile(self.yaml):
      os.remove(self.yaml)

  def test_load_configuration_from_file(self):
    config = component.load_configuration(self.env_var,
                                          self.default_file,
                                          self.yaml)
    self.assertEqual(12345, config["counter"])

  def test_load_configuration_from_env(self):
    os.environ[self.env_var] = self.yaml
    config = component.load_configuration(self.env_var,
                                          self.default_file,
                                          self.yaml)
    self.assertEqual(12345, config["counter"])

  def test_load_configuration_from_default(self):
    shutil.move(self.yaml, self.default_file)
    self.yaml = self.default_file
    config = component.load_configuration(self.env_var,
                                          self.default_file)
    self.assertEqual(12345, config["counter"])

  def test_load_configuration_from_file_missing_file(self):
    with self.assertRaises(IOError):
      config = component.load_configuration(self.env_var,
                                            self.default_file,
                                            "nosuchfile.yaml")
      
  def test_load_configuration_from_file_non_yaml_file(self):
    with open(self.yaml, 'w') as yaml_file:
      yaml_file.write("This is an invalid YAML file")
    with self.assertRaises(ConfigError):
      config = component.load_configuration(self.env_var,
                                            self.default_file,
                                            self.yaml)
