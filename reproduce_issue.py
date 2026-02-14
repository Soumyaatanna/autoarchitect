
import git
import tempfile
import shutil

def test_clone():
    url = "https://github.com/Soumyaatanna/"
    temp_dir = tempfile.mkdtemp()
    try:
        print(f"Attempting to clone {url}")
        git.Repo.clone_from(url, temp_dir, depth=1)
        print("Clone successful (unexpected)")
    except Exception as e:
        print(f"Clone failed as expected: {e}")
    finally:
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)

import os
if __name__ == "__main__":
    test_clone()
