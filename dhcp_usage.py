#!/usr/bin/python3

# Matt Perry 2nd Nov 2022

# Logs into a list of routers and creats a csv report of public IP subnets
# assigned to DHCP interfaces and the % of those subnets with active 
# leases

import paramiko
import re
import csv
import tik_ssh
import creds
import threading
import concurrent.futures
from pathlib import Path
from ipaddress import ip_address,ip_interface,ip_network

# List to hold router names and Number of private leases
lease_list = []

# path to routers.csv and output.csv
current_dir = Path.cwd()
router_file = current_dir / 'routers.csv'
output_file = current_dir / 'output.csv'

# Array to store DHCP subnets
dhcp_subnets = []

def get_router_info(router):
    ip = router[1]
    ssh = tik_ssh.connect(str(ip), creds.username, creds.password)
    
    if ssh == None:
        return None
    else:
        router_name = get_router_name(ssh)
        dhcp_servers = get_dhcp_servers(ssh)
        
        for dhcp_server in dhcp_servers:
            dhcp_networks = get_dhcp_leases(ssh, dhcp_server, router_name)
            
    return 1

def get_dhcp_leases(ssh, dhcp_server, router_name):
    command = f":put [ /ip address print as-value where \
        interface={dhcp_server['interface']} and disabled=no ]"
    output = tik_ssh.command(ssh, command)
    dhcp_networks = parse_interface_networks(output)
    
    command = f":put [ /ip dhcp-server lease print as-value where dynamic=yes ]"
    output = tik_ssh.command(ssh, command)
    leases = parse_leases(output)

    networks = []

    for subnet in dhcp_networks:

        networks.append({
            'router': router_name,
            'server': dhcp_server['name'],            
            'network': subnet,
            'ip available': subnet.num_addresses - 3,
            'total leases': 0,
            'dynamic': 0,
            'reserved': 0,
            'public': 0,
            'private': 0
        })
    
    if leases != None:
        for lease in leases:
            for i in range(len(networks)):
                if networks[i]['network'].overlaps(lease):
                    networks[i]['dynamic'] += 1
                    networks[i]['total leases'] += 1
                    if lease.is_global:
                        networks[i]['public'] += 1
                    else:
                        networks[i]['private'] += 1
    
    command = f":put [ /ip dhcp-server lease print as-value where \
       server={dhcp_server['name']} and dynamic=no and status=bound ]"
    output = tik_ssh.command(ssh, command)
    leases = parse_leases(output)

    if leases != None:
        for lease in leases:
            for i in range(len(networks)):
                if networks[i]['network'].overlaps(lease):
                    networks[i]['reserved'] += 1
                    networks[i]['total leases'] += 1
                    if lease.is_global:
                        networks[i]['public'] += 1
                    else:
                        networks[i]['private'] += 1
    
    for network in networks:
        dhcp_subnets.append(network)

def get_dhcp_servers(ssh):
    dhcp_servers = []
    
    command = "/ip dhcp-server print count-only"
    output = tik_ssh.command(ssh, command)
    server_count = int(output[0])
    
    if server_count > 0:
        for i in range(server_count):
            command = f":put [ /ip dhcp-server get number={i} name ]"
            output = tik_ssh.command(ssh, command)
            server_name = output[0]
            
            command = f":put [ /ip dhcp-server get number={i} interface ]"
            output = tik_ssh.command(ssh, command)
            server_interface = output[0]
            
            dhcp_servers.append({'name': server_name, 'interface': server_interface})
    return dhcp_servers

def get_router_name(ssh):
    command = "/system identity print"
    output = tik_ssh.command(ssh, command)
    router_name = output[0].split(': ')[1]
    
    return router_name
        
def load_routers(path):
    #list to hold router names and IP
    routers = []
    
    with open(path) as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            routers.append([row[0], row[1]])
    
    return routers

def output_csv(output_file):
    with open(output_file, 'w') as csvfile:
        headers = dhcp_subnets[0].keys()

        writer = csv.DictWriter(csvfile,headers)

        writer.writeheader()
        writer.writerows(dhcp_subnets)
        
        

def parse_interface_networks(output):
    lines = output[0].split('.id=')
    networks = []
    for line in lines:
        if line != '':            
            for value in line.split(';'):
                if value[:8] =='address=':
                    networks.append(ip_interface(value[8:]).network)
    if len(networks) > 0:
        return networks
    else:
        return None

def parse_leases(output):

    lines = output[0]

    leases = []
    for line in lines.split('.id=')[1:]:
        for value in line.split(';'):
            if value[:8] == 'address=':
                leases.append(ip_network(value[8:] + '/32'))

    if leases == []:
        return None
    else:
        return leases

def poplulate_dhcp(routers):
    with concurrent.futures.ThreadPoolExecutor(max_workers=40) as executor:
        executor.map(get_router_info,routers)

def main():
    routers = load_routers(router_file)
    
    poplulate_dhcp(routers)

    if len(dhcp_subnets) > 0:
        output_csv(output_file)

if __name__ == "__main__":
    main()
