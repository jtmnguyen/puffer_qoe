import os
import random
import subprocess
import time
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

    driver.find_element(By.NAME, "username").send_keys("username") 
    driver.find_element(By.NAME, "password").send_keys("password")
    
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


if __name__ == "__main__":
    print(watch("https://puffer.stanford.edu/player/", 10))
