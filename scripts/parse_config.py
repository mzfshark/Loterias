import json
import sys

def parse_config(network):
    print(f"Debug: Parsing config for network: {network}", file=sys.stderr)  # Debug output to stderr
    with open('./src/config.json') as f:
        config = json.load(f)
    
    if network in config:
        data = config[network]
        return {
            "RPC_URL": data['RPC_URL'],
            "NATIVE_TOKEN": data['NATIVE_TOKEN'],
            "PROJECT_FUND": data['PROJECT_FUND'],
            "GRANT_FUND": data['GRANT_FUND'],
            "OPERATION_FUND": data['OPERATION_FUND']
        }
    else:
        raise ValueError(f"Network '{network}' not found in the configuration.", file=sys.stderr)

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print(f"Usage: python3 {sys.argv[0]} <network>", file=sys.stderr)
        sys.exit(1)
    
    network = sys.argv[1]
    try:
        config = parse_config(network)
        for key, value in config.items():
            print(f"{key}={value}")
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
