#!/bin/bash


# Configure Innolight DR4 transceiver module into 4x100G breakout mode
# so that each 100G ports can be operated independently

# Usage:
# ./cmis4_initial.sh $port_i2c_no
#
port=$1

# "========================================================================="
# "Init CMIS 4.0 module in port $port"
# "========================================================================="

# "-------------------------------------------------------------------------"
# " Set page 00h before start configuration..."
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 0x7f 0

# "-------------------------------------------------------------------------"
# "step 1. SW reset module"
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 26 0x08
sleep 0.2

# "-------------------------------------------------------------------------"
# "step 2. deinitialize datapath"
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 127 0x10
sudo i2cset -f -y $port 0x50 128 0xff

# "-------------------------------------------------------------------------"
# "step 3. enable hi-power mode"
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 26 0x00
sleep 0.2

# "-------------------------------------------------------------------------"
# "step 4. Datapath configuration"
# "step 4.a. Write 0xff to page 10h byte 143"
# "          Apply DataPathInit..."
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 0x7f 0x10 
sudo i2cset -f -y $port 0x50 0x8f 0xff  
sleep 0.2

# "-------------------------------------------------------------------------"
# "step 4.b. Check configuration errors codes in page 11h byte 202 - 205"
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 0x7f 0x11

# "-------------------------------------------------------------------------"
# "step 5. Datapath activation Write the corresponding values to upper page"
# "        10h byte 128 (to power up the DP lanes)"
# "-------------------------------------------------------------------------"
sudo i2cset -f -y $port 0x50 0x7f 0x10
sudo i2cset -f -y $port 0x50 0x80 0x00

sudo i2cset -f -y $port 0x50 0x7f 0
