import argparse
import subprocess

def main():
    parser = argparse.ArgumentParser(description="Record MQTT messages using mosquitto_sub.")
    parser.add_argument('broker_uri', type=str, help="The URI of the MQTT broker (e.g., mqtt://broker.hivemq.com)")
    parser.add_argument('channel', type=str, help="The MQTT channel to subscribe to.")
    parser.add_argument('output_file', type=str, help="The file to save received messages.")
    args = parser.parse_args()

    # Parse MQTT URI
    if args.broker_uri.startswith('mqtt://'):
        broker = args.broker_uri[len('mqtt://'):]
    else:
        print("Invalid broker URI. Use the format 'mqtt://<broker_address>'")
        return

    print(f"Connecting to MQTT broker at {broker} and subscribing to channel {args.channel}")
    print(f"Saving messages to {args.output_file}")

    try:
        # Run mosquitto_sub
        with open(args.output_file, 'w') as file:
            subprocess.run(
                ['mosquitto_sub', '-h', broker, '-t', args.channel],
                stdout=file
            )
    except FileNotFoundError:
        print("Error: mosquitto_sub command not found. Please ensure Mosquitto is installed.")
    except Exception as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    main()
