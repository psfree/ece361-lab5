#!/usr/bin/python

import sys
import pdb
import re # For regex

import ryu_ofctl
from ryu_ofctl import *

def main(macHostA, macHostB):
    print "Installing flows for %s <==> %s" % (macHostA, macHostB)

    ##### FEEL FREE TO MODIFY ANYTHING HERE #####
    try:
        pathA2B = dijkstras(macHostA, macHostB)
        installPathFlows(macHostA, macHostB, pathA2B)
    except:
        raise


    return 0

# Installs end-to-end bi-directional flows in all switches
def installPathFlows(macHostA, macHostB, pathA2B):
    ##### YOUR CODE HERE #####
    pdb.set_trace()
    for each in pathA2B:
        dpid = str(each['dpid']).zfill(16)
        port1 = each['in_port']
        port2 = each['out_port']
        act1 = ryu_ofctl.OutputAction(port1)
        act2= ryu_ofctl.OutputAction(port2)
        flow1 = ryu_ofctl.FlowEntry()
        flow1.dl_dst = macHostB
        flow1.in_port = port1
        flow1.addAction(act2)
        flow2 = ryu_ofctl.FlowEntry()
        flow2.dl_dst = macHostA
        flow2.in_port = port2
        flow2.addAction(act1)
        ryu_ofctl.insertFlow(dpid, flow1)
        ryu_ofctl.insertFlow(dpid, flow2)
    return

# Returns List of neighbouring DPIDs
def findNeighbours(dpid):
    if type(dpid) not in (int, long) or dpid < 0:
        raise TypeError("DPID should be a positive integer value")

    neighbours = []
    switchlinks = ryu_ofctl.listSwitchLinks(str(dpid).zfill(16))['links']
    for each in switchlinks:
        end1 = each['endpoint1']
        end2 = each['endpoint2']    
        if int(end1['dpid'])!=dpid:
            neighbours.append(each)

    return neighbours

# Calculates least distance path between A and B
# Returns detailed path (switch ID, input port, output port)
#   - Suggested data format is a List of Dictionaries
#       e.g.    [   {'dpid': 3, 'in_port': 1, 'out_port': 3},
#                   {'dpid': 2, 'in_port': 1, 'out_port': 2},
#                   {'dpid': 4, 'in_port': 3, 'out_port': 1},
#               ]
# Raises exception if either ingress or egress ports for the MACs can't be found
def dijkstras(macHostA, macHostB):

    # Optional helper function if you use suggested return format
    def nodeDict(dpid, in_port, out_port):
        assert type(dpid) in (int, long)
        assert type(in_port) is int
        assert type(out_port) is int
        return {'dpid': dpid, 'in_port': in_port, 'out_port': out_port}

    # Optional variables and data structures
    INFINITY = float('inf')
    distanceFromA = {} # Key = node, value = distance
    leastDistNeighbour = {} # Key = node, value = neighbour node with least distance from A
    pathAtoB = [] # Holds path information
    
    prev = {}
    dpidlist = ryu_ofctl.listSwitches()['dpids']
    inA = ryu_ofctl.getMacIngressPort(macHostA)
    inB = ryu_ofctl.getMacIngressPort(macHostB)
    assert inA is not None
    assert inB is not None
    portA = int(inA['port'])
    switchA = int(inA['dpid'])
    portB = int(inB['port'])
    switchB = int(inB['dpid'])   

    outlist = []
    if(switchA == switchB):
        d = {}
        d['dpid'] = switchA  
        d['in_port'] = portA
        d['out_port'] = portB
        pathAtoB.append(d)
        return pathAtoB
   
    for each in dpidlist:
        distanceFromA[each] = INFINITY
        leastDistNeighbour[each] = None
        if each==str(switchA).zfill(16):
            distanceFromA[each] = 0
    #pdb.set_trace()
    s = []
    while len(distanceFromA) > 0:
        minval = INFINITY
        dpid_sel = -1
        for each in dpidlist:
            if distanceFromA[each] <minval:
                minval = distanceFromA[each]
                dpid_sel = each
        #pdb.set_trace()
        if dpid_sel == -1:
            break
        dpidlist.remove(dpid_sel)
        if dpid_sel == str(switchB).zfill(16):
            s = []
            if leastDistNeighbour[dpid_sel] is not None or dpid_sel==switchA:
                tmp = dpid_sel
                s.append(tmp)
                while True:
                    out = leastDistNeighbour[tmp]
                    if out is None:
                        break
                    outlist.append(out)
                    tmp = out[2]
                    s.append(tmp)
                break
            else:
                #they are on the same node i.e h1 and h2
                print "lol"
        neighbours = findNeighbours(int(dpid_sel))
        LENGTH = 1
        for each in neighbours:
            alt = distanceFromA[dpid_sel] + LENGTH
            end1 = each['endpoint1']
            end2 = each['endpoint2']
            e1port=end1['port']
            e1dpid = end1['dpid']
            e2port=end2['port']
            if alt<distanceFromA[e1dpid]:
                distanceFromA[e1dpid] = alt
                d = [e1port, e2port, dpid_sel]
                leastDistNeighbour[e1dpid] = d
    d = {}
    s.reverse()
    outlist.reverse()
    pdb.set_trace()
    if not s or int(s[0])!= switchA:
        print "FAILLL"
        return pathAtoB

    linport = portA
    for each in outlist:
        d = {}
        d['in_port'] = linport
        d['out_port'] = each[1]
        d['dpid'] = int(each[2])
        linport = each[0]
        pathAtoB.append(d)
    d = {}
    d['dpid'] = int(switchB)
    d['in_port'] =linport
    d['out_port'] = portB
    pathAtoB.append(d)
    # Some debugging output
    print "leastDistNeighbour = %s" % leastDistNeighbour
    print "distanceFromA = %s" % distanceFromA
    print "pathAtoB = %s" % pathAtoB

    return pathAtoB



# Validates the MAC address format and returns a lowercase version of it
def validateMAC(mac):
    invalidMAC = re.findall('[^0-9a-f:]', mac.lower()) or len(mac) != 17
    if invalidMAC:
        raise ValueError("MAC address %s has an invalid format" % mac)

    return mac.lower()

if __name__ == '__main__':
    if len(sys.argv) != 3:
        print "This script installs bi-directional flows between two hosts"
        print "Expected usage: install_path.py <hostA's MAC> <hostB's MAC>"
    else:
        macHostA = validateMAC(sys.argv[1])
        macHostB = validateMAC(sys.argv[2])

        sys.exit( main(macHostA, macHostB) )
