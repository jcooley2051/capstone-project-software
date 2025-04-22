import subprocess
import time
import signal
import sys
import os

# Dictionary of script names and their corresponding commands.
scripts = {
    "aggregator": "python3 /home/admin/Documents/capstone-project-software/software/Formatting/aggregator2_no_bme_sc.py",
    "analyzer":   "python3 /home/admin/Documents/capstone-project-software/software/testing/analysis.py",
    "gui": f"python3 /home/admin/Documents/capstone-project-software/software/GUI/GUIv11_no_bme_sc.py {os.getpid()}"
}

# Dictionary to hold the running process objects.
processes = {}

def start_script(name, command):
    """Starts the script and stores the process in the processes dictionary."""
    print(f"Starting {name}...")
    proc = subprocess.Popen(
        command,
        shell=True,
        preexec_fn=os.setsid  # Start in a new session, making a new process group
    )
    processes[name] = proc

def cleanup():
    """Terminate all child process groups and their subprocesses."""
    print("Cleaning up child processes...")
    for name, proc in processes.items():
        try:
            print(f"Terminating {name}...")
            os.killpg(os.getpgid(proc.pid), signal.SIGTERM)  # Send SIGTERM to the whole group
        except Exception as e:
            print(f"Error terminating {name}: {e}")

    time.sleep(2)  # Give them time to shut down

    # Force kill any that didn’t shut down
    for name, proc in processes.items():
        if proc.poll() is None:
            try:
                print(f"Forcing {name} to kill...")
                os.killpg(os.getpgid(proc.pid), signal.SIGKILL)
            except Exception as e:
                print(f"Error force killing {name}: {e}")

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
