
import os
import numpy as np
import shutil


from mef_tools.io import MefWriter, MefReader
from scipy import signal
from tqdm import tqdm
from typing import List


def mef3_downsample_8khz_to_250Hz(
        path_source: str,
        path_dest: str=None,
        time_step: float=10*60,
        reference_ch: str=None,
        channels_include: List[str]=[],
        channels_ignore: List[str]=[]
):
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

    if not channels_include.__len__():
        channels_include = rdr.channels

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

        x_ref = 0
        if reference_ch is not None:
            if reference_ch not in rdr.channels:
                raise ValueError(f"Reference channel '{reference_ch}' not found in the MEF3 file.")
            x_ref = rdr.get_data(reference_ch, s_, e_)

        for ch in channels_include:
            if 'ch' in channels_ignore:
                continue

            if reference_ch in ch:
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

def mef3_crop(
        path_source: str,
        path_dest: str=None,
        start_utc: float=None,
        end_utc: float=None,
        reference_ch: str=None,
        channels_include: List[str] = [],
        channels_ignore:List[str] = []
):
    """
    Crops a MEF3 file to a specified time range and saves the result to a new file.

    Parameters:
    ----------
    path_source : str
        Path to the source MEF3 file. Must end with '.mefd'.
    path_dest : str, optional
        Path to save the cropped MEF3 file. If None, the output file will be saved
        in the same directory as the source file with '_cropped' appended to the name.
    start_utc : float
        Start time for cropping in UTC seconds. Must be within the time range of the source file.
    end_utc : float
        End time for cropping in UTC seconds. Must be within the time range of the source file.
    reference_ch : str, optional
        Name of the reference channel to subtract from all other channels. If None, no reference subtraction is applied.
    channels_include : list of str, optional
        List of channel names to include in the cropped file. If empty, all channels are included.
    channels_ignore : list of str, optional
        List of channel names to exclude from the cropped file. These channels will be ignored even if they are in `channels_include`.

    Raises:
    -------
    FileNotFoundError
        If the source file does not exist.
    ValueError
        If the source file is not a valid MEF3 file or if the specified time range is outside the file's time range.
        Also raised if the reference channel is not found in the file.

    Notes:
    ------
    - The function creates a new MEF3 file with cropped data.
    - If a reference channel is provided, its data is subtracted from all other channels before writing.
    - Channels with 'status' in their name or those explicitly ignored are skipped.

    Example:
    --------
    crop_mef3(
        path_source="data/session1.mefd",
        path_dest="data/session1_cropped.mefd",
        start_utc=1620000000,
        end_utc=1620003600,
        reference_ch="REF",
        channels_include=["CH1", "CH2"],
        channels_ignore=["CH3"]
    )
    """

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

    if not (start_utc >= start_file and end_utc <= end_file):
        raise ValueError(f"Start and end times must be within the file's time range: {start_file} - {end_file}")

    Wrt = MefWriter(path_new, overwrite=True)
    Wrt.max_nans_written = 0
    Wrt.record_offset = 0
    Wrt.section3_dict['GMT_offset'] = 0
    Wrt.mef_block_len = 10*8000

    s_ = start_utc * 1e6
    e_ = end_utc * 1e6

    x_ref = 0
    if reference_ch is not None:
        if reference_ch not in rdr.channels:
            raise ValueError(f"Reference channel '{reference_ch}' not found in the MEF3 file.")

        x_ref = rdr.get_data(reference_ch, s_, e_)

    if channels_include.__len__() == 0:
        channels_include = rdr.channels

    for ch in channels_include:
        if 'status' in ch:
            continue

        if ch == reference_ch:
            continue

        if ch in channels_ignore:
            continue

        fs = rdr.get_property('fsamp', ch)

        unit = rdr.get_property('unit', ch)
        ufact = rdr.get_property('ufact', ch)
        precision = int(np.ceil(np.abs(-np.log10(ufact))))
        Wrt.data_units = unit

        x = rdr.get_data(ch, s_, e_)
        if np.isnan(x).sum() < x.shape[0]:
            x = x - x_ref
            Wrt.write_data(x, ch, start_uutc=s_, sampling_freq=fs, precision=precision, reload_metadata=False, discont_handler=True)

