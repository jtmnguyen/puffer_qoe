import os
import time

from netunicorn.client.remote import RemoteClient, RemoteClientException
from netunicorn.base import Experiment, ExperimentStatus, Pipeline

# Tasks to start tcpdump and stop named tcpdump task
from netunicorn.library.tasks.capture.tcpdump import StartCapture, StopNamedCapture

# Upload to file.io - public anonymous temporary file storage
from netunicorn.library.tasks.upload.fileio import UploadToFileIO

# puffer_watcher import
from puffer_watcher import WatchPufferVideo


pipeline = (
    Pipeline()
    .then(StartCapture(filepath="/tmp/capture.pcap", name="capture"))
    .then(WatchPufferVideo("https://puffer.stanford.edu/player/", 10))
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
