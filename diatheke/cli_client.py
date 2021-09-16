#!/usr/bin/env python
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

import diatheke


# Define the client configuration
server_address = "localhost:9002"

# Whether the client connection should be insecure. Must match the
# server config. Insecure connections are not recommended for production.
insecure_connection = True

# The model ID to use when initializing the Diatheke session.
model_id = "1"


def wait_for_input(client, session, input_action):
    """Prompts the user for text input, then returns an updated
    session based on the user-supplied text."""

    # Wait for user input
    text = input("\n\nDiatheke> ")

    # Update the session with the text
    return client.process_text(session.token, text)

def handle_reply(client, reply):
    """Prints the text of the given reply to stdout."""

    print("\n  Reply:", reply.text)

def handle_command(client, session, cmd):
    """Executes the task specified by the given command and
    returns an updated session based on the command result."""

    print("\n  Command:")
    print("    ID:", cmd.id)
    print("    Input params:", cmd.input_parameters)

    # Update the session with the command result
    result = diatheke.CommandResult(id=cmd.id)
    return client.process_command_result(session.token, result)

def handle_transcribe(scribe):
    """Displays the transcribe action, but otherwise does nothing."""

    print("\n  Transcribe:")
    print("    ID:", scribe.id)
    print("    Cubic Model ID:", scribe.cubic_model_id)
    print("    Diatheke Model ID:", scribe.diatheke_model_id)

def process_actions(client, session):
    """Executes the actions for the given session and returns
    an updated session."""

    # Iterate through each action in the list and determine its type
    for action in session.action_list:
        if action.HasField("input"):
            # The WaitForUserAction will involve a session update.
            return wait_for_input(client, session, action.input)
        elif action.HasField("reply"):
            # Replies do not require a session update.
            handle_reply(client, action.reply)
        elif action.HasField("command"):
            # The CommandAction will involve a session update.
            return handle_command(client, session, action.command)
        elif action.HasField("transcribe"):
            # Transcribe actions do not require a session update.
            handle_transcribe(action.transcribe)
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
