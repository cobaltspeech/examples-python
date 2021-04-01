# -*- coding: utf-8 -*-
#
# Copyright(2021) Cobalt Speech and Language Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License")
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# http: // www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import subprocess


class Recorder(object):
    """Recorder launches an external application to handle recording audio."""

    def __init__(self, cmd):
        self.args = cmd.split()
        self.process = None

    def start(self):
        """Start the external recording application."""

        # Ignore if we already started it
        if self.process is not None:
            return

        # Start the subprocess
        self.process = subprocess.Popen(args=self.args,
                                        stdout=subprocess.PIPE)

    def stop(self):
        """Stop the external recording application."""

        # Ignore if it is not running
        if self.process is None:
            return

        # Stop the subprocess
        self.process.stdout.close()
        self.process.terminate()
        self.process = None

    def read(self, bufsize):
        """Read audio data from the external recording application."""

        # Raise an error if we haven't started the app
        if self.process is None:
            raise RuntimeError("Recording application is not running")

        # Get the data from stdout
        return self.process.stdout.read(bufsize)
