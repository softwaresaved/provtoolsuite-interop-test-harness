"""Interoperability test harness resources.
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
import yaml

from prov.interop import factory
from prov.interop.comparator import Comparator
from prov.interop.component import ConfigError
from prov.interop.component import ConfigurableComponent

class HarnessResources(ConfigurableComponent):
  """Interoperability test harness resources."""

  TEST_CASES = "test-cases"
  """string or unicode: configuration key for test cases directory"""
  COMPARATORS = "comparators"
  """string or unicode: configuration key list of comparators"""
  CLASS = "class"
  """string or unicode: configuration key for comparator class names"""

  def __init__(self):
    """Create harness resources.
    """
    super(HarnessResources, self).__init__()
    self._test_cases = ""
    self._comparators = {}
    self._format_comparators = {}

  @property
  def test_cases(self):
    """Get test cases directory

    :returns: directory name
    :rtype: list of str or unicode
    """
    return self._test_cases

  @property
  def comparators(self):
    """Get dictionary of comparators.

    :returns: comparators
    :rtype: dict from str or unicode to instances of
    :class:`~prov.interop.comparator.Comparator`
    """
    return self._comparators

  @property
  def format_comparators(self):
    """Gets dictionary of comparators keyed by formats.
    Formats are as defined in ``prov.interop.standards``.

    :returns: comparators
    :rtype: dict from str or unicode to instances of 
      :class:`~prov.interop.comparator.Comparator`
    """
    return self._format_comparators

  def register_comparators(self, comparators):
    """Populate dictionaries mapping both comparator names and formats 
    to instances of :class:`~prov.interop.comparator.Comparator`.

    ``comparators`` must be a dictionary with entries of form::

        Comparator nick-name
          class: ... class name...
          ...class-specific configuration...

    For example::

        ProvPyComparator: 
          class: prov.interop.provpy.comparator.ProvPyComparator
          executable: python
          arguments: [/home/user/prov/scripts/prov-compare, -f, FORMAT1, -F, FORMAT2, FILE1, FILE2]
          formats: [provx, json]

    :param comparators: Mapping of comparator names to 
    class names and comparator-specific configuration
    :type config: dict
    :raises ConfigError: if ``comparators`` is empty,
    comparator-specific configuration is missing ``class``, or there
    is a problem loading, creating or configuring an instance of a 
    sub-class of :class:`~prov.interop.comparator.Comparator`.
    """
    if len(comparators) == 0:
      raise ConfigError("There must be at least one comparator defined")
    for comparator_name in comparators:
      config = comparators[comparator_name]
      HarnessResources.check_configuration(
        config, [HarnessResources.CLASS])
      class_name = config[HarnessResources.CLASS]
      comparator = factory.get_instance(class_name)
      comparator.configure(config)
      self._comparators[comparator_name] = comparator
      for format in comparator.formats:
        self._format_comparators[format] = comparator

  def configure(self, config):
    """Configure harness.
    ``config`` is expected to hold configuration of form::

        test-cases: ...test cases directory...
        comparators:
          Comparator nick-name
            class: ... class name...
            ...class-specific configuration...
        ...other configuration...

    Other configuration is saved but not processed by this class.

    For example::

        test-cases: /home/user/interop/test-cases
        comparators:
          ProvPyComparator: 
            class: prov.interop.provpy.comparator.ProvPyComparator
            executable: python
            arguments: [/home/user/prov/scripts/prov-compare, -f, FORMAT1, -F, FORMAT2, FILE1, FILE2]
            formats: [provx, json]
        ProvPy: /home/user/interop/config/provpy.yaml
        ProvToolbox: /home/user/interop/config/provtoolbox.yaml
        ProvTranslator: /home/user/interop/config/provtranslator.yaml
        ProvStore: /home/user/interop/config/provstore.yaml

    :param config: Configuration
    :type config: dict
    :raises ConfigError: if ``config`` does not hold the above
    entries, or problems arise invoking :func:`configure`
    """
    super(HarnessResources, self).configure(config)
    HarnessResources.check_configuration(
      config,
      [HarnessResources.TEST_CASES, HarnessResources.COMPARATORS])
    self._test_cases = config[HarnessResources.TEST_CASES]
    self.register_comparators(config[HarnessResources.COMPARATORS])
