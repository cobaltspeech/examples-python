# Cubic Examples
This directory contains code demonstrating how to use the [Cubic SDK](https://docs.cobaltspeech.com/asr/sdk-cubic/).

## Build
Before using the examples, the Cubic SDK package must be installed. For the examples, we recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to do this.

```bash
# Create the virtual environment using Python 3 and activate it
python3 -m venv cubic-env
source cubic-env/bin/activate

# Install the Cubic SDK
pip install --upgrade pip
pip install "git+https://github.com/cobaltspeech/sdk-cubic#egg=cobalt-cubic&subdirectory=grpc/py-cubic"
```

## Run
These examples are intended to be run from the command line. Note that for these examples, the server address, model ID, and other options are hardcoded near the beginning of the files.

```bash
cd <path/to/examples-python/cubic>

# Run the batch ASR client (uses a file for input)
python batch_client.py

# Run the streaming ASR client (uses an external program for input)
python streaming_client.py
```

## Audio I/O
For the `streaming_client` example, the audio I/O is handled exclusively by external applications such as aplay/arecord or sox. This allows some flexibility in audio processing as it does not require a tight integration in the example code with specific audio drivers, as all audio is simply piped from the external application to the example. The specific application can be anything as long the following conditions are met:

* The application supports the encodings, sample rate, bit-depth, etc. required by the underlying Cubic ASR models.
* For recording, the application must stream audio data to stdout.

The specific applications (and their args) should be specified as strings in the code (the `record_cmd` variable).

For the `batch_client` example, audio comes from sample.wav, included in this directory for convenience. A different
file may be used by specifying its path in the `audio_file` variable, provided the file has the correct encoding,
sample rate, bit-depth, etc. that the underlying Cubic model supports.
