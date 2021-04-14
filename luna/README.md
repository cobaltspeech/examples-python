# Luna Examples
This directory contains code demonstrating how to use the
[Luna SDK](https://sdk-luna.cobaltspeech.com).

## Build
Before using the examples, the Luna SDK package must be installed.
For the examples, we recommend using a [virutal environment](https://docs.python.org/3/tutorial/venv.html) to do this.

```bash
# Create the virtual environment and activate it
python3 -m venv luna-env
source luna-env/bin/activate

# Install the Luna SDK
pip install "git+https://github.com/cobaltspeech/sdk-luna#egg=cobalt-luna&subdirectory=grpc/py-luna"
```

## Run
The examples are intended to be run from the command line. Note that the server address, model ID, and other options are hardcoded near the beginning of the file.

```bash
cd <path/to/examples-python/luna>

# Run the CLI
python cli_client.py
```

## Audio I/O
The audio I/O is handled exclusively by external applications such
as aplay/arecord or sox. This allows some flexibility in audio
processing as it does not require a tight integration in the 
example code with specific audio drivers, as all audio is simply
piped from the external application to the example. The specific
application can be anything as long as the following conditions are met:

* The application supports the encodings, sample rate, bit-depth, etc. of the audio returned by Luna.
* For playback, the application must read audio data from stdin.

The specific applications (and their args) should be specified as
strings in the code (the `play_cmd` variable).
