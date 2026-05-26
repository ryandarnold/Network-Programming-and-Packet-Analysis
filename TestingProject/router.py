#!/usr/bin/python
from mininet.topo import Topo
from mininet.net import Mininet
from mininet.node import Node
from mininet.log import setLogLevel, info
from mininet.cli import CLI

class LinuxRouter(Node):
    def config(self, **params):
        super(LinuxRouter, self).config(**params)
        self.cmd('sysctl net.ipv4.ip_forward=1')

    def terminate(self):
        self.cmd('sysctl net.ipv4.ip_forward=0')
        super(LinuxRouter, self).terminate()

class NetworkTopo(Topo):
    def build(self, **_opts):
        #Add 3 routers in three different subnets
        rA = self.addHost('rA', cls=LinuxRouter, ip='20.10.172.129/26') #the subnet to the switch?
        rB = self.addHost('rB', cls=LinuxRouter, ip='20.10.172.1/25') #the subnet to the switch?
        rC = self.addHost('rC', cls=LinuxRouter, ip='20.10.172.193/27')
        #Add 3 switches
        s1 = self.addSwitch('s1')
        s2 = self.addSwitch('s2')
        s3 = self.addSwitch('s3')

        #Add host-like switch links in the same subnet
        self.addLink(s1, rA, intfName2='rA-eth1', params2={'ip':'20.10.172.129/26'}) # connects s1 to r1 via r1's NIC port: r1-eth1
        self.addLink(s2, rB, intfName2='rB-eth1', params2={'ip':'20.10.172.1/25'})
        self.addLink(s3, rC, intfName2='rC-eth1', params2={'ip':'20.10.172.193/27'})

        #Add router-router link in a new subnet for the router-router connection
        self.addLink(rA, rB, intfName1='rA-eth2', intfName2='rB-eth2', params1={'ip':'20.10.100.1/24'}, params2={'ip':'20.10.100.2/24'}) #router to router connection for params1/2
        self.addLink(rB, rC, intfName1='rB-eth3', intfName2='rC-eth3', params1={'ip':'20.10.100.3/24'}, params2={'ip':'20.10.100.4/24'})
        self.addLink(rC, rA, intfName1='rC-eth4', intfName2='rA-eth4', params1={'ip':'20.10.100.5/24'}, params2={'ip':'20.10.100.6/24'})

        #Adding hosts specifying the default route
        h1 = self.addHost(name='h1', ip='20.10.172.130/26', defaultRoute='via 20.10.172.129') # default route is the route from host to router
        h2 = self.addHost(name='h2', ip='20.10.172.131/26', defaultRoute='via 20.10.172.129') #ip is the IP address of the host

        h3 = self.addHost(name='h3', ip='20.10.172.2/25', defaultRoute='via 20.10.172.1')
        h4 = self.addHost(name='h4', ip='20.10.172.3/25', defaultRoute='via 20.10.172.1')

        h5 = self.addHost(name='h5', ip='20.10.172.194/27', defaultRoute='via 20.10.172.193')
        h6 = self.addHost(name='h6', ip='20.10.172.195/27', defaultRoute='via 20.10.172.193')

        # Add host-switch links
        self.addLink(h1, s1)
        self.addLink(h2, s1)

        self.addLink(h3, s2)
        self.addLink(h4, s2)

        self.addLink(h5, s3)
        self.addLink(h6, s3)

def run():
    topo = NetworkTopo()
    net = Mininet(topo=topo)

    # Add routing for reaching networks that aren't directly connected
    info(net['rA'].cmd("ip route add 20.10.172.0/25 via 20.10.100.2 dev rA-eth2"))  # adding network address NOT the router subnet address
    info(net['rA'].cmd("ip route add 20.10.172.192/27 via 20.10.100.5 dev rA-eth4"))

    info(net['rB'].cmd("ip route add 20.10.172.128/26 via 20.10.100.1 dev rB-eth2"))
    info(net['rB'].cmd("ip route add 20.10.172.192/27 via 20.10.100.4 dev rB-eth3"))

    info(net['rC'].cmd("ip route add 20.10.172.0/25 via 20.10.100.3 dev rC-eth3"))
    info(net['rC'].cmd("ip route add 20.10.172.128/26 via 20.10.100.6 dev rC-eth4"))

    net.start()
    CLI(net)
    net.stop()

if __name__ == '__main__':
    setLogLevel('info')
    run()