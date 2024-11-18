#!/bin/bash
cd
cd ~/GNURadio-mmWave/OOT_modules_new/gr-iNETS_SIVERSControl
sudo rm -r build/
mkdir build
cd build
cmake ..
make -j4
sudo make install
sudo ldconfig
