
from brainmaze_data_files.cadence_workstation import downsample_cadence_mef3_to_250Hz

path = '/Volumes/Beryllium/Data/bds_export/R22D037/R22D037_IntraOP.mefd'
path_dest = '/Users/mivalt.filip/Data'

downsample_cadence_mef3_to_250Hz(path, path_dest=path_dest, time_step=10*60)

