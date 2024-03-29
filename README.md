# Examples-python
Examples of calling Cobalt's Python SDKs.

## Cubic Example
The [cubic](./cubic) folder contains three example clients that interact with Cubic.
* [batch_client](./cubic/batch_client.py), which submits all audio to Cubic before receiving a transcript. Audio data is read from a file.
* [streaming_client](./cubic/streaming_client.py), which streams audio to Cubic as it becomes available, and receives transcripts back from Cubic as they become available. The audio I/O is handled by a user-specified external process, such as sox, aplay, arecord, etc.
* [webrtc_client](./cubic/webrtc_client.py), which establishes a WebRTC connection to Cubic and streams several files in real-time, writing their transcripts back to a single file.

## Luna Example
The [luna](./luna) folder contains an example client that interacts with Luna.
* [cli_client](./luna/cli_client.py), which allows a user to send text to synthesize to Luna, then streams back the audio as it is received. The audio I/O is handled by a user-specified external process, such as sox, aplay, arecord, etc.

## Diatheke Example
The [diatheke](./diatheke) folder contains two example clients that interact with Diatheke.
* [audio_client](./diatheke/audio_client.py), which is a voice only interface where the application accepts user audio, processes the result, then gives back an audio response. The audio I/O is handled by a user-specified external process, such as sox, aplay, arecord, etc.
* [cli_client](./diatheke/cli_client.py), which is a text only interface where the application processes text from the user, then gives a reply as text.

See [here](./diatheke/README.md) for more details about the examples, and [here](https://sdk-diatheke.cobaltspeech.com) for the SDK documentation.
