#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (2020 -- present) Cobalt Speech and Language, Inc.
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

import client
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
play_cmd = "sox -q -c 1 -r 22050 -b 16 -L -e signed -t raw - -d"


def wait_for_input(c, session, input_action):
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

    def result_handler(result):
        if len(result.partial_result.alternatives) != 0:
            print("\n  Partial Result:", result.partial_result)
        else:
            print("\n  ASRResult:")
            print("    Text: ", result.asr_result.text)
            print("    Confidence: ", result.asr_result.confidence)
            print("    cubic result:", result.asr_result.cubic_result)

    # Start the recorder
    recorder = audio_io.Recorder(cmd=record_cmd)
    recorder.start()
    print("\nStart recording...")

    # Record until we get an asr_result
    asr_result = c.read_asr_audio_with_partial(
        session.token, recorder.process.stdout, result_handler, 8192)
    recorder.stop()

    # ASR result found, process asr result and update session
    return c.process_asr_result(session.token, asr_result)


def handle_reply(c, reply):
    """Uses TTS to play back the reply as speech."""

    print("\n  Reply:")
    print("    Text: ", reply.text)
    print("    Luna Model: ", reply.luna_model)

    # Start the player
    player = audio_io.Player(cmd=play_cmd)
    player.start()
    c.write_tts_audio(reply, player.process.stdin)
    player.stop()


def handle_transcribe(c, scribe):
    """Creates a new transcribe stream and records audio from
    the user. Displays transcription in the terminal."""
    # Set up the result callback function
    final_transcription = ""

    def cb(result):
        nonlocal final_transcription

        # Print the result on the same line (overwrite current contents).
        # Note that this assumes stdout is going to a terminal.
        print(result.text, " (confidence: ", result.confidence, ")", end="\r")

        if result.is_partial:
            return

        # As this is a final result (non-partial), go to the next line
        # in preparation for the next result.
        print("")

        # Accumulate all non-partial results here.
        final_transcription = final_transcription + result.text

    # Start the recorder
    recorder = audio_io.Recorder(cmd=record_cmd)
    recorder.start()

    # Run the transcription
    c.read_transcribe_audio(scribe, recorder.process.stdout, 8192, cb)
    recorder.stop()

    # Display the final transcription
    print("\nFinal Transcription: ", final_transcription)


def handle_command(c, session, cmd):
    """Executes the task specified by the given command and
    returns an updated session based on the command result."""

    print("\n  Command:")
    print("    ID:", cmd.id)
    print("    Input params:", cmd.input_parameters)
    print("    NLU result:", cmd.nlu_result)

    # Update the session with the command result
    return c.process_command_result(session.token, cmd)


def process_actions(c, session):
    """Executes the actions for the given session and returns
    an updated session."""

    # Iterate through each action in the list and determine its type
    for action in session.action_list:
        if action.HasField("input"):
            # The WaitForuserAction will involve a session update.
            return wait_for_input(c, session, action.input)
        elif action.HasField("reply"):
            # Replies do not require a session update.
            handle_reply(c, action.reply)
        elif action.HasField("command"):
            # The CommandAction will involve a session update.
            return handle_command(c, session, action.command)
        elif action.HasField("transcribe"):
            # Transcribe actions do not require a session update.
            handle_transcribe(c, action.transcribe)
        else:
            raise RuntimeError("unknown action={}".format(action))


if __name__ == "__main__":
    # Create the client
    c = client.Client(server_address, insecure_connection)

    # Print server version info
    ver = c.version()
    print("Server Version")
    print("  Diatheke:", ver.diatheke)
    print("  Chosun (NLU):", ver.chosun)
    print("  Cubic (ASR):", ver.cubic)
    print("  Luna (TTS):", ver.luna)
    print("")

    # Print the list of available models on the server
    model_list = c.list_models()
    print("Available Models:")
    for mdl in model_list:
        print("  ID:", mdl.id)
        print("    Name:", mdl.name)
        print("    Language:", mdl.language)
        print("    ASR Sample Rate:", mdl.asr_sample_rate)
        print("    TTS Sample Rate:", mdl.tts_sample_rate)
        print("")

    # Create a new session
    session = c.create_session(model_id).session_output

    try:
        # Run the main loop
        while True:
            res = process_actions(c, session).session_output

            # Update session only if next action list is not empty.
            if len(res.action_list) != 0:
                session = res

    except BaseException as err:
        print(err)
    finally:
        # Clean up the session when we are done
        c.delete_session(session.token)
        print("Session closed")
