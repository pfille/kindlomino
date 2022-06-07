[![Action Shot](/images/display.jpg)](https://youtu.be/7x2k6CjCG04)

# Kindlomino: A high definition ePaper 'Now Playing' viewer For Volumio on a jailbroken Kindle
[![pdm-managed](https://img.shields.io/badge/pdm-managed-blueviolet)](https://pdm.fming.dev)

Code for an easy-on-the-eye ePaper display that talks to a kind-to-the-ear, bit-perfect music player. All of the musical heavy lifting is done by [Volumio](https://github.com/volumio/Volumio2). The code sets up a socket connection, listens for changes and updates the information displayed on a jailbroken kindle.

## References
This project is based on the original [palomino project](https://github.com/veebch/palomino) and [this blog post](https://matthealy.com/kindle?utm_source=pocket_mylist). The idea is to generate an png image with the now playing information that can then be displayed on the Kindle.

## Hardware
**Volumio server**:
This is covered in detail elsewhere, but the **tl;dr** is

- Pi Zero2 and [JustBoom Digi Zero pHAT ](https://shop.justboom.co/collections/raspberry-pi-audio-boards/products/justboom-digi-zero-phat)

**Track Viewer**:
- Pi Zero2 (or essentially any newer Pi; the script can also be run on the Pi that is running the Volumio server itself)
- [Kindle Touch (Kindle 5, 600x800 px)](https://wiki.mobileread.com/wiki/Kindle_Touch) or any other Kindle that can be jailbroken to enable USB networking.


## Prerequisites
- A Working Volumio server on your LAN
- A Pi Zero running Raspbian
- Kindle that can be jailbroken

## Installation 

All of this takes place on the dedicated Pi Zero2 or the Pi Zero2 running the volumio server. 

From your home directory, clone the repository 

```
git clone git@github.com:pfille/kindlomino.git
cd kindlomino
```

then install the required modules using `python3 -m pip install -r requirements.txt` then 
move to the directory and copy the example config file and tailor to your needs:
```
cp config_example.yaml config.yaml
```
You can then edit `config.yaml` file to set the name of your server.
Once that's done, you can run the code using the command:
```
python3 palomino.py
```
After a few seconds, the screen will show the track currently playing on you Volumio server.

## Add Autostart

Once you've got a working instance of the code, you will probably want it to start automatically every time you power up. You can use systemd to start the code as a service on boot.

```
cat <<EOF | sudo tee /etc/systemd/system/palomino.service
[Unit]
Description=palomino
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u /home/pi/palomino/palomino.py
WorkingDirectory=/home/pi/palomino/
StandardOutput=inherit
StandardError=inherit
Restart=always
User=pi

[Install]
WantedBy=multi-user.target
EOF
```
Now, simply enable the service you just made and reboot...
```  
sudo systemctl enable palomino.service
sudo systemctl start palomino.service

sudo reboot
```
## Licence

GNU GENERAL PUBLIC LICENSE Version 3.0
 
