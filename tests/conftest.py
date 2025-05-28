
import os
import shutil
import tempfile
import time

import pytest

@pytest.fixture()
def test_large_file():
    temp_dir = tempfile.mkdtemp()
    source_file = os.path.join(temp_dir, "test_1gb.bin")
    dest_file = os.path.join(temp_dir, "test_1gb_copy.bin")

    with open(source_file, 'wb') as f:
        f.write(os.urandom(1 * 1024 * 1024 * 1024))  # ~1 GB

    yield source_file, dest_file

    if os.path.exists(source_file):
        os.remove(source_file)

    if os.path.exists(dest_file):
        os.remove(dest_file)

    shutil.rmtree(temp_dir, ignore_errors=True)
    while os.path.exists(temp_dir):
        time.sleep(0.1)

