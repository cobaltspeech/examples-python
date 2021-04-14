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

import audio_io
import time
from luna.client import LunaClient
from luna import luna_pb2 as lunapb

# Connect to the Cobalt demo server (replace value to use a different
# server, such as "localhost:2727")
server_address = "demo.cobaltspeech.com:2727"

# TTS voice to use. You can view available models with the
# ListVoices() method (shown below).
voice_id = "en_US_25"

# The external process responsible for playing audio
play_cmd = "sox -q -c 1 -r 25600 -b 16 -L -e signed -t raw - -d"

def stream_synthesis(text, client, synth_config):
    """Run the streaming synthesis method for Luna client (i.e., play
    audio as it is generated)"""

    if text == "":
        return

    start_time = time.time()

    # Set up the playback application
    player = audio_io.Player(cmd=play_cmd)
    player.start()

    # Set up the synthesis stream
    print("Creating TTS stream using voice '{}'".format(synth_config.voice_id))
    request = lunapb.SynthesizeRequest(config=synth_config, text=text)
    stream = client.SynthesizeStream(request)
    offile = open("junk.raw", 'wb')

    # Play responses as they come
    first_response = True
    for response in stream:
        if first_response:
            first_response = False

            # Display some statistics for the first response
            time_to_first = time.time() - start_time
            print("time to first samples: {:f} seconds".format(time_to_first))

        player.push_audio(response.audio)
        offile.write(response.audio)

    # Close the stream and stop the player application
    player.stop()
    offile.close()

    # Print how long the entire method took
    total_time = time.time() - start_time
    print("streaming synthesis took {:f} seconds\n".format(total_time))


if __name__ == "__main__":
    # Create the client
    client = LunaClient(service_address=server_address)

    # Print version info
    version = client.Version().version
    print(version)
    print("")

    # Print the list of available voice models on the server
    resp = client.ListVoices()
    print("Available Models:")
    for v in resp.voices:
        print("  ID:", v.id)
        print("  Name:", v.name)
        print("  Sample Rate(Hz):", v.sample_rate)
        print("  Language:", v.language)
        print("")

    # Set up the synthesis config
    cfg = lunapb.SynthesizerConfig(
        voice_id=voice_id, 
        encoding=lunapb.SynthesizerConfig.RAW_LINEAR16
    )

    # Run the main loop
    try:
        while True:
            text = input("Luna> ")
            stream_synthesis(text, client, cfg)

    except KeyboardInterrupt:
        # Stop when ctrl+C pressed
        pass
    except EOFError:
        # Stop when ctrl+D pressed
        pass
    except Exception as err:
        print("Synthesis error:", err)

    print("")
