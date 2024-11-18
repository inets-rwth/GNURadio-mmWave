#!/bin/bash
cd
cd /home/inets/Workspace/new_setup/OOT_modules_new/gr-iNETS_SIVERSControl
sudo rm -r build/
mkdir build
cd build
cmake ..
make -j5
sudo make install
sudo ldconfig
