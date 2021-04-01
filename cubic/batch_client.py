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

# Name of the file to process
audio_file = "./sample.wav"

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
    print("Running batch ASR on '{}' using model '{}'\n".format(audio_file, model_id))
    cfg = cubic.RecognitionConfig(
        model_id = model_id,
        audio_encoding = cubic.RecognitionConfig.WAV
    )

    try:
        # Open the audio file
        with open(audio_file, 'rb') as audio:
            # Start batch recognition. No results will be returned until
            # the entire file is processed.
            resp = client.Recognize(cfg, audio)
            for result in resp.results:
                if not result.is_partial:
                    print("Transcript:", result.alternatives[0].transcript)

    except KeyboardInterrupt:
        # stop streaming when ctrl+C pressed
        pass
    except Exception as err:
        print("Error while trying to process audio : {}".format(err))
