#!/bin/sh
# Install the files on a pico
if [ -z "$1" ]
  then
    echo "/dev/ttyACMx parameter missing!"
		exit 0
fi

mpremote connect $1 fs mkdir lib
mpremote connect $1 fs mkdir lib/sim76xx

echo "Installing common libraries"
mpremote connect $1 mip install github:mchobby/esp8266-upy/LIBRARIAN


echo "Installing sim76xx  lib on Pico @ $1"
mpremote connect $1 fs cp lib/*.py :lib/
mpremote connect $1 fs cp lib/sim76xx/*.py :lib/sim76xx/

#echo "Copying main.py file"
#mpremote connect $1 fs cp main.py :main.py

echo " "
echo "Done!"
