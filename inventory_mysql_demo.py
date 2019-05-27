#!/usr/bin/env python

##-----------------------------------------------------------------------------
##  Copyright (c) 2016 VeloCloud Networks, Inc.
##  All rights reserved.
##-----------------------------------------------------------------------------

##-----------------------------------------------------------------------------
## Description
## Purpose of the script is to pull customer edge information and dump in the database
##-----------------------------------------------------------------------------

##-----------------------------------------------------------------------------
## Dependencies
## Python SDK Installed or velocloud in the folder
## init_vco_api 2required
##-----------------------------------------------------------------------------


import velocloud
from velocloud.rest import ApiException
from vco_client.rest import ApiException
import requests
from datetime import datetime, timedelta
import json
from requests.packages.urllib3.exceptions import InsecureRequestWarning
import time
import re
import urllib3
import sys
import os
import time
from datetime import datetime
from time import sleep
import mysql.connector
import random
from init_vco_api2 import *
import mysql.connector

reload(sys)
sys.setdefaultencoding('utf8')

urllib3.disable_warnings()
requests.packages.urllib3.disable_warnings(InsecureRequestWarning)

## Update the MySQL server setup details
cnx = mysql.connector.connect(user='user', password='password',
                              host='host/ip',
                              database='customer')

mycursor = cnx.cursor()

# Create VCO list with login details

vco_list = {}

vco_list['vco1'] = {'username': "user@velocloud.net", 'password': "passwd", 'link': "vco1.velcoloud.net",
                   'partner': "Demo1", "backward_compatibility_mode": False}
vco_list['vco2'] = {'username': "user@velocloud.net", 'password': "passwd", 'link': "vco2.velcoloud.net",
                   'partner': "Demo2", "backward_compatibility_mode": False}

### Running below for loop for all the VCOs ###
for vco in vco_list:
    print vco_list[vco]['link']

    ### Login to the VCO using API Call ####
    try:
        client = velocloud.ApiClient(host=vco_list[vco]['link'],
                                     backward_compatibility_mode=vco_list[vco]["backward_compatibility_mode"])
        client.authenticate(vco_list[vco]['username'], vco_list[vco]['password'], operator=True)
        client.cookie
        api = velocloud.AllApi(client)

    except:
        print("Unable to connect")
        print("Unexpected error:", sys.exc_info()[0])
        break

    date = datetime.utcnow()
    date_before = date - timedelta(days=10)

    get_customers = velocloud.NetworkGetNetworkEnterprises()
    get_customers.network_id = 0
    get_customers.id = 0
    get_customers._with = ["edge","edgeCount"]

    sleep(1)
    get_customers_reply = api.networkGetNetworkEnterprises(get_customers)



    # Get Customer details

    random.shuffle(get_customers_reply)
    for customer in get_customers_reply:
        customer = customer.to_dict()
        print json.dumps(customer, indent=4, sort_keys=True)

        Customer_ID_VCO = customer["logicalId"]

        if Customer_ID_VCO == None:
            continue
        VCO = vco_list[vco]['link']
        print customer["name"]
        name = re.match('^[A-Za-z0-9_\'\"|& -]{1,60}', customer["name"])
        Partner = ""
        if customer["enterpriseProxyName"] != None:
            partner = re.match('^[A-Za-z0-9_ -]{1,60}', customer["enterpriseProxyName"])
            if partner:
                Partner = partner.group(0)

        if name:
            Customer_NAME = name.group(0)
        else:
            Customer_NAME = "Invalid"

        Version = 0
        Segments_bool = 0
        Segments_num = 0
        NVS_bool = 0
        NVS_num = 0
        CVH_bool = 0
        CVH_num = 0
        HA_bool = False
        Cluster_bool = False
        VRRP_bool = False
        VNF_bool = False
        OSPF_BOOL = False
        BGP_BOOL = 0
        ROUTE_NUM = 0
        ROUTE_CHANGE = 0
        MPLS_BOOL = False
        WIRELESS_LINK = False
        BACKUP_LINK = False

        try:
            date = datetime.utcnow()
            date_before = date - timedelta(days=3)
            get_metrics = velocloud.MonitoringGetAggregateEdgeLinkMetrics()
            get_metrics.enterprises = customer["id"]
            interval = velocloud.Interval()
            interval.start = date_before.strftime('%Y-%m-%d %H:%M:%S')
            interval.end = date.strftime('%Y-%m-%d %H:%M:%S')
            get_metrics.interval = interval
            get_metrics.metrics = ["bpsOfBestPathRx", "bpsOfBestPathTx", "scoreTx", "scoreRx", "bytesRx", "bytesTx"]
            sleep(1)

            ## API Call to Collect to collect LINK METRICS OF AN EDGE
            params = {"enterprises": [customer["id"]], "interval": [{"start": interval.start}],
                      "with": ["bpsOfBestPathRx", "bpsOfBestPathTx", "scoreTx", "scoreRx", "bytesRx", "bytesTx"]}
            print params
            get_metrics_reply = client.call_api('/monitoring/getAggregateEdgeLinkMetrics', 'POST', body=params,
                                                response_type=object,
                                                _return_http_data_only=True, _request_timeout=300)

            print "############"
            print "CUSTOMER_ID:" + customer["name"]
            get_edges = velocloud.EnterpriseGetEnterpriseEdges()
            get_edges.enterpriseId = customer["id"]
            get_edges._with = []
            get_edges._with.append("recentLinks")
            get_edges._with.append("configuration")
            get_edges._with.append("cloudServiceStatus")
            get_edges._with.append("vnfs")
            get_edges._with.append("site")
            get_edges = api.enterpriseGetEnterpriseEdges(get_edges)

            ## API Call to Collect to get ENTERPRISE EDGE DETAILS
            params = {"enterpriseId": customer["id"],
                      "with": ["site", "configuration", "recentLinks", "cloudServiceSiteStatus", "vnfs",
                               "certificates"]}
            try:
                get_edges = client.call_api('/enterprise/getEnterpriseEdges', 'POST', body=params, response_type=object,
                                            _return_http_data_only=True)

            except ApiException as e:
                print(e)
            except:
                print "Any other error"

            ## API Call to Collect to get ENTERPRISE SERVICES DETAILS
            params = {"enterpriseId": customer["id"], "with": ["configuration", "profileCount", "edgeUsage"]}
            try:
                get_services = client.call_api('/enterprise/getEnterpriseServices', 'POST', body=params,
                                               response_type=object,
                                               _return_http_data_only=True)

            except ApiException as e:
                print(e)

            sleep(1)
            date_now = datetime.utcnow()
            ## API Call to Collect to get ENTERPRISE ROUTE TABLE

            params = {"enterpriseId": customer["id"]}
            try:
                res = client.call_api('/enterprise/getEnterpriseRouteTable', 'POST', body=params, response_type=object,
                                      _return_http_data_only=True, _request_timeout=300)

            except ApiException as e:
                print(e)
            except:
                print "too many events"

            ## Update any change of learned Routes
            number_of_routes_changes = 0
            try:
                for route in res["subnets"]:
                    for exit in route["eligableExits"]:
                        if exit["type"] != "DIRECT":
                            # Disabled for of now
                            ROUTE_NUM = ROUTE_NUM
                    for exit in route["preferredExits"]:
                        if exit["type"] != "DIRECT":
                            ROUTE_NUM = ROUTE_NUM + 1
                    if "learnedRoute" in route:
                        date_route_got_changed = datetime.strptime(route["learnedRoute"]["modified"],
                                                                   '%Y-%m-%dT%H:%M:%S.%fZ')
                        seconds = int(date_now.strftime('%s')) - int(date_route_got_changed.strftime('%s'))
                        minutes = seconds / 60
                        if (minutes < 1440):
                            #### For theRoute got changed last 24H back
                            number_of_routes_changes = number_of_routes_changes + 1

                print "TOTAL OF ROUTES CHANGED IN LAST 10 minutes:" + str(number_of_routes_changes)
            except:
                print "no routes"
            ROUTE_CHANGE = number_of_routes_changes

            sleep(1)
            ## API Call to Collect Edge Alerts
            params = {"enterpriseId": customer["id"],
                      "interval": {"start": date_before.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3]}}
            try:
                alerts = client.call_api('/enterprise/getEnterpriseAlerts', 'POST', body=params, response_type=object,
                                         _return_http_data_only=True)

            except:
                print("Unable to connect")
                print("Unexpected error:", sys.exc_info()[0])


            # API Call to Collect Profiles and Configurations


            sleep(1)
            params = {"enterpriseId": customer["id"], "with": ["edgeCount", "modules", "refs"]}
            try:
                configuration = client.call_api('/enterprise/getEnterpriseConfigurations', 'POST', body=params,
                                                response_type=object,
                                                _return_http_data_only=True)

            except:
                print("Unable to connect")
                print("Unexpected error:", sys.exc_info()[0])

        except ApiException as e:
            print(e)
            print("#We have no access to this customer")
            print("Unexpected error:", sys.exc_info()[0])
            sleep(10)
            continue
        # Determine if the Edge is a HUB
        for edge in get_edges:
            try:
                Score = 0
                print json.dumps(edge, indent=4, sort_keys=True)
                Bandwidth = 0
                UPLINK_USAGE = 0
                DOWNLINK_USAGE = 0
                Total_TX_Usage = 0
                Total_RX_Usage = 0
                Total_RX_Bandwidth = 0
                Total_TX_Bandwidth = 0
                HUB = False
                ENGINEER = None




                for config in configuration:
                    if config["edgeCount"] > 0:
                        for module in config["modules"]:
                            if 'refs' in module.keys():
                                if 'deviceSettings:vpn:edgeHub' in module["refs"].keys():

                                    #
                                    # Process Data
                                    #

                                    try:
                                        print ["modules"]["deviceSettings:vpn:edgeHub"]["data"]["logicalId"]
                                        if module["refs"]["deviceSettings:vpn:edgeHub"]["data"]["logicalId"] == edge[
                                            "logicalId"]:
                                            HUB = True
                                            print "HUB TRUE1"
                                    except Exception, e:
                                        print json.dumps(module["refs"], indent=4, sort_keys=True)

                                    for vpnref in module["refs"]["deviceSettings:vpn:edgeHub"]:
                                        print vpnref
                                        try:
                                            if vpnref["data"]["logicalId"] == edge["logicalId"]:
                                                HUB = True
                                                print "HUB TRUE2"

                                        except Exception, e:
                                            print Exception

                # API Call to collect type of events

                sleep(0.5)
                params = {"enterpriseId": customer["id"], "edgeId": edge["id"],
                          "interval": {"start": date_before.strftime('%Y-%m-%dT%H:%M:%S.%fZ')[:-3]}}
                try:
                    events = client.call_api('/event/getEnterpriseEvents', 'POST', body=params, response_type=object,
                                             _return_http_data_only=True)
                except ApiException as e:
                    print(e)

                ## MySQL query to update Events Table
                query = """INSERT IGNORE INTO Events ( Date, EdgeID, Name, Type)
                        VALUES (%s, %s, %s, %s)"""
                ## Edge events
                for event in events["data"]:
                    Date = datetime.strptime(event["eventTime"], '%Y-%m-%dT%H:%M:%S.%fZ')
                    Name = event["event"]
                    Type = "Event"

                    val = (Date, edge["logicalId"], Name, Type)
                    mycursor.execute(query, val)
                    cnx.commit()
                    if edge["edgeState"] == "CONNECTED":
                        if Name == "EDGE_HEALTH_ALERT" or Name == "EDGE_MEMORY_USAGE_ERROR":
                            Type = "BADCONFIG"
                            Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()
                        if HUB and Name == "EDGE_TUNNEL_CAP_WARNING":
                            Type = "BADCONFIG"
                            Name2 = "HUB_TUNNEL_CAP_WARNING"
                            Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                            val = (Date, edge["logicalId"], Name2, Type)
                            mycursor.execute(query, val)
                            cnx.commit()
                ## Alert events
                for alert in alerts["data"]:
                    print alert
                    if alert["edgeId"] == edge["id"]:
                        print alert
                        Type = "Alert"
                        Date = datetime.strptime(alert["triggerTime"], '%Y-%m-%dT%H:%M:%S.%fZ')
                        Name = alert["type"]
                        val = (Date, edge["logicalId"], Name, Type)
                        mycursor.execute(query, val)
                        cnx.commit()




                ## Gathers Edge and customer Specific data
                if (edge["activationState"] == "PENDING"):

                    License = "NOT ACTIVATED"
                    activated_days = 0
                    activated_time = None
                    Bandwidth = 0
                    TX_Bandwidth = 0
                    RX_Bandwidth = 0

                else:
                    linkn = 0
                    for link in get_metrics_reply:

                        # link = link.to_dict()
                        print json.dumps(link, indent=4, sort_keys=True)
                        # sleep(10)
                        ### CHECK if LINK IS BACKUP
                        BACKUP = False
                        for link_recent in edge["recentLinks"]:
                            link["link"]["displayName"] = ""

                            if link_recent["displayName"] == link["link"]["displayName"]:
                                if link_recent["backupState"] != "UNCONFIGURED":
                                    BACKUP = True

                        if "scoreTx" in link.keys():
                            print "there was a score"
                            # sleep(5)
                        else:
                            print "no secure was define"
                            link["scoreTx"] = 1
                            link["scoreRx"] = 1


                        if "link" in link.keys():
                            if link["link"]["edgeId"] == edge["id"] and link["scoreTx"] != 0 and BACKUP == False:
                                print "#linkMetric"
                                print json.dumps(link, indent=4, sort_keys=True)
                                # sleep(50)
                                Bandwidth = int(link["bpsOfBestPathTx"]) + int(link["bpsOfBestPathRx"])
                                Score = ((Score * linkn + (float(link["scoreTx"]) + float(link["scoreRx"]))) * 12.5) / (
                                            linkn + 1)
                                linkn + 1
                                print Score
                                print float(link["scoreTx"])
                                print float(link["scoreRx"])
                                TX_Bandwidth = int(link["bpsOfBestPathTx"])
                                RX_Bandwidth = int(link["bpsOfBestPathRx"])
                                RX_Usage = int(link["bytesRx"])
                                TX_Usage = int(link["bytesTx"])

                                Total_TX_Bandwidth = TX_Bandwidth + Total_TX_Bandwidth
                                Total_RX_Bandwidth = RX_Bandwidth + Total_RX_Bandwidth
                                Total_TX_Usage = Total_TX_Usage + TX_Usage
                                Total_RX_Usage = Total_RX_Usage + RX_Usage

                    if Total_RX_Bandwidth > 0:
                        DOWNLINK_USAGE = ((float(Total_RX_Usage * 8)) / float(
                            ((Total_RX_Bandwidth * 60 * 60 * 8 * 5)))) * 100
                        if DOWNLINK_USAGE > 100:
                            DOWNLINK_USAGE = 100
                    if Total_TX_Bandwidth > 0:
                        UPLINK_USAGE = ((float(Total_TX_Usage * 8)) / float(
                            ((Total_TX_Bandwidth * 60 * 60 * 8 * 5)))) * 100
                        if UPLINK_USAGE > 100:
                            UPLINK_USAGE = 100

                    Bandwidth = Bandwidth / 1000000
                    if (Bandwidth <= 30 and edge["modelNumber"]):
                        License = edge["modelNumber"] + "_30M"
                    if (Bandwidth <= 50 and Bandwidth > 30):
                        License = edge["modelNumber"] + "_50M"
                    if (Bandwidth <= 100 and Bandwidth > 50):
                        License = edge["modelNumber"] + "_100M"
                    if (Bandwidth <= 200 and Bandwidth > 100):
                        License = edge["modelNumber"] + "_200M"
                    if (Bandwidth <= 400 and Bandwidth > 200):
                        License = edge["modelNumber"] + "_400M"
                    if (Bandwidth <= 1000 and Bandwidth > 400):
                        License = edge["modelNumber"] + "_1G"
                    if (Bandwidth > 1000):
                        License = edge["modelNumber"] + "_5G"

                    if (Bandwidth > 200 and edge["edgeState"] == "CONNECTED" and (
                            edge["modelNumber"] == "edge520" or edge["modelNumber"] == "edge510" or edge[
                        "modelNumber"] == "edge500")):
                        print("we gound an edge is overcapacity edge5x0 200")
                        sleep(1)
                        Type = "BADCONFIG"
                        Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                        if HUB:
                            Name = "OVERCAPACITY_HUB " + edge["modelNumber"] + " over 200"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()
                        elif DOWNLINK_USAGE > 5 or UPLINK_USAGE > 5:
                            Name = "OVERCAPACITY_HIGHUSAGE " + edge["modelNumber"] + " over 200"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()

                    if (Bandwidth > 1000 and edge["edgeState"] == "CONNECTED" and edge["modelNumber"] == "edge540"):
                        print("we gound an edge is overcapacity")
                        sleep(1)
                        Type = "BADCONFIG"
                        Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                        if HUB:
                            Name = "OVERCAPACITY_HUB " + edge["modelNumber"] + " over 1000"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()
                        elif DOWNLINK_USAGE > 5 or UPLINK_USAGE > 5:
                            Name = "OVERCAPACITY_HIGHUSAGE " + edge["modelNumber"] + " over 1000"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()

                    if (Bandwidth > 2000 and edge["edgeState"] == "CONNECTED" and edge["modelNumber"] == "edge840"):
                        print("we gound an edge is overcapacity")
                        sleep(1)
                        Type = "BADCONFIG"
                        Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                        if HUB:
                            Name = "OVERCAPACITY_HUB " + edge["modelNumber"] + " over 2000"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()
                        elif DOWNLINK_USAGE > 5 or UPLINK_USAGE > 5:
                            Name = "OVERCAPACITY_HIGHUSAGE " + edge["modelNumber"] + " over 2000"
                            val = (Date, edge["logicalId"], Name, Type)
                            mycursor.execute(query, val)
                            cnx.commit()

                    last_contact = datetime.strptime(re.split('T| ', edge["lastContact"])[0], '%Y-%m-%d')
                    activated_time = datetime.strptime(re.split('T| ', edge["activationTime"])[0], '%Y-%m-%d')
                    activated_days = (last_contact - activated_time).days

                ## Edge Status , Profile ID and Serial Numbers
                Bandwidth_String = str(Bandwidth) + "Mbps"
                EdgeID = edge["logicalId"]
                Version = edge["buildNumber"]
                name = re.match("[A-Za-z0-9_ -]{1,60}", edge["name"])
                if name:
                    EdgeName = name.group(0)
                else:
                    EdgeName = "Invalid"
                    print EdgeName
                    sleep(6)
                Profile_ID = edge["configuration"]["enterprise"]["id"]
                Activation_Status = edge["activationState"]
                Edge_Status = edge["edgeState"]
                Activated_Day = activated_time
                Activated_Days = activated_days
                if edge["endpointPkiMode"] != None:
                    Certificate = edge["endpointPkiMode"]
                else:
                    Certificate = False
                if edge["serialNumber"] != None:
                    SerialNumber = edge["serialNumber"]
                else:
                    SerialNumber = False
                if edge["site"]["city"] != None:
                    City = edge["site"]["city"]
                else:
                    City = False
                if edge["site"]["country"] != None:
                    Country = edge["site"]["country"]
                else:
                    Country = False
                if edge["site"]["postalCode"] != None:
                    PostalCode = edge["site"]["postalCode"]
                else:
                    PostalCode = False
                if edge["site"]["state"] != None:
                    State = edge["site"]["state"]
                else:
                    State = False

                HA = "NONE"
                Private_LINKS_num = 0
                Private_LINKS_bool = False
                Private_LINKS_vlan = 0
                Public_LINKS_num = 0
                Public_LINKS_bol = False
                Public_LINKS_vlan = 0
                Public_LINKS_BACKUP = 0
                PUBLIC_LINKS_WIRELESS = 0
                bgp_bool = False
                ospf_bool = False
                netflow_bool = False
                static_routes_bool = False
                static_routes_num = 0
                Multicast_bool = False
                Firewall_rules_bool = False
                Firewall_rules_num = 0
                Firewall_rules_in_bool = False
                Firewall_rules_out_bool = False
                Business_policy_bool = False
                Business_policy_num = 0
                Firewall_Edge_Specific = 0
                WAN_Edge_Specific = 0
                QOS_Edge_Specific = 0
                Device_Settings_Edge_Specific = 0

                # To determine the location and country
                try:
                    lat = edge["site"]["lat"]
                    lon = edge["site"]["lon"]
                except:
                    print("Value not available strange")
                for link in edge["recentLinks"]:
                    print "#recentLink"
                    print json.dumps(link, indent=4, sort_keys=True)
                    if link["lat"] == 37.402866 or link["lat"] == "37.402866":
                        Private_LINKS_num = Private_LINKS_num + 1
                        Private_LINKS_bool = True
                        MPLS_BOOL = 1
                    else:

                        Public_LINKS_num = Public_LINKS_num + 1
                        Public_LINKS_bol = True
                        if link["backupState"] != "UNCONFIGURED":
                            Public_LINKS_BACKUP = Public_LINKS_BACKUP + 1
                            BACKUP_LINK = 1
                        if link["networkType"] == "WIRELESS":
                            PUBLIC_LINKS_WIRELESS = PUBLIC_LINKS_WIRELESS + 1
                            WIRELESS_LINK = 1

                for config in edge["configuration"]["enterprise"]["modules"]:
                    if config["name"] == "deviceSettings":
                        Device_Settings_Edge_Specific = config["isEdgeSpecific"]
                        config_device_settings = config
                    if config["name"] == "firewall":
                        Firewall_Edge_Specific = config["isEdgeSpecific"]
                        config_firewall = config
                    if config["name"] == "QOS":
                        QOS_Edge_Specific = config["isEdgeSpecific"]
                        config_QOS = config
                    if config["name"] == "WAN":
                        WAN_Edge_Specific = config["isEdgeSpecific"]

                if edge["haState"] == "UNCONFIGURED":
                    HA = "NONE"
                elif edge["haState"] == "PENDING_INIT" or edge["haState"] == "FAILED" or edge[
                    "haState"] == "PENDING_DISSOCIATION":
                    HA = "ACTIVE_STANDBY_DOWN"
                elif config_device_settings["edgeSpecificData"]["ha"]["enabled"]:
                    HA = "ACTIVE_STANDBY_UP"
                    HA_bool = 1

                for service in get_services:
                    if service["type"] == "edgeHubClusterMember":
                        print json.dumps(service, indent=4, sort_keys=True)
                        if service["edgeId"] == edge["id"]:
                            HA = "CLUSTER"
                            Cluster_bool = True
                            HUB = True

                try:
                    for segment in config_device_settings["edgeSpecificData"]["segments"]:
                        if segment["vrrp"]["enabled"]:
                            HA = "VRRP"
                            VRRP_bool = True
                            print("found VRRP")
                except:
                    print("no VRRP")

                if Device_Settings_Edge_Specific:
                    try:
                        for route in config_device_settings["edgeSpecificData"]["routes"]["static"]:
                            static_routes_bool = True
                            static_routes_num = static_routes_num + 1
                    except:
                        print("no static routes")

                    ### ADDING CHECKING for 2.X configuration and 3.X configuration
                    try:
                        passed = True
                        # Verify if all interfaces are either Routed or Disabled
                        # Verify if GE1 is used for HA if everything is okay then pass

                        # check if network has GE2-GE5 if yes set passed to False
                        for network in config_device_settings["edgeSpecificData"]["lan"]["network"]:
                            for interface in network["interfaces"]:
                                if interface == "GE1":
                                    if config_device_settings["edgeSpecificData"]["ha"]["enabled"] == "True":
                                        print("HA enabled")
                                    else:
                                        passed == False
                                else:
                                    passed = False

                    except:
                        print("NO ROUTED")
                    try:
                        if config_device_settings["edgeSpecificData"]["bgp"]["enabled"] == True:
                            bgp_bool = True
                            BGP_BOOL = True
                    except:
                        print("no bgp ")

                    try:
                        if config_device_settings["edgeSpecificData"]["netflow"]["enabled"] == True:
                            netflow_bool = True
                    except:
                        print("no netflow ")
                    try:
                        for interface in config_device_settings["edgeSpecificData"]["routedInterfaces"]:
                            try:
                                if interface["ospf"]["enabled"] == True:
                                    ospf_bool = True
                                    OSPF_BOOL = True
                            except:
                                print("DO NOTHING")
                            try:
                                if interface["multicast"]["igmp"]["enabled"] == True:
                                    Multicast_bool = True
                                if interface["multicast"]["pim"]["enabled"] == True:
                                    Multicast_bool = True
                            except:
                                print("DO NOTHING")
                    except:
                        print("#SHOUD NOT GET HERE")

                try:
                    local_segments = 0
                    for segment in config_device_settings["edgeSpecificData"]["segments"]:
                        Segments_bool = True
                        local_segments = local_segments + 1
                        if (local_segments > Segments_num):
                            Segments_num = local_segments
                        try:
                            if segment["vrrp"]["enabled"] == True:
                                HA = "VRRP"
                                VRRP_bool = True
                                print("found VRRP")
                        except:
                            print("no VRRP")
                        try:
                            if segment["bgp"]["enabled"] == True:
                                bgp_bool = True
                                BGP_BOOL = True
                        except:
                            print("no bgp")
                        try:
                            if segment["netflow"]["enabled"] == True:
                                netflow_bool = True
                        except:
                            print("no netflow")
                        try:
                            for route in segment["routes"]["static"]:
                                static_routes_bool = True
                                static_routes_num = static_routes_num + 1
                        except:
                            print("no static routes")

                except:
                    print("no segmenets")

                if Firewall_Edge_Specific:
                    try:
                        for rule in config_firewall["edgeSpecificData"]["inbound"]:
                            try:
                                rule["name"]
                                Firewall_rules_in_bool = True
                                Firewall_rules_num = Firewall_rules_num + 1
                            except:
                                print("bla")
                        for rule in config_firewall["edgeSpecificData"]["outbound"]:
                            try:
                                rule["name"]
                                Firewall_rules_out_bool = True
                                Firewall_rules_num = Firewall_rules_num + 1
                            except:
                                print("bla")
                    except:
                        print("DO NOTHING")

                if QOS_Edge_Specific:
                    try:
                        for rule in config_QOS["edgeSpecificData"]["rules"]:
                            try:
                                rule["name"]
                                Business_policy_bool = True
                                Business_policy_num = Business_policy_num + 1
                            except:
                                print("bla")
                    except:
                        print("GOT HERE BUT NO QOS")

                sleep(0.1)
                params = {"enterpriseId": customer["id"], "edgeId": edge["id"], "with": ["modules"]}
                try:
                    edge_config_stack = client.call_api('/edge/getEdgeConfigurationStack', 'POST', body=params,
                                                        response_type=object,
                                                        _return_http_data_only=True)
                except ApiException as e:
                    print(e)

                print json.dumps(edge_config_stack, indent=4, sort_keys=True)
                for configs in edge_config_stack:
                    print json.dumps(configs, indent=4, sort_keys=True)
                    if configs["name"] == "Edge Specific Profile":
                        for modules in configs["modules"]:
                            if modules["name"] == "WAN":
                                if "links" in modules["data"].keys():
                                    for link in modules["data"]["links"]:
                                        if link["bwMeasurement"] != "USER_DEFINED" and edge[
                                            "edgeState"] == "CONNECTED" and HUB:
                                            print("we gound a hub that is set as dynamic")
                                            sleep(3)
                                            Type = "BADCONFIG"
                                            Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                                            Name = "HUB_WITH_DYNAMIC_BANDWIDTH"
                                            val = (Date, edge["logicalId"], Name, Type)
                                            mycursor.execute(query, val)
                                            cnx.commit()
                                        if link["dynamicBwAdjustmentEnabled"] and edge["edgeState"] == "CONNECTED":
                                            if re.match('R2', Version) is not None:
                                                print("we found dynamicBwAdjustmentEnabled in R2")
                                                sleep(1)
                                                Type = "BADCONFIG"
                                                Date = date_now.strftime('%Y-%m-01T00:00:00.000Z')[:-3]
                                                Name = "R2_EDGE_DBA"
                                                val = (Date, edge["logicalId"], Name, Type)
                                                mycursor.execute(query, val)
                                                cnx.commit()
                ## Update Edge events in MySQL Edge Table
                query = """INSERT INTO Edge ( EdgeID, EdgeName, Customer_ID_VCO, Profile_ID, License, Certificate, SerialNumber, City, State, Country, PostalCode,  Bandwidth, Activation_Status, 
                                 Edge_Status, Activated_Day, Activated_Days, HA, Private_LINKS_num, Private_LINKS_bool, 
                                 Private_LINKS_vlan, Public_LINKS_num, Public_LINKS_bol, Public_LINKS_vlan, Public_LINKS_BACKUP, 
                                 bgp_bool, ospf_bool, netflow_bool, static_routes_bool, static_routes_num, Multicast_bool, 
                                 Firewall_rules_bool, Firewall_rules_num, Firewall_rules_in_bool, Firewall_rules_out_bool, 
                                 Business_policy_bool, Business_policy_num, PUBLIC_LINKS_WIRELESS ,Firewall_Edge_Specific ,
                                 WAN_Edge_Specific, QOS_Edge_Specific, Device_Settings_Edge_Specific,lat,lon,Score,UPLINK_USAGE,DOWNLINK_USAGE,Version,HUB )
                                 VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s,
                                  %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s ,%s, %s, %s, %s, %s , %s ,%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)   
                                 ON DUPLICATE KEY UPDATE
                                  EdgeName = VALUES(EdgeName), 
                                  Customer_ID_VCO = VALUES(Customer_ID_VCO), 
                                  Profile_ID= VALUES(Profile_ID),
                                  License= VALUES(License), Bandwidth= VALUES(Bandwidth),
                                  Certificate= VALUES(Certificate),
                                  SerialNumber= VALUES(SerialNumber),
                                  City= VALUES(City),
                                  State= VALUES(State),
                                  Country= VALUES(Country),
                                  PostalCode= VALUES(PostalCode),
                                  Bandwidth= VALUES(Bandwidth), 
                                  Activation_Status= VALUES(Activation_Status), 
                                  Edge_Status= VALUES(Edge_Status), 
                                  Activated_Day= VALUES(Activated_Day), 
                                  Activated_Days= VALUES(Activated_Days), HA= VALUES(HA), 
                                  Private_LINKS_num= VALUES(Private_LINKS_num), 
                                  Private_LINKS_bool= VALUES(Private_LINKS_bool), 
                                  Private_LINKS_vlan= VALUES(Private_LINKS_vlan), 
                                  Public_LINKS_num= VALUES(Public_LINKS_num), 
                                  Public_LINKS_bol= VALUES(Public_LINKS_bol), 
                                  Public_LINKS_vlan= VALUES(Public_LINKS_vlan), 
                                  Public_LINKS_BACKUP= VALUES(Public_LINKS_BACKUP),
                                  bgp_bool= VALUES(bgp_bool),
                                  ospf_bool= VALUES(ospf_bool), 
                                  netflow_bool= VALUES(netflow_bool), 
                                  static_routes_bool= VALUES(static_routes_bool), 
                                  static_routes_num= VALUES(static_routes_num), 
                                  Multicast_bool= VALUES(Multicast_bool), 
                                  Firewall_rules_bool= VALUES(Firewall_rules_bool), 
                                  Firewall_rules_num= VALUES(Firewall_rules_num), 
                                  Firewall_rules_in_bool= VALUES(Firewall_rules_in_bool), 
                                  Firewall_rules_out_bool= VALUES(Firewall_rules_out_bool), 
                                  Business_policy_bool= VALUES(Business_policy_bool), 
                                  Business_policy_num= VALUES(Business_policy_num), 
                                  PUBLIC_LINKS_WIRELESS= VALUES(PUBLIC_LINKS_WIRELESS),
                                  Firewall_Edge_Specific= VALUES(Firewall_Edge_Specific),
                                  WAN_Edge_Specific= VALUES(WAN_Edge_Specific),
                                  QOS_Edge_Specific= VALUES(QOS_Edge_Specific),
                                  Device_Settings_Edge_Specific= VALUES(Device_Settings_Edge_Specific),
                                  lat= VALUES(lat),
                                  lon= VALUES(lon),
                                  Score= VALUES(Score),
                                  UPLINK_USAGE= VALUES(UPLINK_USAGE),
                                  DOWNLINK_USAGE= VALUES(DOWNLINK_USAGE),
                                  Version = VALUES(Version),
                                  HUB = VALUES(HUB)
                                  ;
                     """

                if EdgeID:
                    val = (
                    EdgeID, EdgeName, Customer_ID_VCO, Profile_ID, License, Certificate, SerialNumber, City, State, Country, PostalCode, Bandwidth, Activation_Status, Edge_Status,
                    Activated_Day, \
                    Activated_Days, HA, Private_LINKS_num, Private_LINKS_bool, Private_LINKS_vlan, Public_LINKS_num,
                    Public_LINKS_bol, \
                    Public_LINKS_vlan, Public_LINKS_BACKUP, bgp_bool, ospf_bool, netflow_bool, static_routes_bool,
                    static_routes_num, \
                    Multicast_bool, Firewall_rules_bool, Firewall_rules_num, Firewall_rules_in_bool,
                    Firewall_rules_out_bool, \
                    Business_policy_bool, Business_policy_num, PUBLIC_LINKS_WIRELESS, Firewall_Edge_Specific,
                    WAN_Edge_Specific, \
                    QOS_Edge_Specific, Device_Settings_Edge_Specific, lat, lon, Score, UPLINK_USAGE, DOWNLINK_USAGE,
                    Version, HUB)

                print val
                print query
                mycursor.execute(query, val)

                cnx.commit()
            except ApiException as e:
                print(e)
                print("#We have some issue with this edge")
                print("Unexpected error:", sys.exc_info()[0])
                sleep(10)
                continue

        # Update Customer events in MySQL Customer Table


        query = """INSERT INTO Customer ( Customer_ID_VCO, VCO, Customer_NAME, Version, Segments_bool, 
                             Segments_num, NVS_bool, NVS_num, CVH_bool, CVH_num, 
                             VNF_bool, HA_bool, Cluster_bool, VRRP_bool, OSPF_BOOL, BGP_BOOL, ROUTE_NUM,ROUTE_CHANGE,MPLS_BOOL,WIRELESS_LINK,BACKUP_LINK,Partner )
                             VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) 
                             ON DUPLICATE KEY UPDATE
                              VCO = VALUES(VCO), 
                              Customer_NAME= VALUES(Customer_NAME),
                              Version= VALUES(Version), 
                              Segments_bool= VALUES(Segments_bool), 
                              Segments_num= VALUES(Segments_num), 
                              NVS_bool= VALUES(NVS_bool), 
                              NVS_num= VALUES(NVS_num),
                              CVH_bool= VALUES(CVH_bool), 
                              CVH_num= VALUES(CVH_num), 
                              VNF_bool= VALUES(VNF_bool), 
                              HA_bool= VALUES(HA_bool), 
                              Cluster_bool= VALUES(Cluster_bool), 
                              VRRP_bool= VALUES(VRRP_bool),
                              OSPF_BOOL= VALUES(OSPF_BOOL),
                              BGP_BOOL= VALUES(BGP_BOOL),
                              ROUTE_NUM= VALUES(ROUTE_NUM),
                              ROUTE_CHANGE= VALUES(ROUTE_CHANGE),
                              MPLS_BOOL= VALUES(MPLS_BOOL),
                              WIRELESS_LINK= VALUES(WIRELESS_LINK),
                              BACKUP_LINK= VALUES(BACKUP_LINK),
                              Partner = VALUES(Partner)
                              ;
                 """
        ## For all the Partner , can be updated to specific partner
        if Partner == "":
            Partner = vco_list[vco]['partner']

        val = (
        Customer_ID_VCO, VCO, Customer_NAME, Version, Segments_bool, Segments_num, NVS_bool, NVS_num, CVH_bool, CVH_num,
        VNF_bool, HA_bool, \
        Cluster_bool, VRRP_bool, OSPF_BOOL, BGP_BOOL, ROUTE_NUM, ROUTE_CHANGE, MPLS_BOOL, WIRELESS_LINK, BACKUP_LINK,
        Partner)
        print val
        mycursor.execute(query, val)

        cnx.commit()
        # sleep(30)

# Close the MySQL connection post table update
cnx.close()


