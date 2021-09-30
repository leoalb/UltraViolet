import json
import subprocess
import time
import sys
from MaxiNet.Frontend import maxinet
from MaxiNet.Frontend.container import Docker
from mininet.topo import Topo
from mininet.node import OVSSwitch

with open("/usr/local/share/MaxiNet/dev/tempVioletfiles/infra-config-new2.json") as f:
    dataConfig = json.load(f)

with open("/usr/local/share/MaxiNet/dev/tempVioletfiles/device_types.json") as f:
    deviceConfig = json.load(f)

with open("/usr/local/share/MaxiNet/dev/tempVioletfiles/vm_types.json") as f:
    vmType = json.load(f)

# Dict to maintain Container BW and Latency 
nwConfig = {}

deviceTypes = {}

def get_distribution(dataConfig):
    fog = {}
    for key, value in dataConfig["infra_config"]["devices"].items():
        if key == "Fog":
            fog_temp = list(dataConfig["infra_config"]["devices"]["Fog"].keys())
            for fog_i in fog_temp:
                fog[fog_i] = []
                deviceTypes[fog_i] = dataConfig["infra_config"]["devices"]["Fog"][fog_i]["device_type"]
        if key == "Edge":
            edge_temp = list(dataConfig["infra_config"]["devices"]["Edge"].keys())
            for edge_i in edge_temp:
                ed_dom = edge_i.split("-")[1][0]
                fog_str = "Fog-" + ed_dom
                fog[fog_str].append(edge_i)
                deviceTypes[edge_i] = dataConfig["infra_config"]["devices"]["Edge"][edge_i]["device_type"]
    return (len(dataConfig["infra_config"]["devices"]["Fog"]), len(dataConfig["infra_config"]["devices"]["Edge"]), fog)

(fog_len, edge_len, config) = get_distribution(dataConfig)

print(config)

# Topology Creation

topo = Topo()

metaFog = {}
metaEdge = {}
metaSwitch = {}


for i in range(0, len(list(config.keys()))):
    fog = list(config.keys())[i]
    # add global switch for the fog to connect public network
    print("Creating Public Networks")
    metaSwitch["global-"+fog] = {}
    metaSwitch["global-"+fog]["id"] = "s100"+str(i)
    metaSwitch["global-"+fog]["topo"] = topo.addSwitch(metaSwitch["global-"+fog]["id"])
    metaSwitch["global-"+fog]["bw"] = dataConfig["infra_config"]["public_networks"]["global"]["bw"]
    metaSwitch["global-"+fog]["latency"] = dataConfig["infra_config"]["public_networks"]["global"]["latency"]+"ms"
    #print("Public Network Config -> " +  str(metaSwitch["global-"+fog]))


    # AddHost for Fogs
    metaFog[fog] = {}
    # Provide IP
    metaFog[fog]["ip"] = "10.2."+str(i//255)+"."+str(i%255+1)
    # Get req. Container Memory
    mem_req = deviceConfig[deviceTypes[fog]]["memory_mb"] + "m"
    # Get host Mount 
    mountSites = deviceConfig[deviceTypes[fog]]["host_mount"].split(",")
    # print(fog, ": ", mountSites)
    # Get host Image 
    hostImage = deviceConfig[deviceTypes[fog]]["docker_image"]
    metaFog[fog]["topo"] = topo.addHost(fog, cls=Docker, ip=metaFog[fog]["ip"], dimage=hostImage, mem_limit=mem_req, volumes=mountSites)
    print(fog + " created")
    
    

    # add a switch for each fog's private network
    print("Creating "+fog+"'s Private Network")
    metaSwitch[fog] = {}
    metaSwitch[fog]["id"] = "s"+str(i+1)
    metaSwitch[fog]["topo"] = topo.addSwitch(metaSwitch[fog]["id"])
    metaSwitch[fog]["bw"] = dataConfig["infra_config"]["private_networks"][fog+"-private"]["bw"]
    metaSwitch[fog]["latency"] = dataConfig["infra_config"]["private_networks"][fog+"-private"]["latency"]+"ms"
    print(fog+"'s Network -> " + str(metaSwitch[fog]))
    
    
    # Checking Fog Device Max Outgoing BW (Public)
    if int(deviceConfig[deviceTypes[fog]]["nic_out_bw_mbps"]) < int(metaSwitch["global-"+fog]["bw"]):
        bw_ = deviceConfig[deviceTypes[fog]]["nic_out_bw_mbps"] + "m"
    else:
        bw_ = metaSwitch["global-"+fog]["bw"] + "m"

    #Checking Fog Device Max Outgoing BW (Private)
    if int(deviceConfig[deviceTypes[fog]]["nic_out_bw_mbps"]) < int(metaSwitch[fog]["bw"]):
        bw_2 = deviceConfig[deviceTypes[fog]]["nic_out_bw_mbps"] + "m"
    else:
        bw_2 = metaSwitch[fog]["bw"] + "m"

    # add Link to public network
    print("Adding "+fog+" to its public network")
    topo.addLink(metaFog[fog]["topo"], metaSwitch["global-"+fog]["topo"], bw = bw_, delay = metaSwitch["global-"+fog]["latency"])
    # add Link to private network
    print("Adding "+fog+" to its private network")
    topo.addLink(metaFog[fog]["topo"], metaSwitch[fog]["topo"], intfName1=fog+"-eth1", params1={'ip':'10.1.200/8'}, bw = bw_2, delay = metaSwitch[fog]["latency"])

    # Link between global switches
    if(i):
        fog_previous = list(config.keys())[i-1]
        topo.addLink( metaSwitch["global-"+fog_previous]["topo"], metaSwitch["global-"+fog]["topo"], bw = bw_, delay = metaSwitch["global-"+fog]["latency"])


    nwConfig[fog] = {}

    nwConfig[fog]["intf0"] = {}
    nwConfig[fog]["intf0"]["ip"] = metaFog[fog]["ip"]
    nwConfig[fog]["intf0"]["bw"] = bw_
    nwConfig[fog]["intf0"]["latency"] = metaSwitch["global-"+fog]["latency"]

    nwConfig[fog]["intf1"] = {}
    nwConfig[fog]["intf1"]["ip"] = "10.1.200.0"
    nwConfig[fog]["intf1"]["bw"] = bw_2
    nwConfig[fog]["intf1"]["latency"] = metaSwitch[fog]["latency"]

    # AddHost for Edges
    print("Creating Edges for "+fog)
    for j in range(0, len(config[fog])):
        edge = config[fog][j]
        metaEdge[edge] = {}
        # Provide IP
        metaEdge[edge]["ip"] = "10.1."+str(j//255)+"."+str(j%255)
        # Store req. Container Memory
        mem_req = deviceConfig[deviceTypes[edge]]["memory_mb"] + "m"
        # Add host Mount 
        mountSites = deviceConfig[deviceTypes[edge]]["host_mount"].split(",")
        # print(edge, ": ", mountSites)
        # Get host Image 
        hostImage = deviceConfig[deviceTypes[edge]]["docker_image"]
        metaEdge[edge]["topo"] = topo.addHost(edge, cls=Docker, ip=metaEdge[edge]["ip"], dimage=hostImage, mem_limit=mem_req, volumes=mountSites)
        print(edge+" created")
        # add Links to private network
        print("Adding "+edge+" to "+fog+"'s private network")

        #Checking Edge Device Max Outgoing BW (Private)
        if int(deviceConfig[deviceTypes[edge]]["nic_out_bw_mbps"]) < int(metaSwitch[fog]["bw"]):
            bw_2 = deviceConfig[deviceTypes[edge]]["nic_out_bw_mbps"] + "m"
        else:
            bw_2 = metaSwitch[fog]["bw"] + "m"
        topo.addLink(metaEdge[edge]["topo"], metaSwitch[fog]["topo"], bw = bw_2, delay = metaSwitch[fog]["latency"])

        nwConfig[edge] = {}
        nwConfig[edge]["intf0"] = {}
        nwConfig[edge]["intf0"]["ip"] = metaEdge[edge]["ip"]
        nwConfig[edge]["intf0"]["bw"] = bw_2
        nwConfig[edge]["intf0"]["latency"] = metaSwitch[fog]["latency"]

    with open("/container/UVnwConfig.json", "w") as outfile: 
        json.dump(nwConfig, outfile)



cluster = maxinet.Cluster()
exp = maxinet.Experiment(cluster, topo, switch=OVSSwitch)
exp.setup()

try:
    print("Waiting 3 secs to converge")
    time.sleep(3)
    
    # Re-initailize fog's public connections
    print(metaFog)
    print(metaEdge)

    vm_coremark = int(vmType["m4.10xl"]["coremark"])
    # run the below to command to get number of cpus
    #cpu = int(subprocess.run(['nproc', '--all'], stdout=subprocess.PIPE).stdout.decode('utf-8'))
    cpu = int(vmType["m4.10xl"]["core_count"])

    for fog in metaFog:
        fog_node = exp.get_node(fog)

        strg = "ifconfig"+" "+fog+"-eth0"+" "+metaFog[fog]["ip"]+" "+"netmask 255.255.255.0"
        fog_node.cmd(strg)

        ips = exp.get_node("Fog-1").cmd("ifconfig -a | awk '/(cast)/ { print $2 }' | cut -d':' -f2")
        ip_list = ips.replace("'", "").split("\n")
        #print(ip_list)

        intfString = "ifconfig | grep \"" + "Fog-1" + "\" | awk {'print $1'}"
        intfs = exp.get_node("Fog-1").cmd(intfString)
        intfs_list = intfs.replace("'", "").split("\n")
        #print(intfs_list)



        #print(fog, " Volumes = " , fog_node.volumes)
        
        # Cpu limit is set after the containers are created, cos we dont know where the containers will be placed.
        container_coremark = int(deviceConfig[deviceTypes[fog]]["coremark"])
        cpu_part = (container_coremark / vm_coremark) * cpu
        cpu_quota = int(cpu_part * 100000)
        #print("C_CM - ", container_coremark, ", V_CM - ", vm_coremark, ", cpu - ", cpu, ", cpu_part - ", cpu_part, ", cpu_quota - ", cpu_quota)
        fog_node.updateCpuLimit(cpu_period=100000, cpu_quota=cpu_quota)
        #print(fog_node.cgroupGet('cpus', resource='cpuset'))
        print(fog, " resources = " , fog_node.resources)
        print(fog, " volumes = " , fog_node.volumes)
        print()

    for edge in metaEdge:
        edge_node = exp.get_node(edge)
        container_coremark = int(deviceConfig[deviceTypes[edge]]["coremark"])
        cpu_part = (container_coremark / vm_coremark) * cpu
        cpu_quota = int(cpu_part * 100000)
        edge_node.updateCpuLimit(cpu_period=100000, cpu_quota=cpu_quota)
        print(edge, " resources = " , edge_node.resources)
        print(edge, " volumes = " , edge_node.volumes)
        print()

    # see configs
   # print(exp.get_node("Fog-1").cmd("ifconfig"))
   # print(exp.get_node("Fog-2").cmd("ifconfig"))
    
    # pings
   # print("Fog-1 -> Fog-2")
   # print(exp.get_node("Fog-1").cmd("ping -c 3 10.0.0.2"))
    
   # print("Edge-1.1 -> Fog-1")
   # print(exp.get_node("Edge-1.1").cmd("ping -c 3 10.0.2.0"))

   # print("Edge-1.2 -> Edge-1.1")
   # print(exp.get_node("Edge-1.2").cmd("ping -c 3 10.0.1.0"))

   # print("Edge-2.1 -> Fog-1")
   # print(exp.get_node("Edge-2.1").cmd("ping -c 3 10.0.0.1"))

   # print("Edge-2.2 -> Edge-2.1")
   # print(exp.get_node("Edge-2.2").cmd("ping -c 3 10.0.1.0"))


   

    exp.CLI(locals(), globals())
finally:
    exp.stop()




