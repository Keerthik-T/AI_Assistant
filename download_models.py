import os
import sys
import urllib.request

MODEL_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/kokoro-v1.0.onnx"
VOICES_URL = "https://github.com/thewh1teagle/kokoro-onnx/releases/download/model-files-v1.0/voices-v1.0.bin"

MODEL_FILE = "kokoro-v1.0.onnx"
VOICES_FILE = "voices-v1.0.bin"


def download_file(url, filename):
    if os.path.exists(filename):
        print(f"File '{filename}' already exists, skipping download.")
        return

    print(f"Downloading {filename} from {url}...")

    def progress_callback(block_num, block_size, total_size):
        read_so_far = block_num * block_size
        if total_size > 0:
            percent = (read_so_far * 100) / total_size
            sys.stdout.write(
                f"\rProgress: {percent:.1f}% ({read_so_far / 1024 / 1024:.2f} MB / {total_size / 1024 / 1024:.2f} MB)"
            )
        else:
            sys.stdout.write(f"\rProgress: {read_so_far / 1024 / 1024:.2f} MB")
        sys.stdout.flush()

    try:
        urllib.request.urlretrieve(url, filename, reporthook=progress_callback)
        print(f"\nSuccessfully downloaded {filename}!")
    except Exception as e:
        print(f"\nError downloading {filename}: {e}")
        if os.path.exists(filename):
            os.remove(filename)


if __name__ == "__main__":
    print("Starting Kokoro Model Downloader...")
    download_file(MODEL_URL, MODEL_FILE)
    download_file(VOICES_URL, VOICES_FILE)
    print("Done!")
