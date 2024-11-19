import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Record MQTT messages using mosquitto_sub.")
    parser.add_argument('host', type=str, help="The hostname or IP of the MQTT broker (e.g., localhost or 192.168.1.1).")
    parser.add_argument('port', type=int, help="The port number of the MQTT broker (e.g., 1883).")
    parser.add_argument('channel', type=str, help="The MQTT channel to subscribe to.")
    parser.add_argument('output_file', type=str, help="The file to save received messages.")
    args = parser.parse_args()

    print(f"Connecting to MQTT broker at {args.host}:{args.port} and subscribing to channel {args.channel}")
    print(f"Saving messages to {args.output_file}")

    try:
        # Run mosquitto_sub
        with open(args.output_file, 'w') as file:
            subprocess.run(
                ['mosquitto_sub', '-h', args.host, '-p', str(args.port), '-t', args.channel],
                stdout=file
            )
    except FileNotFoundError:
        print("Error: mosquitto_sub command not found. Please ensure Mosquitto is installed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
