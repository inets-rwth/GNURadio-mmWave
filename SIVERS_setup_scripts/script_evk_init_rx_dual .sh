# This is how the order of operations will be. It will be sufficient to run this script to set up both EVK02001 and EVK06002.

trap 'echo Ctrl + C pressed, not stopping execution' 2 # to prevent exiting upon Ctrl + C

pythonpathbackup=$PYTHONPATH

# first set up cruijff - replace the directory here with the location of the cruijff library in your system
export PYTHONPATH=$pythonpathbackup:/home/inets/Workspace/evk02001/cruijff_evk-Release_20211123_1800/cruijff_a:
echo python evk02001_init_rx.py
python evk02001_init_rx.py

# then set up eder - replace the directory here with the location of the cruijff library in your system
export PYTHONPATH=$pythonpathbackup:/home/inets/Workspace/evk06002/evk06002_sw_release_20220406_1715/eder_evk-Release_20220406_1715/Eder_B:
echo python evk06002_init_rx.py
python evk06002_init_rx.py

export PYTHONPATH=$pythonpathbackup
echo "You may start the GNURadio flow now."

trap 2 # return to its original state
popd
