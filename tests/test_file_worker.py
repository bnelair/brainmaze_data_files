import pytest
import os.path
from typing import Tuple

import tempfile
import pandas as pd
import time
import shutil
import hashlib
import subprocess
import threading
import time
import os
import re
import shlex # For displaying the command safely
from pathlib import Path
import signal # For sending signals like SIGINT

from brainmaze_datutils.workers.file_workers import FileWorker
from brainmaze_datutils.utils import get_crc32

from .conftest import test_large_file


def test_dummy():
    assert True
    print('done')

def test_FileWorker_move(test_large_file: Tuple[str, str]):
    source_file, dest_file = test_large_file

    source_size = os.path.getsize(source_file)
    source_crc = get_crc32(source_file)

    transfer_worker = FileWorker(source_file, dest_file, move_file=True, start_at_init=True)
    time.sleep(0.1)
    assert transfer_worker.progress > 0
    assert transfer_worker.in_progress == True
    assert os.path.isfile(dest_file)

    while not transfer_worker.finished:
        time.sleep(0.01)
        print(transfer_worker.progress)

    assert os.path.exists(dest_file)
    assert not os.path.exists(source_file)

    dest_size = os.path.getsize(dest_file)
    dest_crc = get_crc32(dest_file)

    assert source_size == dest_size
    assert source_crc == dest_crc

def test_FileWorker_copy(test_large_file: Tuple[str, str]):
    source_file, dest_file = test_large_file

    source_size = os.path.getsize(source_file)
    source_crc = get_crc32(source_file)

    transfer_worker = FileWorker(source_file, dest_file, move_file=False, start_at_init=False)
    time.sleep(1)

    assert transfer_worker.progress == 0
    assert transfer_worker.in_progress == False
    assert not os.path.isfile(dest_file)

    transfer_worker.start()

    while not transfer_worker.finished:
        time.sleep(0.01)
        print(transfer_worker.progress)


    assert os.path.exists(dest_file)
    assert os.path.exists(source_file)

    dest_size = os.path.getsize(dest_file)
    dest_crc = get_crc32(dest_file)

    assert source_size == dest_size
    assert source_crc == dest_crc






