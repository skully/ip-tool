#!/usr/bin/env python3
import ipaddress
import subprocess
import json
import argparse
from ipaddress import ip_network


def get_container_networks():
    """ Retrieves the subnet that contains the container's main IP address. """
    try:
        # Lekérdezi a konténer saját IP-jét és prefix hosszát
        result = subprocess.run(['ip', '-json', 'addr'], capture_output=True, text=True, check=True)
        ip_data = json.loads(result.stdout)

        for iface in ip_data:
            if iface['ifname'] == 'lo':
                continue  # Kihagyjuk a loopback interfészt
            if 'addr_info' in iface:
                for addr in iface['addr_info']:
                    if addr['family'] == 'inet':  # Csak IPv4-et figyelünk
                        ip_address = addr['local']
                        prefixlen = addr['prefixlen']

                        # Meghatározzuk a teljes subnetet
                        network = ipaddress.ip_network(f"{ip_address}/{prefixlen}", strict=False)
                        return str(network)  # Pl. "10.244.1.0/24"

    except Exception as e:
        return f"Error retrieving subnet info: {str(e)}"

def collect_logs_by_image(image_name: str, output_file: str):
    try:
        # List all namespaces
        namespaces = subprocess.check_output("kubectl get namespaces -o=jsonpath='{.items[*].metadata.name}'",
                                             shell=True, text=True).split()

        with open(output_file, "w", encoding="utf-8") as file:
            for namespace in namespaces:
                # List all pods in the namespace
                pods = subprocess.check_output(
                    f"kubectl get pods -n {namespace} -o=jsonpath='{{.items[*].metadata.name}}'", shell=True,
                    text=True).split()

                for pod in pods:
                    images = subprocess.check_output(
                        f"kubectl get pod {pod} -n {namespace} -o=jsonpath='{{.spec.containers[*].image}}'", shell=True,
                        text=True).split()
                    absolute_pod_name = f"{pod}.{namespace}"

                    if image_name in images:
                        try:
                            logs = subprocess.check_output(f"kubectl logs {pod} -n {namespace}", shell=True, text=True)
                            for line in logs.splitlines():
                                file.write(f"{absolute_pod_name} {line}\n")
                            #file.write("\n")
                        except Exception as e:
                            file.write(f"{absolute_pod_name} Error retrieving logs: {e}\n\n")

        print(f"Logs collected successfully in {output_file}")
    except Exception as e:
        print(f"Error executing command: {e}")


def check_collision(file_path):
    subnets = []
    found = False

    with open(file_path, 'r') as file:
        for line in file:
            parts = line.strip().split()
            if len(parts) == 2:
                identifier, subnet = parts
                subnet_network = ip_network(subnet, strict=False)

                for existing_id, existing_subnet in subnets:
                    existing_network = ip_network(existing_subnet, strict=False)
                    if subnet_network.overlaps(existing_network):
                        print(f"Collision: {subnet} ({identifier}), {existing_subnet} ({existing_id})")
                        found = True

                subnets.append((identifier, subnet))
    if not found:
        print("Found none")

def main():
    parser = argparse.ArgumentParser(description="Utility script for container network inspection and log collection.")
    parser.add_argument("--collect", metavar="FILE", type=str,
                        help="Collect logs from Kubernetes pods into the specified file")
    parser.add_argument("--check", metavar="FILE", type=str,
                        help="Check file")
    args = parser.parse_args()

    if args.collect:
        collect_logs_by_image("ip-tool:latest", args.collect)
    elif args.check:
        check_collision(args.check)
    else:
        print(get_container_networks())



if __name__ == "__main__":
    main()
