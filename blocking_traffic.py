import ryu_ofctl

dpid = '1'
ryu_ofctl.deleteAllFlows(dpid)

act2 = ryu_ofctl.OutputAction(2)


flow1 = ryu_ofctl.FlowEntry()
flow1.dl_src = "00:00:00:00:00:01"
flow1.dl_dst = "00:00:00:00:00:03"

flow2 = ryu_ofctl.FlowEntry()
flow2.dl_src = "00:00:00:00:00:03"
flow2.dl_dst = "00:00:00:00:00:01"

flow3 = ryu_ofctl.FlowEntry()
flow3.dl_dst = "00:00:00:00:00:02"
flow3.addAction(act2)



ryu_ofctl.insertFlow(dpid, flow1)
ryu_ofctl.insertFlow(dpid, flow2)
