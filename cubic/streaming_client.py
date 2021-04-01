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

import cubic
import audio_io


# Connect to the Cobalt demo server (replace value to use a different
# server, such as "localhost:2727")
server_address = "demo.cobaltspeech.com:2727"

# ASR model to use. You can view available models with the
# ListModels() method (shown below).
model_id = "en-us-16-far"

# Whether the client connection is insecure. Must match the
# server config. Insecure connections are not recommended for
# production.
insecure_connection = False

# The external process responsible for recording audio
record_cmd = "sox -q -d -c 1 -r 16000 -b 16 -L -e signed -t raw -"

if __name__ == "__main__":
    # Create the client
    client = cubic.Client(server_address)

    # Print version info
    resp = client.Version()
    print("Version")
    print("  Cubic:", resp.cubic)
    print("  Server:", resp.server)
    print("")

    # Print the list of available models on the server
    resp = client.ListModels()
    print("Available Models:")
    for mdl in resp.models:
        print("  ID:", mdl.id)
        print("  Name:", mdl.name)
        print("  Sample Rate:", mdl.attributes.sample_rate)
        print("")

    # Set up the recognition config
    print("Creating ASR stream using model '{}'".format(model_id))
    cfg = cubic.RecognitionConfig(
        model_id = model_id
    )

    # Set up the external recorder
    recorder = audio_io.Recorder(cmd=record_cmd)
    recorder.start()

    try:
        # Stream the audio using our recorder app
        print("\n(Recording. Ctrl+C to exit)")
        for resp in client.StreamingRecognize(cfg, recorder):
            for result in resp.results:
                # This demo only cares about the final result
                if not result.is_partial:
                    print(result.alternatives[0].transcript)

    except KeyboardInterrupt:
        # stop streaming when ctrl+C pressed
        pass
    except Exception as err:
        print("Error while trying to stream audio : {}".format(err))

    recorder.stop()
