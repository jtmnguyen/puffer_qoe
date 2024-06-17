# Puffer Quality of Experience Dataset Curation

## Experiment setup
### Set up Puffer server in a virtual environment
1. Run Ubuntu Desktop virtual machine on VirtualBox following the [Ubuntu documentation](https://ubuntu.com/tutorials/how-to-run-ubuntu-desktop-on-a-virtual-machine-using-virtualbox#1-overview).
2. Clone [puffer repository](https://github.com/StanfordSNR/puffer?tab=readme-ov-file) in the VirtualBox environment.
3. Follow the official [documentation](https://github.com/StanfordSNR/puffer/wiki/Documentation) to set up and run the local Puffer server.

### Set up environment for netUnicorn and LibreQoS
1. Add the packet capture data of the background users to the outgoingGroupedPcap and incomingGroupedPcap directories in the format <user_ip_address>/<pcap_name>.pcap.
3. Modify login credentials in puffer_watcher.py:
```
driver.find_element(By.NAME, "username").send_keys("username")
driver.find_element(By.NAME, "password").send_keys("password")
```
4. Replace "https://puffer.stanford.edu/player/" in watch_puffer.py with the url of the local Puffer server:
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
