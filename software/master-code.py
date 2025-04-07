import subprocess
import time
import signal
import sys
import os

# Dictionary of script names and their corresponding commands.
scripts = {
    "aggregator": "python3 /home/admin/Documents/capstone-project-software/software/Formatting/aggregator2.py",
    "analyzer":   "python3 /home/admin/Documents/capstone-project-software/software/testing/analysis.py",
    "gui": f"python3 /home/admin/Documents/capstone-project-software/software/GUI/GUIv11.py {os.getpid()}"
}

# Dictionary to hold the running process objects.
processes = {}

def start_script(name, command):
    """Starts the script and stores the process in the processes dictionary."""
    print(f"Starting {name}...")
    proc = subprocess.Popen(command, shell=True)
    processes[name] = proc

def cleanup():
    """Terminate all child processes."""
    print("Cleaning up child processes...")
    for name, proc in processes.items():
        print(f"Terminating {name}...")
        proc.terminate()  # Gracefully ask the process to terminate.
    # Give processes a moment to exit gracefully.
    time.sleep(2)
    # Force kill any processes still running.
    for name, proc in processes.items():
        if proc.poll() is None:
            print(f"Forcing {name} to kill...")
            proc.kill()
    print("Cleanup complete.")

def signal_handler(sig, frame):
    """Handle termination signals."""
    print("Signal received, terminating child processes...")
    cleanup()
    sys.exit(0)

# Register signal handlers for SIGINT (CTRL+C) and SIGTERM.
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Start all scripts.
for name, command in scripts.items():
    start_script(name, command)

# Monitoring loop: checks every second whether a process has stopped.
try:
    while True:
        for name, proc in list(processes.items()):
            if proc.poll() is not None:  # Process has terminated.
                print(f"{name} terminated. Restarting...")
                start_script(name, scripts[name])
        time.sleep(1)
except KeyboardInterrupt:
    print("Keyboard interrupt received. Exiting...")
    cleanup()
    sys.exit(0)
