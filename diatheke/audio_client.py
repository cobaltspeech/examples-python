#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright(2020) Cobalt Speech and Language Inc.
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

import diatheke
import audio_io


# Define the client configuration
server_address = "localhost:9002"

# Whether the client connection should be insecure. Must match the
# server config. Insecure connections are not recommended for production.
insecure_connection = True

# The model ID to use when initializing the Diatheke session.
model_id = "1"

# The external process responsible for recording audio
record_cmd = "sox -q -d -c 1 -r 16000 -b 16 -L -e signed -t raw -"

# The external process responsible for playing audio
play_cmd = "sox -q -c 1 -r 48000 -b 16 -L -e signed -t raw - -d"


def wait_for_input(client, session, input_action):
    """Creates a new ASR stream and records audio from the user.
    The audio is sent to Diatheke until an ASR result is returned,
    which is used to return an updated session."""

    # The given input action has a couple of flags to help the
    # app decide when to begin recording audio.
    if input_action.immediate:
        # This action is likely waiting for user input in response
        # to a question Diatheke asked, in which case the user should
        # reply immediately. If this flag is false, the app may wait
        # as long as it wants before processing user input (such as
        # waiting for a wake-word below).
        pass
    
    if input_action.requires_wake_word:
        # This action requires the wake-word to be spoken before
        # the user input will be accepted. Use a wake-word detector
        # and wait for it to trigger.
        pass

    # Create an ASR stream
    stream = client.new_session_asr_stream(session.token)

    # Start the recorder
    recorder = audio_io.Recorder(cmd=record_cmd)
    recorder.start()
    print("\nRecording...")

    # Record until we get a result
    result = diatheke.read_ASR_audio(stream, recorder.process.stdout, 8192)
    recorder.stop()

    # Display the result
    print("\n  ASRResult:")
    print("    Text: ", result.text)
    print("    Confidence: ", result.confidence)

    return client.process_asr_result(session.token, result)

def handle_reply(client, reply):
    """Uses TTS to play back the relpy as speech."""

    print("\n  Reply:")
    print("    Text: ", reply.text)
    print("    Luna Model: ", reply.luna_model)
    
    # Create the tts stream
    stream = client.new_tts_stream(reply)

    # Start the player
    player = audio_io.Player(cmd=play_cmd)
    player.start()
    diatheke.write_TTS_audio(stream, player.process.stdin)
    player.stop()

def handle_command(client, session, cmd):
    """Executes the task specified by the given command and
    returns an updated session based on the command result."""

    print("\n  Command:")
    print("    ID:", cmd.id)
    print("    Input params:", cmd.input_parameters)

    # Update the session with the command result
    result = diatheke.CommandResult(id=cmd.id)
    return client.process_command_result(session.token, result)

def process_actions(client, session):
    """Executes the actions for the given session and returns
    an updated session."""

    # Iterate through each action in the list and determine its type
    for action in session.action_list:
        if action.HasField("input"):
            # The WaitForuserAction will involve a session update.
            return wait_for_input(client, session, action.input)
        elif action.HasField("reply"):
            # Replies do not require a session update.
            handle_reply(client, action.reply)
        elif action.HasField("command"):
            # The CommandAction will involve a session update
            return handle_command(client, session, action.command)
        else:
            raise RuntimeError("unknown action={}".format(action))

if __name__ == "__main__":
    # Create the client
    client = diatheke.Client(server_address, insecure_connection)

    # Print server version info
    ver = client.version()
    print("Server Version")
    print("  Diatheke:", ver.diatheke)
    print("  Chosun (NLU):", ver.chosun)
    print("  Cubic (ASR):", ver.cubic)
    print("  Luna (TTS):", ver.luna)
    print("")

    # Print the list of available models on the server
    model_list = client.list_models()
    print("Available Models:")
    for mdl in model_list:
        print("  ID:", mdl.id)
        print("    Name:", mdl.name)
        print("    Language:", mdl.language)
        print("    ASR Sample Rate:", mdl.asr_sample_rate)
        print("    TTS Sample Rate:", mdl.tts_sample_rate)
        print("")

    # Create a new session
    session = client.create_session(model_id)

    try:
        # Run the main loop
        while True:
            session = process_actions(client, session)

    except BaseException as err:
        print(err)
    finally:
        # Clean up the session when we are done
        client.delete_session(session.token)
        print("Session closed")
