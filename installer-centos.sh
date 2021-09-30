echo "UltraViolet installer for CentOS"
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

echo "Running YUM Update"
sudo yum update -y

echo "Installing Python3"
sudo yum install -y python3

echo "Installing required dependencies"
sudo yum install -y epel-release
sudo yum install -y autoconf screen cmake build-essential sysstat python3-matplotlib uuid-runtime python3-pip vim git ansible

echo "Installing Containernet"
cd containernet/
sudo ansible-playbook -i "localhost," -c local ansible/install_centos.yml

sudo make install
cd ..

echo "Installing Metis"
sudo yum install -y metis

echo "Installing Pyro4"
pip3 install Pyro4

echo "Installing MaxiNet3"
cd Maxinet3
sudo make install
cp share/MaxiNet.cfg ~/.MaxiNet.cfg
cd ..

echo "UltaViolet was installed Successfully"
