import ryu_ofctl

act1 = ryu_ofctl.OutputAction(1)
act2 = ryu_ofctl.OutputAction(2)
act3 = ryu_ofctl.OutputAction(3)


flow1 = ryu_ofctl.FlowEntry()
port1  = ryu_ofctl.getMacIngressPort("00:00:00:00:00:01")
port2  = ryu_ofctl.getMacIngressPort("00:00:00:00:00:03")

flow1.in_port = port1['port']
flow1.addAction(act2)
flow1.addAction(act3)

flow2 = ryu_ofctl.FlowEntry()
flow2.in_port = port2['port']
flow2.addAction(act1)
flow2.addAction(act2)

dpid = '1'

ryu_ofctl.insertFlow(dpid, flow1)
ryu_ofctl.insertFlow(dpid, flow2)
