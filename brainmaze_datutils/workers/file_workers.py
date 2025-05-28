
import os
import time
import threading

CHUNK_SIZE = 1024 * 1024 * 4 # 4 MB

class FileWorker:
    def __init__(self, path_src: str, path_dest: str, move_file: bool = False, start_at_init: bool = False):
        self._path_src = str(path_src)
        self._path_dest = str(path_dest)
        self._move = move_file

        self._last_update_time = 0
        self._last_processed_size = 0
        self._progress = 0
        self._speed = 0.0
        self._eta = 0.0
        self._processed_size = 0
        self._total_size = 0
        self._in_progress = False
        self._finished = False

        self._cancel = False
        self._thread = None
        self.lock = threading.Lock()

        if start_at_init:
            self.start()

    def error(self, error: str):
        print(f"Error: {error}")

    def start(self):
        self._cancel = False
        self._in_progress = True
        self._finished = False
        self._thread = threading.Thread(target=self._start_copy)
        self._thread.start()

    def cancel(self):
        if self._thread is None:
            return

        with self.lock:
            self._cancel = True

        time.sleep(0.1)
        if self._thread:
            self._thread.join()
            self._thread = None

    def _calculate_speed_and_eta(self, processed_size: int, total_size: int):
        current_time = time.time()
        time_delta = current_time - self._last_update_time

        # if time_delta >= 0.1:
        size_delta = processed_size - self._last_processed_size
        speed = size_delta / time_delta if time_delta > 0 else 0
        remaining_size = total_size - processed_size
        eta = remaining_size / speed if speed > 0 else 0
        self._last_update_time = current_time
        self._last_processed_size = processed_size
        return speed / (1024 * 1024), eta

    def _start_copy(self):
        if not os.path.exists(self._path_src):
            return

        try:
            total_size = os.path.getsize(self._path_src)
            os.makedirs(os.path.dirname(self._path_dest), exist_ok=True)

            self._last_update_time = time.time()
            processed_size = 0

            with open(self._path_src, 'rb') as fsrc, open(self._path_dest, 'wb') as fdst:
                while self._in_progress:
                    if self._cancel:
                        if os.path.exists(self._path_dest):
                            os.remove(self._path_dest)
                        return

                    chunk = fsrc.read(CHUNK_SIZE)
                    if not chunk:
                        self._finished = True
                        self._in_progress = False
                        break

                    fdst.write(chunk)
                    processed_size += len(chunk)

                    speed, eta = self._calculate_speed_and_eta(processed_size, total_size)
                    if speed is not None:
                        progress = (processed_size / total_size) * 100
                        processed_mb = processed_size / (1024 * 1024)
                        total_mb = total_size / (1024 * 1024)
                        self._update_progress(progress, speed, eta, processed_mb, total_mb)

            if self._move:
                os.remove(self._path_src)

        except Exception as e:
            if os.path.exists(self._path_dest):
                os.remove(self._path_dest)
            print(f"Error: {str(e)}")

    def _update_progress(self, progress: float, speed: float, eta: float, processed_size: float, total_size: float):
        with self.lock:
            self._progress = progress
            self._speed = speed
            self._eta = eta
            self._processed_size = processed_size
            self._total_size = total_size

    @property
    def finished(self):
        return self._finished

    @property
    def progress(self):
        return self._progress

    @property
    def in_progress(self):
        return self._in_progress

    @property
    def status(self):
        return {
            'in_progress': self._in_progress,
            'finished': self._finished,
            'progress': self._progress,
            'speed': self._speed,
            'eta': self._eta,
            'processed_size': self._processed_size,
            'total_size': self._total_size,
            'source': self._path_src,
            'destination': self._path_dest
        }



    def __del__(self):
        if self._thread:
            self._thread.join()
            self._thread = None
