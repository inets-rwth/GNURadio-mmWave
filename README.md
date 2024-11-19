
GNURadio-mmWave
================================

This GNURadio framework is based on the work proposed in the paper:

A. Schott, A. Ichkov, B. Acikgöz, N. Beckmann, L. Reiher, L. Simić, “A Multi-Band mm-Wave Experimental Platform Towards Environment-Aware Beam Management in the Beyond-5G Era”, in Proc. ACM WiNTECH 2024.


Installation
=========================

- The setup has been tested on Ubuntu OS (both 20.04 LTS as well as MATE distribution).
- Make sure that you have Python 3.8 installed on your system.
- Install GNURadio 3.10 from source. You can follow the official guide from GNURadio provided here: https://wiki.gnuradio.org/index.php?title=LinuxInstall#For_GNU_Radio_3.10,_3.9,_and_Main_Branch. Note that our framework is developed for operation using USRP X410, so you need to install UHD 4.6 before installing GNURadio (please refer to the GNURadio documentation on the provided link).
- Install the drivers for the SIVERS Semiconductors EVK02001 and EVK06002/3. The instructions and source files are provided by the manufacturer (SIVERS Semiconductors) upon the purchase of these modules. After installation, append the locations of these drivers (the folder paths ending with "cruijff_a" and "Eder_B") to your PYTHONPATH environment variable. Otherwise, you will not be able to import the driver libraries in Python.
- Download the "OOT_modules_new" folder from this repository. Install all the modules within the folder. You can use the provided "install_module.sh" bash script by replacing the directory for each module you want to install.
- Download the "Flowgraphs" and "SIVERS_setup_scripts" folders from this repository.

The correct operation of the system has been verified for Ubuntu 20.04 LTS, Python 3.8.10, GNURadio 3.10.6, UHD 4.6.0 and the latest driver versions for the SIVERS Semiconductors EVK02001 (cruijff_evk-Release_20211123_1800) and EVK06002/3 (eder_evk-Release_20220406_1715).


Running
==================

- **USRP setup:** Make sure that you connect your USRP X410 via Ethernet to your PC and that you can succesfully reach it (run the standalone UHD command "uhd_usrp_probe" in the terminal).
- **EVK devices setup:** Make sure that your Sivers Semiconductors EVK02001 (for 28 GHz operation) and/or EVK06002/3 (for 60 GHz operation) are connected via the provided USB cable to your PC. You can verify this by running the accompanying driver from the manufacturer. Once this is verified, you can run the provided scripts in the "SIVERS_setup_scripts" for setting up the correct configuration parameters. For this, you would need to set the correct serial number of your EVK device in the provided script via the variable "unit_name = "SNSPXXXXXX", where XXXXXX is the 6-digit serial number of your EVK device (please change this for different modules using the individual scripts, e.g. evk02001_init_rx and evk02001_init_tx for the TX/RX EVK02001 and evk06002_init_rx and evk06002_init_tx for the TX/RX EVK06002/3). 
- **SPI & USB control for beam switching:** The GNURadio code enables both USB and SPI control for switching the beams of the EVK devices. If you want to use the provided USB control (please note that this is significantly slower that the SPI control), please set the variable "use_spi = False" in the provided scripts for initializing the EVK devices (see previous point). By default, the code assumes that fast SPI-control is used for beam switching, which is enabled via the UHD SPI API (https://files.ettus.com/manual/page_x400_gpio_api.html). The concrete steps for enabling SPI control on the EVK devices, i.e. cable connections and pin settings on the EVK device, can be found in the provided user manual. If you need additional help with enabling this on your EVK device, please do not hesitate to contact the authors.
- **Running the GNURadio code:** We provide four separate modes of operation, depending on the frequency and beam switching control mechanism:
    1) **Single-band 28 GHz operation (using EVK02001 & USB control)**
       "...\Flowgraphs\TX\SIVERS_USB_Control\Transceiver_Station_TX_USB.grc" for running the TX and "...\Flowgraphs\RX\SIVERS_USB_Control\Transceiver_Station_RX_USB.grc" for running the RX at 28 GHz.
    2) **Single-band 28 GHz operation (using EVK02001 & SPI control)**
       "...\Flowgraphs\TX\SIVERS_SPI_Control_SingleBand_28G\Transceiver_Station_TX_SPI_singleband_28G.grc" for running the TX and "...\Flowgraphs\RX\SIVERS_SPI_Control_28G\Transceiver_Station_RX_SPI_28G.grc" for running the RX at 28 GHz.
    3) **Single-band 60 GHz operation (using EVK06002/3 & SPI control)**
       "...\Flowgraphs\TX\SIVERS_SPI_Control_SingleBand_60G\Transceiver_Station_TX_SPI_singleband_60G.grc" for running the TX and "...\Flowgraphs\RX\SIVERS_SPI_Control_60G\Transceiver_Station_RX_SPI_60G.grc" for running the RX at 60 GHz.
    4) **Dual-band 28/60 GHz operation (using both EVK devices simultaneously & SPI control)**
       "...\Flowgraphs\TX\SIVERS_SPI_Control_DualBand\Transceiver_Station_TX_SPI_dualband.grc" for running the two TX devices simultaneously on the same USRP device. For running the dual-band RX, you need to run separate GNURadio instances connected to two individual USRP devices. For running the RX at 28 GHz, please use "...\Flowgraphs\RX\SIVERS_SPI_Control_28G\Transceiver_Station_RX_SPI_28G.grc" and for running the RX at 60 GHz, please use "...\Flowgraphs\RX\SIVERS_SPI_Control_60G\Transceiver_Station_RX_SPI_60G".
