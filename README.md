# decentral-air-quality-monitoring-server
server service of decentral-air-quality-monitoring prject

## How to set up the Server
* download archive
* unpack archive

`$ sudo tar -xzvf particle-release-1-0.tar.gz -C /opt/ ` 

`$ useradd particle`

`$ sudo mkdir /var/log/particle`

`$ cd /opt/particle-release-1-0`

`$ virtualenv -p python3 venv`

`$ source venv/bin/activate`

`$ pip3 install -r requirements.txt`

`$ ln -s /opt/particle-release-1-0/systemd/particle-ttn.service /etc/systemd/system/particle-ttn.service`

`$ ln -s /opt/particle-release-1-0/systemd/particle-wlan.service /etc/systemd/system/particle-wlan.service`

* edit the files in the settings directory

`$ systemctl daemon-reload`

`$ systemctl start particle-ttn && systemctl enable particle-ttn`

`$ systemctl start particle-wlan && systemctl enable particle-wlan`