# Puffer Quality of Experience Dataset Curation

## Experiment setup
### Set up Puffer server in a virtual environment
1. Run Ubuntu Desktop virtual machine on VirtualBox following the [Ubuntu documentation](https://ubuntu.com/tutorials/how-to-run-ubuntu-desktop-on-a-virtual-machine-using-virtualbox#1-overview).
2. Clone [puffer repository](https://github.com/StanfordSNR/puffer?tab=readme-ov-file) in the VirtualBox environment.
3. Follow the official [documentation](https://github.com/StanfordSNR/puffer/wiki/Documentation) to set up and run the local Puffer server.

### Set up environment for netUnicorn and LibreQoS
1. Add the packet capture data of the background users to the outgoingGroupedPcap and incomingGroupedPcap directories in the format <user_ip_address>/<pcap_name>.pcap.
2. Modify login credentials in puffer_watcher.py:
    ```
    driver.find_element(By.NAME, "username").send_keys("username")
    driver.find_element(By.NAME, "password").send_keys("password")
    ```
3. Replace "https://puffer.stanford.edu/player/" in watch_puffer.py with the url of the local Puffer server:
    ```
    pipeline = (
        Pipeline()
        .then(StartCapture(filepath="/tmp/capture.pcap", name="capture"))
        .then(WatchPufferVideo("https://puffer.stanford.edu/player/", 10))
        .then(StopNamedCapture(start_capture_task_name="capture"))
        .then(UploadToFileIO(filepath="/tmp/capture.pcap", expires="1d"))
    )
    ```

## Data collection 
### Some background:
We are actively using and running commands on two servers:
1. ```snl-server-2```: This will serve as the upstream server
2. ```snl-server-9```: This will serve as the downstream server
We are ssh-ing into these servers. "on server 2", "on local", and "on server 9" refer to where each of the below steps are executed.


At a high-level, our general experiment scenario uses the Puffer (Stanford) video server backend/platform to stream videos from. We will utilize netUnicorn as Puffer clients, stream the videos for a set duration of time. This video traffic will be redirected through snl-server-2 and snl-server-9 (with a hidden snl-server-10 that uses libreQoS), and while we stream these videos we will also replay UCSB gateway packet captures as background traffic. On each server, we will utilize a repository of packet captures from anonymized UCSB network users, sorted by IP address. We will first get IP addresses that have traffic that meets our needs. We consider that 1) the traffic is randomly chosen and representative, 2) that the traffic has a certain data rate, and 3) the captured duration. 

### Steps:

To get these IPs that meet our needs(and log the IPs for book-keeping):
1. run ```$ ./init_exp_ips.sh``` on server 2

Next, we have to move these IPs to server 9 so we replay the same traffic simultaneously from snl-server-2 and -9. (We do it this way to also have a local store of the experiment).

2. run ```$ scp <user>@snl-server-2.cs.ucsb.edu:~/curr_ips.txt .``` on local
3. run ```$ scp curr_ips.txt <user>@snl-server-9.cs.ucsb.edu:~/```  on local


4. cd to the correct directory
    1. run ```$ cd /mnt/md0/jaber/outgoingGroupedPcap``` on server 9
  
Next, we want to replay traffic between upstream server 9 through server 10 and server 2. Steps 5, 6, and 7 should be executed simultaneously, and for the same duration.
5. Start tcpreplays
    1. run ```$ cat ~/curr_ips.txt | grep -o "'[0-9.]*'" | xargs tcpreplay -i ens2f1``` on server 9 
    2. run ```$ cat ~/curr_ips.txt | grep -o "'[0-9.]*'" | xargs -I {} find /mnt/md0/jaber/incomingGroupedPcap/{} -type f -name '*.pcap' | xargs tcpreplay -i eno2``` on server 2

6. Start tshark pcaps
    1. run ```$ tshark -i ens2f1 -f ‘host <PINOT-node1 IPaddr> or host <PINOT-node2 IPaddr>’ -w ~/downstream_data/result1_15min.pcap``` on server 9 
    2. run ```$ tshark -i eno2 -f ‘host <PINOT-node1 IPaddr> or host <PINOT-node12 IPaddr>’ -w ~/upstream_data/result1_15min.pcap``` on server 2
  
We also want to run the puffer_watcher so that we can collect the video streaming packets.

7. Run ```python puffer_watcher.py``` on linux VM.

For each iteration of the experiment, we adjust the data_rate parameter to the python script invoked by ```init_exp_ips.sh```.
