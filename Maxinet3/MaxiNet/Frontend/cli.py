#!/usr/bin/python

from cmd import Cmd
import subprocess
import sys
import time
import traceback
import ast
import json
import os
from typing import NewType
from MaxiNet.Frontend.container import Docker


class CLI(Cmd):
    prompt = "UltraViolet> "

    helpStr = "You may also type '<hostname> <command>' to execute commands" +\
              " on maxinet hosts\n\texample: h1 ifconfig h1-eth1"

    def __init__(self, experiment, plocals, pglobals):
        self.experiment = experiment
        self.plocals = plocals
        self.pglobals = pglobals
        Cmd.__init__(self)
        while True:
            try:
                self.cmdloop()
                break
            except KeyboardInterrupt:
                print ("\nInterrupt")

    def emptyline(self):
        pass

    def do_help(self, s):
        "Print help"
        Cmd.do_help(self, s)
        if s is "":
            print (self.helpStr)

    def do_hosts(self, s):
        "Print all hostnames"
        h = ""
        for host in self.experiment.hosts:
            h = h + " " + host.name
        print (h)

    def do_workers(self, s):
        "Print all workers; worker id in brackets"
        h = ""
        for worker in self.experiment.cluster.worker:
            wid = self.experiment.hostname_to_workerid[worker.hn()]
            h = h + " " + worker.hn() + "[" + str(wid) + "]"
        print (h)

    def do_switches(self, s):
        "Print all switchnames; worker id in brackets"
        h = ""
        for switch in self.experiment.switches:
            wid = self.experiment.hostname_to_workerid[
                self.experiment.get_worker(switch).hn()
            ]
            h = h + " " + switch.name +\
                "[" + str(wid) + "]"
        print (h)

    def do_pingall(self, s):
        """Do ping between all hosts (or between one and all other hosts
        if host is given as parameter)
        """
        sent = 0.0
        received = 0.0
        if(len(s) == 0):
            for host in self.experiment.hosts:
                for target in self.experiment.hosts:
                    if(target == host):
                        continue
                    sys.stdout.write(host.name + " -> " + target.name)
                    sent += 1.0
                    if(host.pexec("ping -c1 " + target.IP())[2] != 0):
                        print (" X")
                    else:
                        received += 1.0
                        print ("")
        else:
            host = self.experiment.get(s)
            if(host is None):
                print ("Error: Node " + s + " does not exist")
            else:
                for target in self.experiment.hosts:
                    if(target == host):
                        continue
                    sys.stdout.write(host.name + " -> " + target.name)
                    sent += 1.0
                    if(host.pexec("ping -c1 " + target.IP())[2] != 0):
                        print (" X")
                    else:
                        received += 1.0
                        print ("")
        print ("*** Results: %.2f%% dropped (%d/%d received)" % \
                    ((1.0 - received / sent) * 100.0, int(received), int(sent)))

    def do_routes(self, s):
        """execute ip route in all switches
        """
        for sw in self.experiment.switches:
            print(sw.pexec("ip route"))

    def do_route(self, s):
        """execute ip route at switch
        """
        sp = s.split(" ")
        sw = sp[0]
        switch = self.experiment.get(sw)
        if(switch is None):
            print ("Error: Switch " + sw + " does not exist")
        else:
            out = switch.pexec("ip route")
            out = out[0].split('\n')
            for i in out:
                print (i)

    def do_ifconfig(self, s):
        """execute ifconfig at switch
        """
        sp = s.split(" ")
        sw = sp[0]
        switch = self.experiment.get(sw)
        if(switch is None):
            print ("Error: Switch " + sw + " does not exist")
        else:
            out = switch.pexec("ifconfig")
            out = out[0].split('\n')
            for i in out:
                print (i)

    def do_dpctl(self, s):
        "execute dpctl at switch"
        sp = s.split(" ")
        sw = sp[0]
        cmd = " ".join(sp[1:len(sp)])
        switch = self.experiment.get(sw)
        if(switch is None):
            print ("Error: Switch " + sw + " does not exist")
        else:
            print (switch.dpctl(cmd))

    def do_ip(self, s):
        "Print ip of host"
        node = self.experiment.get(s)
        if(node is None):
            print ("Error: Node " + s + " does not exist")
        else:
            print (node.IP())

    def do_py(self, s):
        "Execute Python command"
        cmd = s
        main = __import__("__main__")
        try:
            exec(cmd, self.pglobals, self.plocals)
        except Exception as e:
            traceback.print_exc()

    def do_xterm(self, s):
        "Start xterm on the list of given hosts (separated through spaces)"
        nodes = s.split()
        for node in nodes:
            if(self.experiment.get(node) is None):
                print ("Error: Node " + s + " does not exist")
            else:
                self.default(node + " xterm -title MaxiNet-" + node + " &")
                time.sleep(0.2)

    def do_addhost(self, s):
        "Add host to the topology at the run time. args -> <name, wid (optional), cls (optional), ip, dimage (optionl)>\n example-> addhost h10 wid=0 cls=Docker ip=10.0.0.3 dimage=ubuntu:trusty"
        cmd_list = s.split(" ")
       # print(cmd_list)
        ip = [s for s in cmd_list if "ip" in s]
        wid = [s for s in cmd_list if "wid" in s]
        cls = [s for s in cmd_list if "cls" in s]
        dimage = [s for s in cmd_list if "dimage" in s]

        if not len(ip):
            print("Ip address for host not provided.")
            return
        if len(dimage):
            if len(cls) == 0 or cls[0].split("=")[1]==None:
                print("cls is not set to Docker")
                return
            if len(wid):
                self.experiment.addHost(name=cmd_list[0], wid=wid[0].split("=")[1], cls=Docker, ip=ip[0].split("=")[1], dimage=dimage[0].split("=")[1])
            else:
                self.experiment.addHost(name=cmd_list[0], cls=Docker,ip=ip[0].split("=")[1], dimage=dimage[0].split("=")[1])
        else:
            if len(wid):
                self.experiment.addHost(name=cmd_list[0], wid=wid[0].split("=")[1], ip=ip[0].split("=")[1])
            else:
                self.experiment.addHost(name=cmd_list[0], ip=ip[0].split("=")[1])
    
    def do_addswitch(self, s):
        "Add Switch to the topology at run time. args -> <name, wid (optional)> \n example -> addswitch s10 wid=0"
        cmd_list = s.split(" ")
        wid = [s for s in cmd_list if "wid" in s]
        if len(wid):
            self.experiment.addSwitch(name=cmd_list[0], wid=wid[0].split("=")[1])
        else:
            self.experiment.addSwitch(name=cmd_list[0])

    def do_addlink(self, s):
        """ Add link to the topography at runtime.

        args -> <node1, node2, autoconf, bw (optional), delay (optional), intfname1 (optional), params1 (optional)>
        example -> addlink node1=f1 node2=f2 autoconf=true bw=25 delay=50ms intfname1=f1-eth1 params={'ip':'10.0.2/8'}

        """
        cmd_list = s.split(" ")
        node1 = [s for s in cmd_list if "node1" in s]
        node2 = [s for s in cmd_list if "node2" in s]
        port1 = [s for s in cmd_list if "port1" in s]
        port2 = [s for s in cmd_list if "port2" in s]
        autoconf = [s for s in cmd_list if "autoconf" in s]
        bw = [s for s in cmd_list if "bw" in s]
        delay = [s for s in cmd_list if "delay" in s]
        intfname1 = [s for s in cmd_list if "intfname1" in s]
        params1 = [s for s in cmd_list if "params1" in s]

        if len(node1) == 0 or len(node2) == 0:
            print("Provide host names where link will be attached")
            return
        
        if len(autoconf):
            if autoconf[0].split("=")[1] == "True" or autoconf[0].split("=")[1] == "true":
                autoconf = True
            else:
                autoconf = False

        if len(bw):
            bw = int(bw[0].split("=")[1])
            if len(delay):
                self.experiment.addLink(node1=node1[0].split("=")[1], node2=node2[0].split("=")[1], autoconf=autoconf, bw=bw, delay=delay[0].split("=")[1])
            else:
                 self.experiment.addLink(node1=node1[0].split("=")[1], node2=node2[0].split("=")[1], autoconf=autoconf, bw=bw)

        if len(intfname1):
            if not len(params1):
                print("Provide parameters for interface")
                return

        if len(params1):
            if not len(intfname1):
                print("Provide interface name")
                return
            params1 = ast.literal_eval(params1[0].split("=")[1])

            if len(bw):
                if len(delay):
                    self.experiment.addLink(node1=node1[0].split("=")[1], node2=node2[0].split("=")[1], autoconf=autoconf, intfname1=intfname1[0].split("=")[1], params1=params1, bw=bw, delay=delay[0].split("=")[1])
                else:
                    self.experiment.addLink(node1=node1[0].split("=")[1], node2=node2[0].split("=")[1], autoconf=autoconf, intfname1=intfname1[0].split("=")[1], params1=params1, bw=bw)
            else:
                    self.experiment.addLink(node1=node1[0].split("=")[1], node2=node2[0].split("=")[1], autoconf=autoconf, intfname1=intfname1[0].split("=")[1], params1=params1)


    def do_updatelink(self, s):
        """ Update Links at runtime.

        args -> <node>
        example -> updatelink node

        """
        cmd_list = s.split(" ")
        nodeIntfs = self.experiment.fetchHostLinks(cmd_list[0])
        #print(nodeIntfs)
        print("Select Interface -> ")
        intfs = nodeIntfs.split(",")
        intfs[0] = intfs[0][1:]
        intfs[-1] = intfs[-1][:-1]
        count = 1
        for intf in intfs:
            print(count, end =". ")
            print(intf)
            count += 1
        choiceintf = int(input("Choice: "))
        intfready = []
        intfready.append(cmd_list[0])
        intfready.append(choiceintf-1)
        selectedintfs = intfs[choiceintf-1]
        print("Set one of following \n1. bandwidth\n2. delay\n3. loss\n4. Link Up\n5. Link Down\nchoice - ", end = "")
        choice = int(input())
        if choice == 1 or choice == 2 or choice ==3:
            val = input("value : ")
            self.experiment.updateLink(intfready, choice, val)
        elif choice == 4:
            src = cmd_list[0]
            dst = selectedintfs.split(":")[1].split(">")[1].split("-")[0]
            self.experiment.configLinkStatus(src, dst, "up")
        elif choice == 5:
            src = cmd_list[0]
            dst = selectedintfs.split(":")[1].split(">")[1].split("-")[0]
            self.experiment.configLinkStatus(src, dst, "down")
        else:
            print("incorrect input")
            return 

    def do_exit(self, s):
        """Exit"""
        return "exited by user command"

    def do_EOF(self, s):
        """Exit on EOF (Ctrl+D)"""
        return self.do_exit(s)

    def do_quit(self, s):
        """Exit"""
        return self.do_exit(s)

    #add import os at top and the delete this comment
    def do_terminal(self, s):
        """Create a new Terminal"""
        subprocess.call(["gnome-terminal", "-x", "python /usr/local/lib/python3.6/dist-packages/MaxiNet-1.2-py3.6.egg/MaxiNet/Frontend/cli2.py  'Hi'"])

    def do_nwconfig(self, s):
        """View the Network configuration"""
        with open("/container/nwConfig.json") as f:
            nwConfig = json.load(f)
        file = open('/container/nwConfig.csv','w')
        line = "<Device Name>, <Interface>, <IP Addr>, <Bandwidth>, <Latency>\n"
        file.write(line) 
        for host_ in nwConfig.keys():
            for intf in nwConfig[host_]:
                line = host_ + "," + intf + "," + nwConfig[host_][intf]["ip"] + "," + nwConfig[host_][intf]["bw"] + "," + nwConfig[host_][intf]["latency"] + "\n"
                file.write(line)
        file.close()
        print("Network configuration file created at /container/nwConfig.csv")
        

    def do_uvexec(self, s):
        """Execute a command on multiple hosts.
        
        uvexec -x <command>   -> To run command on all hosts
        uvexec h1 h2 -x <command>  -> To run command on specified hosts

        """
        # split to get hosts and commands
        if "-x" not in s:
            print("Use -x flag to provide the command")
            return
        split1 = s.split("-x")
        if split1[0] == "":
            print("Executing on all hosts")
            for host in self.experiment.hosts:
                exe = host.pexec(split1[1].strip())
                if (exe[2] != 0):
                    choice = int(input(str(host.name) + ": Error Occured while executing command. press 1 to view, 0 to continue."))
                    if choice:
                        print("Details: ")
                        print(exe[0])
                        choice = int(input("Press 1 to exit, 0 to continue"))
                        if choice:
                            return
                        else:
                            continue
                    else:
                        continue
                else:
                    print(host.name, ": Successfully executed.")
        else:
            print("Executing on ", split1[0])
            for host in split1[0].strip().split(" "):
                host = host.strip()
                exe = host + " " + split1[1].strip()
                self.default(exe)




    
    


    def default(self, s):
        node = s[:s.find(" ")]
        cmd = s[s.find(" ") + 1:]
        node_wrapper = self.experiment.get(node)
        if(node_wrapper is None):
            # check if node is the name of a worker. if so, execute command on that worker
            if(node in self.experiment.hostname_to_workerid):
                worker = self.experiment.cluster.get_worker(node)
                # execute command on worker
                rcmd = worker.sshtool.get_ssh_cmd(targethostname=node,
                                           cmd=cmd,
                                           opts=["-t"])

                subprocess.call(rcmd)
            else:
                print ("Error: Node " + node + " does not exist")
        elif node_wrapper.is_docker():
            sys.stdout.write(node_wrapper.cmdPrint(cmd))
        else:
            blocking = True
            if cmd[-1] == "&":
                cmd = cmd[:-1]
                blocking = False
            pid = self.experiment.get_worker(self.experiment.get(node))\
                    .run_cmd("ps ax | grep \"bash.*mininet:" + node +
                             "$\" | grep -v grep | awk '{print $1}'").strip()
            sshtool = self.experiment.get_worker(self.experiment.get(node)).sshtool
            hn = self.experiment.get_worker(self.experiment.get(node)).hn()
            if self.experiment.get_worker(self.experiment.get(node))\
                    .tunnelX11(node):
                user = subprocess.check_output(
                        sshtool.get_ssh_cmd(targethostname=hn,
                                            cmd="echo $USER", opts=["-t"])
                       ).strip().decode(sys.stdout.encoding)
                opts=["-t","-X"]
                if not blocking:
                    opts.append("-n")
                xauthprefix = "/home/"
                if user == "root":
                    xauthprefix = "/"
                rcmd = sshtool.get_ssh_cmd(
                        targethostname=hn,
                        cmd="XAUTHORITY=" + xauthprefix + user + "/.Xauthority mnexec -a "
                            + pid + " " + cmd,
                        opts=opts
                       )
            else:
                rcmd = sshtool.get_ssh_cmd(targethostname=hn,
                                           cmd="mnexec -a " + pid + " " + cmd,
                                           opts=["-t"])
            if blocking:
                subprocess.call(rcmd)
            else:
                subprocess.Popen(rcmd)




