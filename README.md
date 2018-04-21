# encoderd

A python daemon for monitoring the state of multiple rotary encoders connected to a raspberry pi
which transmit angles via mqtt protocol

## Dependencies

 * wiringPi (https://git.drogon.net/?p=wiringPi;a=summary)
 * wiringPi2-Python (https://github.com/Gadgetoid/WiringPi2-Python)
 * py-gaugette (https://github.com/guyc/py-gaugette)

 ```
 git clone git://git.drogon.net/wiringPi
 cd wiringPi
 sudo ./build
 cd ..

 sudo apt-get install python-setuptools python-dev
 git clone https://github.com/Gadgetoid/WiringPi2-Python.git
 cd WiringPi2-Python/
 sudo python setup.py install
 cd ..

 git clone git://github.com/guyc/py-gaugette.git
 cd py-gaugette
 sudo python setup.py install
 cd ..
 ```

## How to use

```Bash
$ git clone https://github.com/JGUINO/3205-codeurs-chariots.git
$ cd 3205-codeurs-chariots
$ ./codeursMQTTIO2.py start ANY
```

Settings are stored in `encoderd-settings.py`.
# 3205-codeurs-chariots
