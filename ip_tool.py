#!/usr/bin/env python3

import argparse
import json
import subprocess
import ipaddress


def get_container_networks():
    """
    Retrieves the subnet that contains the container's main IP address.

    Input: None
    Output: str - The detected subnet in CIDR format (e.g., "10.244.1.0/24"), or an error message if retrieval fails.
    """
    try:
        result = subprocess.run(['ip', '-json', 'addr'], capture_output=True, text=True, check=True)
        ip_data = json.loads(result.stdout)

        for iface in ip_data:
            if iface['ifname'] == 'lo':
                continue  # Skip loopback interface
            if 'addr_info' in iface:
                for addr in iface['addr_info']:
                    if addr['family'] == 'inet':  # Consider only IPv4
                        ip_address = addr['local']
                        prefixlen = addr['prefixlen']
                        network = ipaddress.ip_network(f"{ip_address}/{prefixlen}", strict=False)
                        return str(network)

    except subprocess.CalledProcessError as e:
        return f"Error running 'ip' command: {e.stderr}"
    except json.JSONDecodeError:
        return "Error decoding JSON from 'ip' command output."
    except Exception as e:
        return f"Unexpected error: {str(e)}"


def collect_logs_by_image(image_name: str, output_file: str):
    """
    Collect logs from Kubernetes pods that use a specified image.

    Input:
        image_name (str): The name of the container image to search for.
        output_file (str): Path to the output file where logs will be stored.
    Output: None (logs are written to the specified file).
    """
    try:
        namespaces = subprocess.check_output(
            "kubectl get namespaces -o=jsonpath='{.items[*].metadata.name}'",
            shell=True, text=True
        ).split()

        with open(output_file, "w", encoding="utf-8") as file:
            for namespace in namespaces:
                try:
                    pods = subprocess.check_output(
                        f"kubectl get pods -n {namespace} -o=jsonpath='{{.items[*].metadata.name}}'",
                        shell=True, text=True
                    ).split()
                except subprocess.CalledProcessError as e:
                    file.write(f"Error retrieving pods in namespace {namespace}: {e.stderr}\n")
                    continue

                for pod in pods:
                    try:
                        images = subprocess.check_output(
                            f"kubectl get pod {pod} -n {namespace} -o=jsonpath='{{.spec.containers[*].image}}'",
                            shell=True, text=True
                        ).split()
                        absolute_pod_name = f"{pod}.{namespace}"

                        if image_name in images:
                            logs = subprocess.check_output(
                                f"kubectl logs {pod} -n {namespace}", shell=True, text=True
                            )
                            for line in logs.splitlines():
                                file.write(f"{absolute_pod_name} {line}\n")
                    except subprocess.CalledProcessError as e:
                        file.write(f"{absolute_pod_name} Error retrieving logs: {e.stderr}\n\n")
                    except Exception as e:
                        file.write(f"{absolute_pod_name} Unexpected error: {str(e)}\n\n")

        print(f"Logs collected successfully in {output_file}")

    except FileNotFoundError:
        print(f"Error: Output file '{output_file}' not found.")
    except PermissionError:
        print(f"Error: No permission to write to '{output_file}'.")
    except subprocess.CalledProcessError as e:
        print(f"Error executing kubectl command: {e.stderr}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


def check_collision(file_path: str):
    """
    Checks for subnet collisions in a given file.

    Input:
        file_path (str): Path to the file containing identifier-subnet pairs.
    Output: None (results are printed to the console).
    """
    try:
        subnets = []
        found = False

        with open(file_path, 'r') as file:
            for line in file:
                parts = line.strip().split()
                if len(parts) == 2:
                    identifier, subnet = parts
                    subnet_network = ipaddress.ip_network(subnet, strict=False)

                    for existing_id, existing_subnet in subnets:
                        existing_network = ipaddress.ip_network(existing_subnet, strict=False)
                        if subnet_network.overlaps(existing_network):
                            print(f"Collision: {subnet} ({identifier}), {existing_subnet} ({existing_id})")
                            found = True

                    subnets.append((identifier, subnet))

        if not found:
            print("Found none")

    except FileNotFoundError:
        print(f"Error: File '{file_path}' not found.")
    except PermissionError:
        print(f"Error: No permission to read '{file_path}'.")
    except ValueError as e:
        print(f"Error processing subnet data: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


def main():
    """
    Main function that parses command-line arguments and executes the corresponding functionality.

    Options:
        --collect FILE: Collect logs from Kubernetes pods using a specified image and store them in the given file.
        --check FILE: Check for subnet collisions in the given file.
    """
    parser = argparse.ArgumentParser(description="Utility script for container network inspection and log collection.")
    parser.add_argument("--collect", metavar="FILE", type=str, help="Collect logs from Kubernetes pods into the specified file")
    parser.add_argument("--check-collision", metavar="FILE", type=str, help="Check file for subnet collisions")

    try:
        args = parser.parse_args()

        if args.collect:
            collect_logs_by_image("ip-tool:latest", args.collect)
        elif args.check_collision:
            check_collision(args.check_collision)
        else:
            print(get_container_networks())

    except argparse.ArgumentError as e:
        print(f"Argument error: {str(e)}")
    except Exception as e:
        print(f"Unexpected error: {str(e)}")


if __name__ == "__main__":
    main()
