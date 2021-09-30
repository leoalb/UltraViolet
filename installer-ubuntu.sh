echo "UltraViolet installer for UbuntuOS"
echo ""

if [ "$1" == "--help" ] || [ "$1" == "-h" ]
then
    echo ""
    echo "Invoke without any parameter to interactively install UltraViolet and its dependencies."
    exit 0
fi

echo "----------------"
echo ""
echo "Installing UltraViolet"

echo "Running Apt Update"
sudo apt update -y

echo "Set Python3 as default"
sudo update-alternatives --install /usr/bin/python python /usr/bin/python3 10

echo "Installing required dependencies"
sudo apt-get install git autoconf screen cmake build-essential sysstat python3-matplotlib uuid-runtime python3-pip vim ansible aptitude net-tools -y

echo "Installing Containernet"
cd containernet/
sudo ansible-playbook -i "localhost," -c local ansible/install.yml

sudo make install
cd ..

echo "Installing Metis"
cd metis-5.1.0
make config
make
sudo make install
cd ..


echo "Installing Pyro4"
pip3 install Pyro4

echo "Installing MaxiNet3"
cd MaxiNet3
sudo make install
cp share/MaxiNet.cfg ~/.MaxiNet.cfg
cd ..

echo "UltaViolet was installed Successfully"
