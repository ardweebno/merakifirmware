########################################################################
#
# merakifirmware.py
#
# Version:	1.0
# Purpose: 		Allow easy rollback of Meraki networks to previous code versions.
# Features: 	1. Allow to show previous versions applied to network
#				2. Allow to rollback to a previously applied code version
# Usage:	
#	
#
# % python3 merakifirmware.py --getupgrades --network="LAB1 - appliance"
#
# 2019-09-24T05:55:07Z: Completed upgrade from MX 14.39 (ID: 1828) to MX 14.40 (ID:1868)
# 2020-06-05T08:07:49Z: Completed upgrade from MX 14.40 (ID: 1868) to MX 14.42 (ID:1964)
# 2020-09-29T11:08:22Z: Completed upgrade from MX 14.42 (ID: 1964) to MX 14.53 (ID:2009)
# 2020-09-30T13:41:21Z: Completed upgrade from MX 14.53 (ID: 2009) to MX 15.36 (ID:2088)
# 2020-11-19T03:00:00Z: Completed upgrade from MX 15.36 (ID: 2088) to MX 15.40 (ID:2110)
# 2021-01-28T03:00:00Z: Completed upgrade from MX 15.40 (ID: 2110) to MX 15.42 (ID:2128)
# 2021-07-29T03:00:00Z: Completed upgrade from MX 15.42 (ID: 2128) to MX 15.43 (ID:2181)
# 2021-10-24T11:10:25Z: Completed upgrade from MX 15.43 (ID: 2181) to MX 15.44 (ID:2241)
# 2022-03-24T03:00:00Z: Completed upgrade from MX 15.44 (ID: 2241) to MX 16.16 (ID:2277)
# 2023-01-26T03:00:00Z: Canceled upgrade from MX 16.16 (ID: 2277) to MX 17.10.2 (ID:2372)
# 2022-12-09T01:37:58Z: Completed upgrade from MX 16.16 (ID: 2277) to MX 17.10.2 (ID:2372)
# 2022-12-26T10:47:19Z: Completed upgrade from MX 17.10.2 (ID: 2372) to MX 16.16 (ID:2277)
# 2022-12-27T08:23:31Z: Canceled upgrade from MX 16.16 (ID: 2277) to MX 16.16.8 (ID:2387)
#
#
# Note: The ID: number is an internal Meraki code version for each code release.  For example, MX 16.16.8 code == ID 2387
#
#
#
# % python3 merakifirmware.py --rollback=2277 --network="LAB1 - appliance"
#
# Network was rolled back to code ID: 2277
#
#



########################################################################
import time
import meraki
import sys
import os
import asyncio
import requests
import getopt
import json
from datetime import datetime, timezone



######################################################
#
# Set important runtime variables
#

myAPIKey 	= ""	# The API Key you use to access api.meraki.com
myOrgName	= ""									# This is the name of your Meraki Organization.  Needs to be exactly what you see in Dashboard 


########################################################################
def apiConnect(api_key):
	dashboard = meraki.DashboardAPI(
		api_key=api_key	,
		base_url='https://api.meraki.com/api/v1',
		output_log=False,
		print_console=False)
	return(dashboard)


########################################################################
def getMyOrg(orgName):

	my_org = ''
	orgs = getOrgs()

	# loop through the list of orgs, find the orgID assigned to your org name
	for org in orgs:
		if org['name'] == orgName:
			my_org = int(org['id'])

	if my_org != '':
		return(my_org)
	else:
		print("Error finding orgName {}".format(orgName))
		quit()


########################################################################
def getOrgs():
	try:
		orgs = dashboard.organizations.getOrganizations()
	except:
		print("Error getting org list!  Quitting....")
		quit()
	return(orgs)


########################################################################
def findNetworkId(networks, networkName):
	netID = -1	# This is the defualt in case we don't find a matching networkName
	
	for net in networks:
		if net['name'] == networkName:
			return(net['id'])
	return(netID)


########################################################################
def get_networkid_by_name(networkName,my_key,my_org):
	# Get the current list of networks
	netID = findNetworkId(networks, networkName)
	return(netID)


########################################################################
def print_usage():
	print ();
	print ("Some expample usage examples:")
	print ("merakifirmware.py --getupgrades --network=<Network-Name>                        [Show list of recent upgrades to this device]")
	print ("merakifirmware.py --rollback=<version> --network=<Network-Name>                 [Rollback a network to a previous version ID]")
	print ("")
	print ("")
	quit()


########################################################################
def rollback(networkId, version):
	network_id = networkId
	reasons = [
		{'category': 'performance', 'comment': 'This upgrade made performance suck like a black hole when hangry.'}, 
		{'category': 'stability', 'comment': "The only thing we could count on is this release not working."}
	]

	
	upgradeTime = datetime.now(timezone.utc).isoformat()

	response = dashboard.networks.createNetworkFirmwareUpgradesRollback(
    	network_id, reasons, 
    	product='appliance', 
    	time=upgradeTime, 
    	toVersion={'id': version}
	)
	print()
	print(f"Network was rolled back to code ID: {version}")
	print()
	print()


########################################################################
def getUpgrades(myNetwork, myOrgId, myAPIKey):
	url = f"https://api.meraki.com/api/v1/organizations/{myOrgId}/firmware/upgrades"
	payload = None
	headers = {
    	"Content-Type": "application/json",
    	"Accept": "application/json",
    	"X-Cisco-Meraki-API-Key": myAPIKey
	}

	try:
		response = requests.request('GET', url, headers=headers, data = payload).text.encode('utf8')
	except Exception as e:
		print()
		print("Error: {}".format(str(e)))
		quit()

	myData = json.loads(response)
	for myNet in myData:
		if myNet['network']['name'] == myNetwork:
			fromVersion 	= myNet['fromVersion']['shortName']
			fromVersionId 	= myNet['fromVersion']['id']
			toVersion		= myNet['toVersion']['shortName']
			toVersionId		= myNet['toVersion']['id']
			updatedOn		= myNet['time']
			status			= myNet['status']
			print(f"{updatedOn}: {status} upgrade from {fromVersion} (ID: {fromVersionId}) to {toVersion} (ID:{toVersionId})")



###########################################################################################################################################
#
# main()
#
###########################################################################################################################################

################################### 
# 
# Setting up initital variables
#
debug = False
not_debug = not debug
cmd = ''
myNetwork = ''


###################################
#
# Check for setup errors.
#
if myAPIKey == "" or myOrgName == "":
	print()
	print("ERROR:  You forgot to define your OrgName or API Key.  Check the top of the script.  Exiting...")
	print()
	print()
	quit()



###################################
#
# Grab and process the command line options
#
try:
	options, remainder = getopt.getopt(sys.argv[1:], 'g:r:n', ['getupgrades','network=', 'rollback='])
except Exception as e:
	print()
	print("Error: {}".format(str(e)))
	quit()

for opt, arg in options:
	if opt in ('-g', '--getupgrades'):
		cmd = 'getupgrades'	
	if opt in ('-n', '--network'):
		myNetwork = arg
	if opt in ('-r', '--rollback'):
		cmd = 'rollback'
		version = arg


#*****************************************#
#
# We are in getupgrades mode  
#
#*****************************************#
if cmd == 'getupgrades':
	if myNetwork != "":
		dashboard = apiConnect(myAPIKey)
		myOrgId = getMyOrg(myOrgName)
		getUpgrades(myNetwork, myOrgId, myAPIKey)
		quit()
#*****************************************#
#
# We are in getupgrades mode  
#
#*****************************************#
elif cmd == 'rollback':
	if myNetwork != '':
		dashboard = apiConnect(myAPIKey)
		myOrgId = getMyOrg(myOrgName)
		networks = dashboard.organizations.getOrganizationNetworks(myOrgId)
		networkId = get_networkid_by_name(myNetwork, myAPIKey, myOrgId)
		rollback(networkId, version)
else:
	# something went wrong.  Print out the CLI usage and hope the user figures it out.
	print_usage()
