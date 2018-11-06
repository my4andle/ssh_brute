#!/usr/bin/python3
"""
Usage:
  defaultssh.py -h | --help
  defaultssh.py (--sshpass=<sshpass> --rhosts=<rhosts>) [--sshtimeout=<sshtimeout>] [--sshuser=<sshuser>]
 
Options:
  --sshuser=<sshuser>       Username
  --sshpass=<sshpass>       Password
  --rhosts=<rhosts>         List of targets single ip per line
  --sshtimeout=<sshtimeout> Timeout for each conccurent ssh attempt
"""
import json
import paramiko
import concurrent.futures

from docopt import docopt


def generate_list_from_file(data_file):
    """Convert rhosts file to list"""
    print("Generating data list from: {}".format(data_file))
    data_list = []
    with open(data_file, 'r') as my_file:
        for line in my_file:
            data_list.append(line.strip('\n').strip(' '))
    return data_list

def test_ssh(ip: str, sshuser: str, sshpass: str, sshtimeout: int):
    """check for default creds on ssh"""
    print("Testing ssh for: {}".format(ip))

    try:
        client = paramiko.SSHClient()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        client.connect(
            hostname=ip, 
            port=22, 
            username=sshuser, 
            password=sshpass, 
            timeout=int(sshtimeout),
            auth_timeout=int(sshtimeout),
            banner_timeout=int(sshtimeout),
            )
        client.close()
        return ip
    except:
        pass

def test_ssh_concurrent(rhosts: list, sshuser: str, sshpass: str, sshtimeout: int):
    """Run ssh login test concurrently"""
    print("Entering concurrent url test")
    results_list = []

    if len(rhosts) > 50:
        workers = 50
    else:
        workers = len(rhosts)

    with concurrent.futures.ProcessPoolExecutor(max_workers=workers) as pool:
        results = {pool.submit(test_ssh, ip, sshuser, sshpass, sshtimeout): ip for ip in rhosts}
        for future in concurrent.futures.as_completed(results):
            if future.result():
                results_list.append(future.result())
    return results_list

def main():
    opts = docopt(__doc__)
    rhosts = opts["--rhosts"]
    sshpass = opts["--sshpass"]

    if opts["--sshtimeout"]:
        sshtimeout = opts["--sshtimeout"]
    else:
        sshtimeout = 2
    
    if opts["--sshuser"]:
        sshuser = opts["--sshuser"]
    else:
        sshuser = "root"
        
    rhosts_list = set(generate_list_from_file(rhosts))

    results = test_ssh_concurrent(
        rhosts=rhosts_list,
        sshuser=sshuser,
        sshpass=sshpass,
        sshtimeout=sshtimeout,
    )

    filename = "sshbrute.log"

    with open(filename, mode="w+") as file:
        file.write("Username: {}\n".format(sshuser))
        file.write("Password: {}\n".format(sshpass))
        file.write("Successful logins:\n")
        for item in results:
            file.write(item + "\n")
    print(results)

if __name__ == '__main__':
    main()
