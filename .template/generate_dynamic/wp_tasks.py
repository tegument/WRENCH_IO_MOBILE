import codecs
import datetime
from glob import glob
import logging
import os
from os import path
import plistlib
import re
import subprocess
import tempfile
import time
import uuid

import lib
from lib import task, read_file_as_str
from utils import run_shell

LOG = logging.getLogger(__name__)

@task
def run_wp(build, device):
	if not device or device.lower() == 'simulator': 
		LOG.info('Running Windows Phone Simulator')
	else:
		LOG.info('Running on Windows Phone device: {device}'.format(device=device))

