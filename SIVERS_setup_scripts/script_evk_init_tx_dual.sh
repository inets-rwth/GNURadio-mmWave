# This is how the order of operations will be. It will be sufficient to run this script to set up both EVK02001 and EVK06002.
# Make sure that you have already added the directories of cruijff and eder to your PYTHONPATH, as this script does not work otherwise for some reason.

trap 'echo Ctrl + C pressed, not stopping execution' 2 # to prevent exiting upon Ctrl + C

export pythonpathbackup=$PYTHONPATH

# first set up cruijff - replace the directory here with the location of the cruijff library in your system
export PYTHONPATH=$pythonpathbackup:/home/inets/Workspace/evk02001/cruijff_evk-Release_20211123_1800/cruijff_a/:
echo python evk02001_init_tx.py
python evk02001_init_tx.py

# then set up eder - replace the directory here with the location of the cruijff library in your system
export PYTHONPATH=$pythonpathbackup:/home/inets/Workspace/evk06002/evk06002_sw_release_20220406_1715/eder_evk-Release_20220406_1715/Eder_B/:
echo python evk06002_init_tx.py
python evk06002_init_tx.py

export PYTHONPATH=$pythonpathbackup
echo PYTHONPATH: $PYTHONPATH
echo "You may start the GNURadio flow now."

trap 2 # return to its original state
