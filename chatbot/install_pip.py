# get-pip.py
import os
import shutil
import sys
import tempfile
import urllib.request

BOOTSTRAP_SCRIPT = "https://bootstrap.pypa.io/get-pip.py"

def main():
    with urllib.request.urlopen(BOOTSTRAP_SCRIPT) as response:
        script = response.read()

    temp_dir = tempfile.mkdtemp()
    script_path = os.path.join(temp_dir, "get-pip.py")

    with open(script_path, "wb") as f:
        f.write(script)

    print("Running pip installer...")
    os.system(f'"{sys.executable}" "{script_path}"')

    shutil.rmtree(temp_dir)

if __name__ == "__main__":
    main()
