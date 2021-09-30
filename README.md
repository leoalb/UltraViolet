# UltraViolet
The next version of VIoLET

"Digital twin" for IoT cyber-infrastructure

## UltraViolet installation

## Automatic Installation 
> run the install script


## manual installation 

### Set Python3 as default
> sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10
### 1. Install dependencies
> sudo apt-get install git autoconf screen cmake build-essential sysstat python3-matplotlib uuid-runtime python3-pip -y

### 2. Install  ContainerNet

> sudo apt-get install ansible aptitude -y

> cd ~/Documents/UltraViolet

> cd containernet/ansible && sudo ansible-playbook -i "localhost," -c local install.yml

> cd .. && sudo make install

### 3. Install metis
> cd ~/Documents/UltraViolet

> cd metis-5.1.0

> make config

> make

> sudo make install

### 4. Install Pyro4
> pip3 install Pyro4

### 5. Install MaxiNet
> cd ~/Documents/UltraViolet

> cd MaxiNet3

> sudo make install

### 6. Set up cluster and configure MaxiNet
Repeat above (1-5) steps for every pc you want to use as a worker or frontend.

On the frontend machine copy the MaxiNet-cfg-sample file to ~/.MaxiNet.cfg and edit the file.
> cp share/MaxiNet.cfg ~/.MaxiNet.cfg

> vi ~/.MaxiNet.cfg

Please note that every worker connecting to the MaxiNet Server will need an respective
entry in the configuration file, named by its hostname and containing its ip.
Although UltraViolet tries to guess the IP of the worker if not found in the
configuration file.

More details [here](./Maxinet3/SetupConfigFile.txt).




### 7. Start MaxiNet
On the frontend machine call
> sudo MaxiNetFrontendServer

On every worker machine call
> sudo MaxiNetWorker

You should see that the workers are connecting to the frontend.

POX
> git clone https://github.com/noxrepo/pox.git

Start an OpenFlow controller for example by calling
> cd ~/documents/pox/ && python3 pox.py forwarding.l2_learning

Now run in a new terminal,
> python3 /usr/local/share/MaxiNet/examples/simplePing.py

> python3 /usr/local/share/MaxiNet/examples/testconfig.py

Congratulations, you just set up your own SDN!


### HELP
Find examples code in Maxinet3/MaxiNet/Frondend/examples

To read violet file, read the pythonfile in Maxinet3/MaxiNet/Frontend/dev

Container related [help](./help1.md)