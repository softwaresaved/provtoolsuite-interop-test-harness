"""Manages invocation of ProvPy prov-convert script.
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

import os.path
import re
import shutil
import subprocess

from prov_interop import standards
from prov_interop.component import CommandLineComponent
from prov_interop.component import ConfigError
from prov_interop.converter import ConversionError
from prov_interop.converter import Converter

class ProvPyConverter(Converter, CommandLineComponent):
  """Manages invocation of ProvPy prov-convert script."""

  FORMAT = "FORMAT"
  """string or unicode: token for output format in command-line specification"""
  INPUT = "INPUT"
  """string or unicode: token for input file in command-line specification"""
  OUTPUT = "OUTPUT"
  """string or unicode: token for output file in command-line specification"""
  LOCAL_FORMATS = {standards.PROVX: "xml"}
  """list of string or unicode: list of mapping from formats in
  ``prov_interop.standards`` to formats understood by prov-convert
` """

  def __init__(self):
    """Create converter.
    """
    super(ProvPyConverter, self).__init__()

  def configure(self, config):
   """Configure converter.
    ``config`` is expected to hold configuration of form::

        executable: ...executable name...
        arguments: [...list of arguments including tokens INPUT, OUTPUT...]
        input-formats: [...list of formats...]
        output-formats: [...list of formats...]

    For example::

        executable: python
        arguments: [/home/user/prov/scripts/prov-convert, -f, FORMAT, INPUT, OUTPUT]
        input-formats: [json]
        output-formats: [provn, provx, json]

    Input and output formats must be as defined in
    ``prov_interop.standards``.

    :param config: Configuration
    :type config: dict
    :raises ConfigError: if ``config`` does not hold the above entries
    """
   super(ProvPyConverter, self).configure(config)
   ProvPyConverter.check_configuration(
     self._arguments,
     [ProvPyConverter.FORMAT, ProvPyConverter.INPUT,
      ProvPyConverter.OUTPUT])

  def convert(self, in_file, out_file):
    """Use prov-convert to convert an input file into an output
    file. Each file must have an extension matching one of those
    in ``prov_interop.standards``.
    ``executable`` and ``arguments`` in the configuration are used to
    create a command to execute at the shell. ``FORMAT``,
    ``INPUT`` and ``OUTPUT`` tokens are populated using
    ``in_file``, ``out_file`` values, with mappings to local formats
    supported by prov-cconvert being done if needed.

    :param in_file: Input file name
    :type in_file: str or unicode
    :param out_file: Output file name
    :type out_file: str or unicode
    :raises ConversionError: if the input file is not found, the
    return code is non-zero, the return code is zero but the output
    file is not found, or the input format is invalid
    :raises OSError: if there are problems invoking the converter
    e.g. the script is not found
    """
    super(ProvPyConverter, self).convert(in_file, out_file)
    in_format = os.path.splitext(in_file)[1][1:]
    out_format = os.path.splitext(out_file)[1][1:]
    if not in_format in self.input_formats:
      raise ConversionError("Unsupported input format: " + in_format)
    if not out_format in self.output_formats:
      raise ConversionError("Unsupported input format: " + out_format)
    # Map prov_interop.standards formats to formats supported by prov-convert
    local_in_file = in_file
    local_in_format = in_format
    if (in_format in ProvPyConverter.LOCAL_FORMATS):
      local_in_format = ProvPyConverter.LOCAL_FORMATS[in_format]
      local_in_file = re.sub(in_format + "$", local_in_format, in_file)
      shutil.copy(in_file, local_in_file)
    local_out_file = out_file
    local_out_format = out_format
    if (out_format in ProvPyConverter.LOCAL_FORMATS):
      local_out_format = ProvPyConverter.LOCAL_FORMATS[out_format]
      local_out_file = re.sub(out_format + "$", local_out_format, out_file)
    # Replace tokens in arguments
    command_line = [local_out_format if x==ProvPyConverter.FORMAT else x 
                    for x in self._arguments]
    command_line = [local_in_file if x==ProvPyConverter.INPUT else x 
                    for x in command_line]
    command_line = [local_out_file if x==ProvPyConverter.OUTPUT else x 
                    for x in command_line]
    command_line.insert(0, self.executable)
    # Execute
    try:
      print(" ".join(command_line))
      return_code = subprocess.call(command_line)
      if return_code != 0:
        raise ConversionError(self._executable + " returned " + str(return_code))
      if not os.path.isfile(local_out_file):
        raise ConversionError("Output file not found: " + local_out_file)
      # If using local file extensions, rename output file to have 
      # prov_interop.standards extension
      if (out_format != local_out_format):
        shutil.move(local_out_file, out_file)
    finally:
      if (local_in_file != in_file) and os.path.isfile(local_in_file):
        os.remove(local_in_file)
      if (local_out_file != out_file) and os.path.isfile(local_out_file):
        os.remove(local_out_file)