![Action Shot](/images/display.jpg)

# Kindlomino: A 'Now Playing' viewer for Volumio on a jailbroken Kindle

<p align="center">
<a href="https://pdm.fming.dev"><img alt="pdm: managed" src="https://img.shields.io/badge/pdm-managed-blueviolet"></a>
<a href="https://github.com/psf/black"><img alt="Code style: black" src="https://img.shields.io/badge/code%20style-black-000000.svg"></a>
</p>

Code and instructions for an easy-on-the-eye ePaper display that talks to a kind-to-the-ear, bit-perfect music player. All of the musical heavy lifting is done by [Volumio](https://volumio.com/en/get-started/). The code sets up a socket connection, listens for changes and updates the information displayed on a jailbroken Kindle.

### References
This project is based on the original [palomino project](https://github.com/veebch/palomino) and [this blog post](https://matthealy.com/kindle?utm_source=pocket_mylist).

### Logic of the script
The `kindlomino.py` script is using the [socketIO](https://python-socketio.readthedocs.io/en/latest/index.html) library to listen to changes in the track information provided by the Volumio server. The information is then converted into a PNG with the respective resolution of the kindle display. This image is send to the kindle with `scp` using a USB network connection. After that the kindle native tool `eips` is used to display the image, which is triggered using `ssh`. Admittedly a bit hacky, but it gets the job done :)


## Hardware
**Volumio server**:
This is covered in detail elsewhere, but the **tl;dr** is

- Pi Zero2 and [JustBoom Digi Zero pHAT ](https://shop.justboom.co/collections/raspberry-pi-audio-boards/products/justboom-digi-zero-phat)

**Track Viewer**:
- Pi Zero2 (or essentially any recent Pi; the script can also be run on the Pi that is running the Volumio server itself)
- [Kindle Touch (Kindle 5, 600x800 px)](https://wiki.mobileread.com/wiki/Kindle_Touch) or any other Kindle that can be jailbroken to enable USB networking.


## Prerequisites
- A Working Volumio server on your LAN
- A Pi Zero running Raspbian
- Kindle that can be jailbroken


## Preparation of the Kindle
**DISCLAIMER:** When attempting a jailbreak you may brick your device. Do at your own risk.

This is a short overview which is specific to the Kindle Touch with firmware version between 5.0.x and 5.4.4.2 to install the jailbreak and enable USB networking. However, it is also possible to do with many other models and frmware versions. For more information it is recommended to dig into the mobileread wiki and forum. The most important point of entries are [here](https://wiki.mobileread.com/wiki/Prefix_Index), [here](https://wiki.mobileread.com/wiki/K5_Index), and [here](https://wiki.mobileread.com/wiki/Kindle_Touch_Hacking?utm_source=pocket_mylist). All the important downloads are compiled in [NiLuJe's snapshot thread](https://www.mobileread.com/forums/showthread.php?t=225030).

### Steps:
1. Install jailbreak (detailed info [here](https://www.mobileread.com/forums/showthread.php?t=186645))
    1. Connect your Kindle to your PC
    1. Download the `K5 JailBreak` package from [here](https://www.mobileread.com/forums/showthread.php?t=225030). Extract the content of the download. In the `JailBreak` dir you will find a `kindle-5.4-jailbreak.zip`. The content of this zip needs to be extracted and copied to the root diectory of the Kindle.
    1. Eject and unplug Kindle
    1. On Kindle go to **Home** -> **Menu** -> **Settings** -> **Menu** -> **Update Your Kindle**. Note that the updater won't run which is normal, but the info `**JAILBREAK**` will appear.
1. Install Jailbreak hotfix (detailed info [here](https://www.mobileread.com/forums/showpost.php?p=3004892&postcount=1597))
    1. Reconnect Kindle to PC
    1. Download and extract the `K5 JailBreak Hotfix` package from [here](https://www.mobileread.com/forums/showthread.php?t=225030)
    1. Copy `Update_jailbreak_hotfix_1.16.N_install.bin` to the root directory of the Kindle
    1. Eject and unplug Kindle
    1. On Kindle go to **Home** -> **Menu** -> **Settings** -> **Menu** -> **Update Your Kindle** and the update should run successfully
1. Install KUAL to be able to install extensions (detailed info [here](https://www.mobileread.com/forums/showthread.php?t=203326))
    1. Reconnect Kindle to PC
    1. Download the package `KUAL` from [here](https://www.mobileread.com/forums/showthread.php?t=225030) and extract
    1. Place the `KUAL-KDK-2.0.azw2` file in the `documents/` directory of the Kindle
    1. Eject and unplug Kindle
    1. KUAL should now appear in the Kindle library
1. Add MRPI as KUAL extension (detailed info [here](https://www.mobileread.com/forums/showthread.php?t=251143) and [here -> section KUAL extensions](https://www.mobileread.com/forums/showthread.php?t=203326))
    1. Reconnect Kindle to PC
    1. Download `MR Package Installer` from [here](https://www.mobileread.com/forums/showthread.php?t=225030)
    1. Extract and copy the `extensions` and the `mrpackages` directories into the Kindle root
1. Install USBNewtork using MRPI (detailed info [here](https://www.mobileread.com/forums/showthread.php?t=251143))
    1. Download `USBNetwork Hack` from [here](https://www.mobileread.com/forums/showthread.php?t=225030) and extract the content. Then copy the `Update_usbnet_0.22.N_install_touch_pw.bin` file into the `mrpackages` directory created in step 4.3
    1. Eject and unplug Kindle
    1. Open KUAL from the library and click the `Install MR Packages` in the KUAL Helper menu
1. Finally to enable USB networking, on the home screen of your kindle enter `;un` in the search bar and press enter

**Note:** it might be a good idea to turn off WiFi on the Kindle to prevent OTA updates to revert the jailbreak.

## Connecting to the Kindle from the Pi
**Note:** Default configuration of the Pi and the Kindle are assumed here and the IPs 192.168.15.201 (Pi as host) and 192.168.15.244 (Kindle) are used and expected by kindlomino.py.

* Connect the Kindle to te Pi via USB

* Being logged into the Raspberry Pi you want to use to control the Kindle, open the terminal and type: `ifconfig usb0 del 192.168.15.201`

* The output of `ifconfig` should look similar to this:
```
usb0:0: flags=4163<UP,BROADCAST,RUNNING,MULTICAST>  mtu 1500
        inet 192.168.15.201  netmask 255.255.0.0  broadcast 169.254.255.255
        ether XX:XX:XX:XX:XX:XX  txqueuelen 1000  (Ethernet)
```

*  Then try to connect to the Kindle: `ssh root@192.168.15.244`. You can then connect by entering any password and even an empty one. **Note** that to be able to connect with any password you might need to turn off WiFi on the Kindle.

* If the last step worked we need to write this configuration on every boot of the Raspberry Pi. To do that add the following line into `/etc/rc.local`:
```
(sleep 60; ifconfig usb0 del 192.168.15.201)&
``` 


## Installation on the Pi

All of this takes place on dedicated Pi Zero2 or the Pi Zero2 running the volumio server. 

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
python3 kindlomino.py
```
After a few seconds, the screen will show the track currently playing on your Volumio server.

## Add Autostart

Once you've got a working instance of the code, you will probably want it to start automatically every time you power up. You can use systemd to start the code as a service on boot.

```
cat <<EOF | sudo tee /etc/systemd/system/kindlomino.service
[Unit]
Description=kindlomino
After=network.target

[Service]
ExecStart=/usr/bin/python3 -u /home/pi/kindlomino/kindlomino.py
WorkingDirectory=/home/pi/kindlomino/
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
sudo systemctl enable kindlomino.service
sudo systemctl start kindlomino.service

sudo reboot
```
## Licence

GNU GENERAL PUBLIC LICENSE Version 3.0
 
