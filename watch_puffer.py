import os
import time

from netunicorn.client.remote import RemoteClient, RemoteClientException
from netunicorn.base import Experiment, ExperimentStatus, Pipeline

# Tasks to start tcpdump and stop named tcpdump task
from netunicorn.library.tasks.capture.tcpdump import StartCapture, StopNamedCapture

# Upload to file.io - public anonymous temporary file storage
from netunicorn.library.tasks.upload.fileio import UploadToFileIO

# puffer_watcher import

import random
import subprocess
from typing import Optional

from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC

from netunicorn.base import Failure, Result, Success, Task, TaskDispatcher
from netunicorn.base.architecture import Architecture
from netunicorn.base.nodes import Node


def watch(
    url: str, duration: Optional[int] = 100, chrome_location: Optional[str] = None, webdriver_arguments: Optional[list] = None
) -> Result[str, str]:
    display_number = random.randint(100, 500)
    xvfb_process = subprocess.Popen(
        ["Xvfb", f":{display_number}", "-screen", "0", "1920x1080x24"]
    )
    os.environ["DISPLAY"] = f":{display_number}"

    options = Options()
    options.add_argument("--no-sandbox")
    options.add_argument("--autoplay-policy=no-user-gesture-required")
    options.add_argument("--disable-dev-shm-usage")
    if webdriver_arguments:
        for argument in webdriver_arguments:
            options.add_argument(argument)
    if chrome_location:
        options.binary_location = chrome_location
    
    driver = webdriver.Chrome(service=Service(), options=options)
    time.sleep(1)
    driver.get(url)

    # Puffer login
    WebDriverWait(driver, 10).until(EC.presence_of_element_located((By.NAME, "username")))
    
    driver.find_element(By.NAME, "username").send_keys("user")
    driver.find_element(By.NAME, "password").send_keys("pass")
    
    driver.execute_script("document.getElementById('location').click();")
    
    driver.execute_script("document.getElementsByName('next')[0].click();")
    
    time.sleep(5)


    if duration:
        time.sleep(duration)
        result = Success(f"Video finished by timeout: {duration} seconds")
    else:
        result = Success("Video finished by reaching the end")

    driver.close()
    xvfb_process.kill()
    return result


class WatchPufferVideoLinuxImplementation(Task):
    requirements = [
        "apt install -y python3-pip wget xvfb procps chromium chromium-driver",
        "pip3 install selenium webdriver-manager",
    ]

    def __init__(
        self,
        video_url: str,
        duration: Optional[int] = None,
        chrome_location: Optional[str] = None,
        webdriver_arguments: Optional[list] = None,
        *args,
        **kwargs
    ):
        self.video_url = video_url
        self.duration = duration
        self.chrome_location = chrome_location
        if not self.chrome_location:
            self.chrome_location = "/usr/bin/chromium"
        self.webdriver_arguments = webdriver_arguments
        super().__init__(*args, **kwargs)

    def run(self):
        return watch(self.video_url, self.duration, self.chrome_location, self.webdriver_arguments)

class WatchPufferVideo(TaskDispatcher):
    def __init__(
            self,
            video_url: str,
            duration: Optional[int] = None,
            chrome_location: Optional[str] = None,
            webdriver_arguments: Optional[list] = None,
            *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        self.video_url = video_url
        self.duration = duration
        self.chrome_location = chrome_location
        self.webdriver_arguments = webdriver_arguments
        self.linux_implementation = WatchPufferVideoLinuxImplementation(
            self.video_url,
            self.duration,
            self.chrome_location,
            self.webdriver_arguments,
            name=self.name
        )

    def dispatch(self, node: Node) -> Task:
        if node.architecture in {Architecture.LINUX_AMD64, Architecture.LINUX_ARM64}:
        	return self.linux_implementation
        	
        raise NotImplementedError(
            f'WatchPufferVideo is not implemented for architecture: {node.architecture}'
        )

puffer_url = "http://169.231.44.73:8080/player/"#"https://puffer.stanford.edu/player/"

pipeline = (
    Pipeline()
    .then(StartCapture(filepath="/tmp/capture.pcap", name="capture"))
    .then(WatchPufferVideo(puffer_url, 15*60))
    .then(StopNamedCapture(start_capture_task_name="capture"))
    .then(UploadToFileIO(filepath="/tmp/capture.pcap", expires="1d"))
)

# if you have .env file locally for storing credentials, skip otherwise
if '.env' in os.listdir():
    from dotenv import load_dotenv
    load_dotenv(".env")

NETUNICORN_ENDPOINT = 'https://pinot.cs.ucsb.edu/netunicorn'
NETUNICORN_LOGIN = 'terguero'
NETUNICORN_PASSWORD = 'Xe608gQQGrM0'

client = RemoteClient(endpoint=NETUNICORN_ENDPOINT, login=NETUNICORN_LOGIN, password=NETUNICORN_PASSWORD)
client.healthcheck()

nodes = client.get_nodes()

# switch for showing our infrastructure vs you doing it locally on other nodes
if os.environ.get('NETUNICORN_ENDPOINT', 'http://localhost:26611') != 'http://localhost:26611':
    working_nodes = nodes.filter(lambda node: node.name.startswith("raspi")).take(5)
else:
    working_nodes = nodes.take(1)

working_nodes

# Creating the experiment
experiment = Experiment().map(pipeline, working_nodes)
experiment

for line in experiment[0].environment_definition.commands:
    print(line)

from netunicorn.base import DockerImage
for deployment in experiment:
    # you can explore the image on the DockerHub
    deployment.environment_definition = DockerImage(image='netunicorn/chromium:latest')

experiment_label = "puffer_watcher"
try:
    client.delete_experiment(experiment_label)
except RemoteClientException:
    pass

client.prepare_experiment(experiment, experiment_label)

while True:
    info = client.get_experiment_status(experiment_label)
    print(info.status)
    if info.status == ExperimentStatus.READY:
        break
    time.sleep(20)

for deployment in client.get_experiment_status(experiment_label).experiment:
    print(f"Prepared: {deployment.prepared}, error: {deployment.error}")

client.start_execution(experiment_label)

while True:
    info = client.get_experiment_status(experiment_label)
    print(info.status)
    if info.status != ExperimentStatus.RUNNING:
        break
    time.sleep(20)

from returns.pipeline import is_successful
from returns.result import Result

for report in info.execution_result:
    print(f"Node name: {report.node.name}")
    print(f"Error: {report.error}")

    result, log = report.result  # report stores results of execution and corresponding log
    
    # result is a returns.result.Result object, could be Success of Failure
    # or None is error occured during execution
    print(f"Result is: {type(result)}")
    if isinstance(result, Result):
        data = result.unwrap() if is_successful(result) else result.failure()
        for key, value in data.items():
            print(f"{key}: {value}")

    # we also can explore logs
    for line in log:
        print(line.strip())
    print()
