#!/bin/bash

if [ "$EUID" -ne 0 ]
  then echo "Please run as root"
  exit
fi

spinner() {
    local pid=$1
    local delay=0.1
    local spinstr='|/-\'
    while [ "$(ps a | awk '{print $1}' | grep $pid)" ]; do
        local temp=${spinstr#?}
        printf " [%c]  " "$spinstr"
        local spinstr=$temp${spinstr%"$temp"}
        sleep $delay
        printf "\b\b\b\b\b\b"
    done
    printf "    \b\b\b\b"
}

echo "Installing to system"
echo ""
echo "Copying files..."
mkdir -p /opt/manifest-to-dependencies
copy_files() {
    cp -R * /opt/manifest-to-dependencies/
}
copy_files &
pid=$!
spinner $pid
wait $pid
echo "Files copied"
cd /opt/manifest-to-dependencies
echo ""
echo "Installing dependencies"
apt install python3 python-is-python3 python3-pip python3-venv
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
deactivate
echo ""
echo "Creating system service"
cp manifest-to-dependencies.service /etc/systemd/system/manifest-to-dependencies.service
systemctl daemon-reload
echo "System service created"
echo ""
sleep .5
echo "Start service with:"
echo "systemctl start manifest-to-dependencies.service"
sleep .3
echo "Enable start on boot with:"
echo "systemctl enable manifest-to-dependencies.service"
