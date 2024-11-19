import argparse
import subprocess
import threading
import time


def publish_file_to_channel(host, port, file, channel, delay):
    print(f"Publishing messages from {file} to channel {channel} on {host}:{port} with a delay of {delay} seconds")
    try:
        while True:
            with open(file, 'r') as f:
                for line in f:
                    # Publish each line as a separate message
                    subprocess.run(
                        ['mosquitto_pub', '-h', host, '-p', str(port), '-t', channel, '-m', line.strip()],
                        check=True
                    )
                    time.sleep(delay)
    except FileNotFoundError:
        print(f"Error: File {file} not found.")
    except KeyboardInterrupt:
        print(f"\nStopped publishing for file {file}.")
    except Exception as e:
        print(f"An error occurred: {e}")


def main():
    parser = argparse.ArgumentParser(description="Publish MQTT messages from files to channels.")
    parser.add_argument('host', type=str, help="The hostname or IP of the MQTT broker.")
    parser.add_argument('port', type=int, help="The port number of the MQTT broker.")
    parser.add_argument('--file1', type=str, help="Path to the first file.")
    parser.add_argument('--channel1', type=str, help="MQTT channel for the first file.")
    parser.add_argument('--file2', type=str, help="Path to the second file.")
    parser.add_argument('--channel2', type=str, help="MQTT channel for the second file.")
    parser.add_argument('--file3', type=str, help="Path to the third file.")
    parser.add_argument('--channel3', type=str, help="MQTT channel for the third file.")
    parser.add_argument('--delay', type=float, default=1.0,
                        help="Delay (in seconds) between publishing events. Default is 1 second.")

    args = parser.parse_args()

    threads = []

    # Create a thread for each file-channel pair
    if args.file1 and args.channel1:
        thread1 = threading.Thread(target=publish_file_to_channel,
                                   args=(args.host, args.port, args.file1, args.channel1, args.delay))
        threads.append(thread1)
    if args.file2 and args.channel2:
        thread2 = threading.Thread(target=publish_file_to_channel,
                                   args=(args.host, args.port, args.file2, args.channel2, args.delay))
        threads.append(thread2)
    if args.file3 and args.channel3:
        thread3 = threading.Thread(target=publish_file_to_channel,
                                   args=(args.host, args.port, args.file3, args.channel3, args.delay))
        threads.append(thread3)

    # Start all threads
    for thread in threads:
        thread.start()

    # Wait for all threads to finish (they won't, as they loop indefinitely, but this keeps the main program alive)
    try:
        for thread in threads:
            thread.join()
    except KeyboardInterrupt:
        print("\nProgram interrupted by user. Stopping all threads.")


if __name__ == "__main__":
    main()
