# Diatheke Examples
This directory contains code demonstrating how to use Cobalt [Pre-generated SDK files for Python](https://github.com/cobaltspeech/py-genproto).

## Build
Before using the examples, the Diatheke SDK package must be installed. For the examples, we recommend using a [virtual environment](https://docs.python.org/3/tutorial/venv.html) to do this.

```bash
# Create the virtual environment and activate it
python3 -m venv diatheke-env
source diatheke-env/bin/activate

pip install --upgrade pip
pip install "git+https://github.com/cobaltspeech/py-genproto"
```

## Run
These examples are intended to be run from the command line, where they will accept either text or audio input. Note that for these examples, the server address, model ID, and other options are hardcoded near the beginning of the files.

```bash
cd <path/to/examples-python/diatheke>

# Run the text-based client
python audio_client.py

# Run the audio-based client
python cli_client.py
```

## Audio I/O
For the `audio_client` example, the audio I/O is handled exclusively by external applications such as aplay/arecord or sox. The specific application can be anything as long the following conditions are met:

* The application supports the encodings, sample rate, bit-depth, etc. required by the underlying Cubic ASR and Luna TTS models.
* For recording, the application must stream audio data to stdout.
* For playback, the application must accept audio data from stdin.

The specific applications (and their args) should be specified as strings in the code (the `record_cmd` and `play_cmd` variables).
