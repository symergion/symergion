"""Module initializing and running SymErgion system.

This script sets up a monitoring system using the `watchdog` library to observe changes
in a Git repository's log files. It initializes the necessary components, including
the Git repository, configuration, and SymErgionCoding objects. It then starts an observer
to monitor changes and handles them using a custom event handler.

The script also manages the number of CPU cores used by PyTorch for parallel processing.
"""

import os
import time
import torch

from watchdog.observers import Observer

from git.repository import Repo
from handler.coding import HandlerCoding
from symergion.coding import SymErgionCoding
from symergion.config import Config


# Constants
REPO = "/repo"
DEFAULT_BRANCH = "main"

# Initialize the Git repository
repo = Repo(REPO, DEFAULT_BRANCH)
print(f"{repo} is instantiated for {REPO} with default branch {DEFAULT_BRANCH}")

# Prompt user for the SymErgion configuration file
symergion_config_file = input("Input symergion config file: ")

# Load the configuration from the specified JSON file
symergion_config = Config.from_json(f"/models/{symergion_config_file}")
print(f"{symergion_config} is instantiated for {symergion_config_file}")

# Set the number of CPU cores to use for PyTorch operations
idle_cores = symergion_config.idle_cores
cpu_cores = os.cpu_count() - idle_cores
torch.set_num_threads(cpu_cores)
torch.set_num_interop_threads(cpu_cores)
print(f"{cpu_cores} is set as number of threads for PyTorch")

# Initialize the SymErgionCoding object with the repository and configuration
symergion = SymErgionCoding(repo, symergion_config)
print(f"{symergion} is instantiated to serve {repo} task branches matching the following specification:\n{symergion.task_branch_spec}")

# Update the checkpoints with the correct model paths
for checkpoint in symergion.checkpoints:
    checkpoint.update({"name_or_path": f"/models/{checkpoint.get('name_or_path')}"})

    # Instantiate a Symerg object using the current checkpoint
    symerg = symergion.instantiate_symerg(checkpoint)
    print(f"{symerg.trait} SymErg {symerg} is instantiated for {symerg.name_or_path}")

    # Attach the instantiated Symerg object to the SymErgionCoding instance
    symergion.attach_symerg(symerg)
    print(f"{symerg} is attached to {symergion}")

# Create an event handler for coding-related tasks
event_handler = HandlerCoding(symergion)

# Start observing changes in the Git logs directory
observer = Observer()
observer.schedule(event_handler, path=f"{REPO}/.git/logs/refs", recursive=True)
observer.start()

try:
    # Keep the observer running indefinitely
    while True:
        time.sleep(15)
except KeyboardInterrupt:
    # Stop the observer if interrupted by the user
    observer.stop()

# Wait for the observer to finish
observer.join()
