
import os
import numpy as np
import shutil


from mef_tools.io import MefWriter, MefReader
from scipy import signal
from tqdm import tqdm

def downsample_cadence_mef3_to_250Hz(path_source, path_dest=None, time_step=10*60):
    fs_target = 250

    if not os.path.exists(path_source):
        raise FileNotFoundError(f"Source file {path_source} does not exist.")

    if not path_source.endswith('.mefd'):
        raise ValueError(f"Source file {path_source} is not a MEF3 file.")

    path_new = path_dest

    if path_new is None:
        path_new = path_source.replace('.mefd', f'_{fs_target}Hz.mefd')

    if not path_new.endswith('.mefd'):
        path_new = os.path.join(path_new, path_source.split(os.sep)[-1].replace('.mefd', f'_{fs_target}Hz.mefd'))

    base_dir = os.path.dirname(path_new)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    rdr = MefReader(path_source)
    fs = rdr.get_property('fsamp')

    print('#########################')
    print(f'Session {path_source}')
    print(f'Sample rate {max(fs)}')
    print('#########################')

    start = min(rdr.get_property('start_time'))
    end = max(rdr.get_property('end_time'))
    ts_steps = np.arange(start, end, time_step * 1e6)

    Wrt = MefWriter(path_new, overwrite=True)
    Wrt.max_nans_written = 0
    Wrt.record_offset = 0
    Wrt.section3_dict['GMT_offset'] = 0
    Wrt.mef_block_len = 10*250

    for ts in tqdm(ts_steps):
        s_ = ts
        e_ = s_ + (time_step * 1e6)

        x_ref = rdr.get_data('REF', s_, e_)

        for ch in rdr.channels:
            if 'status' in ch:
                continue

            if 'REF' in ch:
                continue

            fs = rdr.get_property('fsamp', ch)

            if fs != 8000:
                print(f'Channel {ch} has sample rate {fs}, skipping...')
                continue

            unit = rdr.get_property('unit', ch)
            ufact = rdr.get_property('ufact', ch)
            precision = int(np.ceil(np.abs(-np.log10(ufact))))

            Wrt.data_units = unit

            x = rdr.get_data(ch, s_, e_)
            if np.isnan(x).sum() < x.shape[0]:
                x = x - x_ref

                nans = np.isnan(x)
                if np.any(nans):
                    x[nans] = np.nanmean(x)

                nans_250 = nans[::32]

                x = signal.decimate(x, 8) # to 1000 Hz
                x = signal.decimate(x, 4) # to 250 Hz

                if np.any(nans):
                    x[nans_250] = np.nan

                Wrt.write_data(x, ch, start_uutc=s_, sampling_freq=250, precision=precision, reload_metadata=False, discont_handler=True)

            file_annot_src = os.path.join(path_source, 'annotations.csv')
            file_annot_dest = os.path.join(path_new, 'annotations.csv')

            if os.path.exists(file_annot_src):
                shutil.copyfile(file_annot_src, file_annot_dest)

def crop_cadence_mef3(path_source, path_dest=None, start=None, end=None, re_reference=True):
    if not os.path.exists(path_source):
        raise FileNotFoundError(f"Source file {path_source} does not exist.")

    if not path_source.endswith('.mefd'):
        raise ValueError(f"Source file {path_source} is not a MEF3 file.")

    path_new = path_dest

    if path_new is None:
        path_new = path_source.replace('.mefd', f'_cropped.mefd')

    if not path_new.endswith('.mefd'):
        path_new = os.path.join(path_new, path_source.split(os.sep)[-1].replace('.mefd', f'_cropped.mefd'))

    base_dir = os.path.dirname(path_new)
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)

    rdr = MefReader(path_source)
    fs = rdr.get_property('fsamp')

    print('#########################')
    print(f'Session {path_source}')
    print(f'Sample rate {max(fs)}')
    print('#########################')

    start_file = min(rdr.get_property('start_time')) / 1e6
    end_file = max(rdr.get_property('end_time')) / 1e6

    if not (start >= start_file and end <= end_file):
        raise ValueError(f"Start and end times must be within the file's time range: {start_file} - {end_file}")

    Wrt = MefWriter(path_new, overwrite=True)
    Wrt.max_nans_written = 0
    Wrt.record_offset = 0
    Wrt.section3_dict['GMT_offset'] = 0
    Wrt.mef_block_len = 10*8000

    s_ = start * 1e6
    e_ = end * 1e6

    x_ref = 0
    if re_reference:
        x_ref = rdr.get_data('REF', s_, e_)

    for ch in rdr.channels:
        if 'status' in ch:
            continue

        if 'REF' in ch and re_reference:
            continue

        fs = rdr.get_property('fsamp', ch)

        if fs != 8000:
            print(f'Channel {ch} has sample rate {fs}, skipping...')
            continue

        unit = rdr.get_property('unit', ch)
        ufact = rdr.get_property('ufact', ch)
        precision = int(np.ceil(np.abs(-np.log10(ufact))))
        Wrt.data_units = unit

        x = rdr.get_data(ch, s_, e_)
        if np.isnan(x).sum() < x.shape[0]:
            x = x - x_ref
            Wrt.write_data(x, ch, start_uutc=s_, sampling_freq=fs, precision=precision, reload_metadata=False, discont_handler=True)

