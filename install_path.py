#!/usr/bin/python

import sys
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
    #need to make 2 connections in opposite directions
    #for each dictionarly in the pathA2B list
    for each in pathA2B:
        dpid = str(each['dpid']).zfill(16) #make sure the dpid is in the right format
        port1 = each['in_port']
        port2 = each['out_port']
        #create 2 output actions with each of the ports
        act1 = ryu_ofctl.OutputAction(port1)
        act2= ryu_ofctl.OutputAction(port2)
        #create flow1 with dest B, inport=port1, action=port2
        flow1 = ryu_ofctl.FlowEntry()
        flow1.dl_dst = macHostB
        flow1.in_port = port1
        flow1.addAction(act2)
        #create flow2 with destA, inport=port2, action=port1
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
        #ensure that only entries with dpids that are different get added and no duplicates    
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
    
    #setup data
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
    #handle the case where start and endpoints are on the same switch i.e. h1 and h2
    if(switchA == switchB):
        d = {}
        d['dpid'] = switchA  
        d['in_port'] = portA
        d['out_port'] = portB
        pathAtoB.append(d)
        return pathAtoB
   
    #create a distance list and set all values to infinity except the start switch
    for each in dpidlist:
        distanceFromA[each] = INFINITY
        leastDistNeighbour[each] = None
        if each==str(switchA).zfill(16):
            distanceFromA[each] = 0
    s = []
    while len(distanceFromA) > 0:
        minval = INFINITY
        dpid_sel = -1
        #find the node with the lowest distance and select it
        for each in dpidlist:
            if distanceFromA[each] <minval:
                minval = distanceFromA[each]
                dpid_sel = each
        #somehow the list was empty so return an empty path
        if dpid_sel == -1:
            break
        #remove the selected node from the list
        dpidlist.remove(dpid_sel)

        #optimization. because we know the end point we can stop as soon as we hit it and create the path array
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

        #find neighbours of the selected node and then calculate the distances from each
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

    #this part formats the output in a coherent way
    d = {}
    s.reverse()
    outlist.reverse()
    #somehow the list was empty or the first item was not actually the start node, return empty path
    if not s or int(s[0])!= switchA:
        print "FAILLL"
        return pathAtoB

    #format the data using nodeDict
    linport = portA
    for each in outlist:
        d = nodeDict(int(each[2]), linport, each[1])
        linport = each[0]
        pathAtoB.append(d)
    #insert the last node
    d = nodeDict(int(switchB),linport, portB)
    pathAtoB.append(d)

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
