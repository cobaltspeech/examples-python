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

import grpc
import io
import cobaltspeech.diatheke.v3.diatheke_pb2 as diatheke_pb2
import transcribe_pb2 as transcribe_pb2

from cobaltspeech.diatheke.v3.diatheke_pb2_grpc import DiathekeServiceStub
from transcribe_pb2_grpc import TranscribeServiceStub
from streams import ASRStream, TranscribeStream


class Client(object):
    def __init__(self, server_address, insecure=False,
                 server_certificate=None,
                 client_certificate=None,
                 client_key=None):
        """  Creates a new Diatheke Client object.
        Args:
            server_address: host:port of where Diatheke server is running (string)
            insecure: If set to true, an insecure grpc channel is used.
                      Otherwise, a channel with transport security is used.
            server_certificate:  PEM certificate as byte string which is used as a
                                 root certificate that can validate the certificate
                                 presented by the server we are connecting to. Use this
                                 when connecting to an instance of cubic server that is
                                 using a self-signed certificate.
            client_certificate:  PEM certificate as bytes string presented by this Client when
                                 connecting to a server. Use this when setting up mutually
                                 authenticated TLS. The clientKey must also be provided.
            client_key:  PEM key as byte string presented by this Client when
                         connecting to a server. Use this when setting up mutually
                         authenticated TLS. The clientCertificate must also be provided.
        """
        self.server_address = server_address
        self.insecure = insecure

        if insecure:
            # no transport layer security (TLS)
            self._channel = grpc.insecure_channel(server_address)
        else:
            # using a TLS endpoint with optional certificates for mutual authentication
            if client_certificate is not None and client_key is None:
                raise ValueError("client key must also be provided")
            if client_key is not None and client_certificate is None:
                raise ValueError("client certificate must also be provided")
            self._creds = grpc.ssl_channel_credentials(
                root_certificates=server_certificate,
                private_key=client_key,
                certificate_chain=client_certificate)
            self._channel = grpc.secure_channel(server_address, self._creds)

        self._client = DiathekeServiceStub(self._channel)
        self._cubic  = TranscribeServiceStub(self._channel)

        self._buffer = b''

    def __del__(self):
        """ Closes and cleans up the client. """
        try:
            self._channel.close()
        except AttributeError:
            # client wasn't fully instantiated, no channel to close
            pass

    def version(self):
        """Returns the version information of the connected server."""
        return self._client.Version(diatheke_pb2.VersionRequest())

    def list_models(self):
        """Lists the models available to the Diatheke server, as specified in
        the server's config file."""
        return self._client.ListModels(diatheke_pb2.ListModelsRequest()).models

    def create_session(self, model_id: str, wakeword: str = "",
                       custom_metadata: str = "", storage_file_prefix: str = "",
                       input_audio_format: diatheke_pb2.AudioFormat = None,
                       output_audio_format: diatheke_pb2.AudioFormat = None):
        """Creates a new session using the specified _ID ID and return
        the session token and actions. The wakeword will only have an 
        effect if the model has wakeword detection enabled."""
        metadata = diatheke_pb2.SessionMetadata(custom_metadata=custom_metadata,
                                                storage_file_prefix=storage_file_prefix)

        return self._client.CreateSession(diatheke_pb2.CreateSessionRequest(
            model_id=model_id, wakeword=wakeword, metadata=metadata,
            input_audio_format=input_audio_format,
            output_audio_format=output_audio_format))

    def delete_session(self, token):
        """Cleans up the given token. Behavior is undefined if the given
        token is used again after calling this function."""
        self._client.DeleteSession(
            diatheke_pb2.DeleteSessionRequest(token_data=token))

    def process_text(self, token, text):
        """Sends the given text to Diatheke and returns an updated session
        token."""
        req = diatheke_pb2.UpdateSessionRequest(session_input=diatheke_pb2.SessionInput(
            token=token, text=diatheke_pb2.TextInput(text=text)))
        return self._client.UpdateSession(req)

    def process_asr_result(self, token, result):
        """Sends the given ASR result to Diatheke and returns an updated
        session token."""
        req = diatheke_pb2.UpdateSessionRequest(
            session_input=diatheke_pb2.SessionInput(token=token, asr=result))
        return self._client.UpdateSession(req)

    def process_command_result(self, token, cmd):
        """Sends the given command result to Diatheke and returns an updated
        session token. This function should be called in response to a command
        action Diatheke sent previously."""
        cmd = diatheke_pb2.CommandResult(id=cmd.id)
        req = diatheke_pb2.UpdateSessionRequest(
            session_input=diatheke_pb2.SessionInput(token=token, cmd=cmd))
        return self._client.UpdateSession(req)

    def set_story(self, token, story_id, params):
        """Changes the current story for a Diatheke session. Returns an
        updated session token."""
        story = diatheke_pb2.SetStory(story_id=story_id, parameters=params)
        req = diatheke_pb2.UpdateSessionRequest(
            session_input=diatheke_pb2.SessionInput(token=token, story=story))
        return self._client.UpdateSession(req)

    def new_session_asr_stream(self, token):
        """Creates a new stream to transcribe audio for the given
        session token."""
        # Create the ASR stream object and send the session token
        stream = ASRStream(client_stub=self._client)
        stream.send_token(token)
        return stream

    def new_tts_stream(self, token, reply):
        """Creates a new stream to receive TTS audio from Diatheke based
        on the given reply action."""
        return self._client.StreamTTS(diatheke_pb2.StreamTTSRequest(
            reply_action=reply, token=token))

    def new_transcribe_stream(self, action):
        """Creates a new stream for transcriptions usually in response to
        a transcribe action in the session output. This stream differs from
        an ASR stream in purpose - where a session's ASR stream accepts audio
        to continue a conversation with the system, a transcribe stream
        accepts audio for the sole purpose of getting a transcription that
        the client can use for any purpose (e.g., note taking, send a message,
        etc.)."""
        stream = TranscribeStream(client_stub=self._client)
        stream.send_action(action)
        return stream

    def read_asr_audio(self, token, reader, buff_size):
        """Convenience function to create an ASR stream and send audio
        from the given reader to the stream. This function blocks until
        a result is returned. Data is sent in chunks defined by buff_size."""
        # Check if we have a text or byte reader
        is_text = isinstance(reader, io.TextIOBase)

        # Set up a generator function to send the session token and audio
        # data to Diatheke.
        def send_data():
            yield diatheke_pb2.StreamASRRequest(token=token)
            while True:
                if self._buffer == b'':
                    data = reader.read(buff_size)
                else:
                    data = self._buffer
                if (is_text and data == '') or (not is_text and data == b''):
                    # Reached EOF
                    return

                # Send the audio
                yield diatheke_pb2.StreamASRRequest(audio=data)

        # Run the stream
        return self._client.StreamASR(send_data())

    def read_standby_audio(self, reader, buff_size, result_handler):
        
        # Check if we have a text or byte reader
        is_text = isinstance(reader, io.TextIOBase)
        try:
            # Set up a generator function to send the configuration and audio
            # data to Cubic to wait for wakeword.
            def send_data():
                cfg = transcribe_pb2.RecognitionConfig(model_id = "en_US-wakeword",
                                                    audio_format_raw=transcribe_pb2.AudioFormatRAW(sample_rate=16000, 
                                                                                                    channels=1,
                                                                                                    byte_order=transcribe_pb2.ByteOrder.BYTE_ORDER_LITTLE_ENDIAN,
                                                                                                    bit_depth=16,
                                                                                                    encoding=transcribe_pb2.AUDIO_ENCODING_SIGNED))
                yield transcribe_pb2.StreamingRecognizeRequest(config=cfg)

                while True:
                    data = reader.read(buff_size)

                    self._buffer = data
   
                    if (is_text and data == '') or (not is_text and data == b''):
                        # Reached EOF
                        print("reached EOF!")
                        return

                    audio = transcribe_pb2.RecognitionAudio(data=data)
                    # Send the audio
                    yield transcribe_pb2.StreamingRecognizeRequest(audio=audio)

            stream = self._cubic.StreamingRecognize(send_data())
            # Loop over result
            for resp in stream:
                result_handler(resp.result)
                if resp.result.alternatives[0].transcript_raw != "":
                    return resp.result.alternatives[0].transcript_raw
        except Exception as err:
            print("Error while trying to stream audio : {}".format(err))

    def read_asr_audio_with_partial(self, token, reader, result_handler, buff_size):
        """Convenience function to create an ASR stream and send audio
        from the given reader to the stream. This function blocks until
        a result is returned. Data is sent in chunks defined by buff_size."""
        # Check if we have a text or byte reader

        is_text = isinstance(reader, io.TextIOBase)

        # Set up a generator function to send the session token and audio
        # data to Diatheke.
        def send_data():
            yield diatheke_pb2.StreamASRWithPartialsRequest(token=token)
            while True:
                if self._buffer == b'':
                    data = reader.read(buff_size)
                else:
                    data = self._buffer 
                if (is_text and data == '') or (not is_text and data == b''):
                    # Reached EOF
                    return

                # Send the audio
                yield diatheke_pb2.StreamASRWithPartialsRequest(audio=data)

        # Run the stream
        stream = self._client.StreamASRWithPartials(send_data())

        # Loop over result and call result handler function
        for result in stream:
            result_handler(result)

            if result.asr_result.text != "":
                return result.asr_result

    def write_tts_audio(self, token, reply_action, writer):
        """Convenience function to create a TTS stream and send the audio
        to the given writer. This function blocks until there is no more
        audio to receive."""
        # Check if we have a text or byte writer
        is_text = isinstance(writer, io.TextIOBase)

        # Create the stream
        stream = self.new_tts_stream(token, reply_action)
        for data in stream:
            if is_text:
                # Convert the text to a string before writing
                writer.write(str(data.audio))
            else:
                writer.write(data.audio)

    def read_transcribe_audio(self, transcribe_action, reader, buff_size, callback):
        """Convenience function to create a transcribe stream that reads
        audio from the given reader in buff_size chunks. The provided
        callback is called with transcribe results as they become
        available. This function blocks until the streaming is complete."""
        # Check if we have a text or byte reader
        is_text = isinstance(reader, io.TextIOBase)

        # Set up a generator function to send the transcribe action
        # and audio data to Diatheke.
        def send_data():
            yield diatheke_pb2.TranscribeRequest(action=transcribe_action)
            while True:
                data = reader.read(buff_size)
                if (is_text and data == '') or (not is_text and data == b''):
                    # Reached the EOF
                    return

                # Send the audio
                yield diatheke_pb2.TranscribeRequest(audio=data)

        # Call the Transcribe method and send results to the callback
        for result in self._client.Transcribe(send_data()):
            callback(result)
