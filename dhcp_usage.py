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
            dhcp_networks = get_dhcp_leases(ssh, dhcp_server)
            
            for network in dhcp_networks:
                dhcp_subnets.append({})
        
        #dhcp_subnets.append({'name': 'router_name'})
            
    return 1

def get_dhcp_leases(ssh, dhcp_server):
    

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

def parse_routername(output):
    router_name = output[0].split(': ')[1]
    return router_name

def main():
    routers = load_routers(router_file)
    
    

if __name__ == "__main__":
    main()
