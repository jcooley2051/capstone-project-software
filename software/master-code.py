import subprocess
import time

# Dictionary of script names and their corresponding commands.
# scripts = {
#     "aggregator": "python3 /home/admin/Documents/capstone-project-software/software/Formatting/aggregator.py",
#     "analyzer":   "python3 /home/admin/Documents/capstone-project-software/software/testing/analysis.py",
#     "gui":        "python3 /home/admin/Documents/capstone-project-software/software/GUI/GUIv5.py"
# }
scripts = {
    "aggregator": "python3 /home/admin/Documents/capstone-project-software/software/Formatting/aggregator2.py",
    "analyzer":   "python3 /home/admin/Documents/capstone-project-software/software/testing/analysis.py",
    "gui":        "python3 /home/admin/Documents/capstone-project-software/software/GUI/GUIv7.py"
}

# Dictionary to hold the running process objects.
processes = {}

def start_script(name, command):
    """Starts the script and stores the process in the processes dictionary."""
    print(f"Starting {name}...")
    proc = subprocess.Popen(command, shell=True)
    processes[name] = proc

# Start all scripts.
for name, command in scripts.items():
    start_script(name, command)

# Monitoring loop: checks every second whether a process has stopped.
while True:
    for name, proc in list(processes.items()):
        if proc.poll() is not None:  # If poll() returns a value, the process has terminated.
            print(f"{name} terminated. Restarting...")
            start_script(name, scripts[name])
    time.sleep(1)
