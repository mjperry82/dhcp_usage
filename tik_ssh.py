import paramiko
import creds
import csv
from pathlib import Path

paramiko.util.log_to_file("main_paramiko_log.txt", level = "INFO")

def cleanOutput(output):
    newOutput = []
    for line in output:
        #if line.strip() != '':
        newOutput.append(line.strip())
    
    return newOutput            

def connect(host, username, password, port=22):
    client = paramiko.SSHClient()
    client.set_missing_host_key_policy(paramiko.client.AutoAddPolicy())
    
    try:
        client.connect(host, port, username, password,look_for_keys=False,allow_agent=False)
    except Exception as ex:
        print(f"general exception on host {host}")
        print(ex)
        client = None
    except (EOFError):
        print(f"Error on host {host}")
        print(ex)
        client = None
    except (SSHException):
        print(f"SSHExceptions on host {host}")
        print(ex)
        client = None
            
    return client

def command(client,command):
    stderr, stdout, stdin = client.exec_command(command)
    output = []
    for entry in stdout:
        output.append(entry)
    output = cleanOutput(output)
    return output

def main():
    # hide unhandled paramiko errors
    paramiko.util.log_to_file("main_paramiko_log.txt", level = "INFO")

    hosts = loadHosts(csvpath)
    commands = ['/system identity print', '/system package print where name=system']
    
    # counts for % reachable    
    
    for host in hosts:
        print(host)
        client = connect(host, creds.username, creds.password)
        if client != None:
            for command in commands:
                output = command(client,command)
                for line in output:
                    print(line)
            client.close()
            
        print()
    

if __name__ == "__main__":
    main()

