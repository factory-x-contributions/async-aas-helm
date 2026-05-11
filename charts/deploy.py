#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path
import textwrap

DEFAULT_VAULT = "charts/vault.json"
DEFAULT_VALUES_YAML = "charts/async-aas-helm/values.yaml"
DEFAULT_CHART_PATH = "charts/async-aas-helm"
DEFAULT_VALUES_NEW_YAML = "charts/values.local.yaml"
DEFAULT_RELEASE = "async-aas-helm"
REALM_FILES = [ DEFAULT_CHART_PATH + "/config/fa3st-realm.json", DEFAULT_CHART_PATH + "/config/basyx-realm.json", DEFAULT_CHART_PATH + "/config/rabbitmq-realm.json"]

_PATH_PATTERN = "<path:factory-x-ci-cd/data/async-aas#"


def replacement_strategy(variable_name, vault):
    try:
        return vault[variable_name]
    except KeyError:
        print(f" {variable_name}", end="", flush=True, file=sys.stderr)
        return variable_name


def load_vault(vault_path: str | None) -> dict:
    if vault_path is None:
        print("No vault file provided. Using variable name for every <path...>.", file=sys.stderr)
        return {}

    vault_file = Path(vault_path)
    if not vault_file.exists():
        print(f"Warning: {vault_file} not found. Using variable name for every <path...>.", file=sys.stderr)
        return {}

    try:
        with vault_file.open() as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        print(f"Error: Failed to parse {vault_file}: {e}", file=sys.stderr)
        return {}


def inject_values(to_inject: str, injected: str, vault: dict) -> None:
    with open(to_inject, "r") as templated_fd:
        templated_content = templated_fd.read().splitlines()

    nlines = []
    print(f"\n{to_inject.split('/')[-1]}: following values weren't present in vault:\n[", end="", flush=True)
    for line in templated_content:
        nline = line + "\n"
        while _PATH_PATTERN in nline:
            start, stop = (nline.index("<"), nline.index(">"))

            variable_name = nline[start + len(_PATH_PATTERN) : stop]

            variable = replacement_strategy(variable_name, vault) or variable_name

            nline = f"{nline[:start]}{variable}{nline[stop+1:]}"

        nlines.append(nline)
    print("].\nInjection complete!")
    with open(injected, "w+") as values_new_fd:
        values_new_fd.writelines(nlines)



def tweak_rabbitmq_values(values_path: str) -> None:
    """Adjust RabbitMQ-related settings in the injected values file."""
    p = Path(values_path)
    text = p.read_text()

    # Comment out listeners.tcp
    text = text.replace(
        "    listeners.tcp = none  # disable AMQP",
        "    # listeners.tcp = none  # disable AMQP",
    )

    # Comment out web_mqtt.ws_path
    # text = text.replace(
    #     "    web_mqtt.ws_path = /mqtt  # this MUST be set for Basyx (paho default, non-configurable in basyx)",
    #     "    # web_mqtt.ws_path = /mqtt  # this MUST be set for Basyx (paho default, non-configurable in basyx)",
    # )
    text = text.replace(
        "mqtt.hostname=rabbitmq",
        "mqtt.hostname=rabbitmq-mqtt",
    )
    text = text.replace(
        "mqtt.protocol=wss",
        "mqtt.protocol=tcp"
    )          
    text = text.replace(
        "mqtt.port=443",
        "mqtt.port=1883",
    )


    # Set ingress hostname
    text = text.replace(
        '    hostname: ""  # only for management interface, "disable"',
        '    hostname: "rabbitmq"  # only for management interface, "disable"',
    )

    p.write_text(text)


def run_helm(release: str, namespace: str | None, chart: str, values_file: str, seeding: bool, vault: dict) -> None:
    cmd = [
        "helm",
        "upgrade",
        "--install",
        "--create-namespace",
        release,
        chart,
        "--values",
        values_file,
        "--set",
        f"faaast-service.seeding.enabled={'true' if seeding else 'false'}," 
        f"faaast-service.messageBus.host=tcp://{replacement_strategy('rabbitmq-broker-url', vault)}-mqtt:1883"
    ]
    if namespace:
        cmd.extend(["--namespace", namespace])

    print("\nRunning:", " ".join(cmd), "\n")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Deployment failed.")
        sys.exit(1)


def ensure_rabbitmq_mqtt_service(release: str, namespace: str | None) -> None:
    """Create/patch a Service exposing RabbitMQ MQTT on port 1883."""
    ns = namespace or "default"
    manifest = textwrap.dedent(f"""
    apiVersion: v1
    kind: Service
    metadata:
      name: rabbitmq-mqtt
      namespace: {ns}
      labels:
        app.kubernetes.io/name: rabbitmq-mqtt
        app.kubernetes.io/instance: {release}
    spec:
      selector:
        app.kubernetes.io/name: rabbitmq
        app.kubernetes.io/instance: {release}
      ports:
        - name: mqtt
          port: 1883
          targetPort: 1883
          protocol: TCP
    """).lstrip()

    try:
        subprocess.run(
            ["kubectl", "apply", "-f", "-"],
            input=manifest.encode("utf-8"),
            check=True,
        )
    except subprocess.CalledProcessError:
        print("Failed to create/patch rabbitmq-mqtt Service.", file=sys.stderr)
        sys.exit(1)

def run_helm_uninstall(release: str, namespace: str | None) -> None:
    cmd = ["helm", "uninstall", release]
    if namespace:
        cmd.extend(["--namespace", namespace])

    print("Running:", " ".join(cmd))
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Uninstalling deployment failed.")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="Inject values.yaml with secrets from vault.json and run helm upgrade --install/helm uninstall."
    )
    parser.add_argument(
        "-v",
        "--vault",
        help=f"Path to vault JSON file (optional, default: {DEFAULT_VAULT})",
        default=DEFAULT_VAULT,
    )
    parser.add_argument(
        "-f",
        "--values",
        help=f"Path to input values YAML file (default: {DEFAULT_VALUES_YAML})",
        default=DEFAULT_VALUES_YAML,
    )
    parser.add_argument(
        "-o",
        "--output",
        help=f"Path to injected values YAML file (default: {DEFAULT_VALUES_NEW_YAML})",
        default=DEFAULT_VALUES_NEW_YAML,
    )
    parser.add_argument(
        "-c",
        "--chart",
        help=f"Path to Helm chart (default: {DEFAULT_CHART_PATH})",
        default=DEFAULT_CHART_PATH,
    )
    parser.add_argument(
        "-r",
        "--release",
        help=f"Helm release / deployment name (default: {DEFAULT_RELEASE})",
        default=DEFAULT_RELEASE,
    )
    parser.add_argument(
        "-n",
        "--namespace",
        required=False,
        help="Kubernetes namespace for the Helm release (optional, default: \"default\")",
    )
    parser.add_argument(
        "-x",
        "--cleanup",
        action="store_true",
        help="Uninstall the Helm release and exit",
    )
    parser.add_argument(
        "-s",
        "--seeding",
        required=False,
        help="Use seeding for FA³ST Service (required vault fields: initial-aas-file-name, initial-aas-file-location, initial-aas-github-token)",
    )

    args = parser.parse_args()

    # Summary message
    operation = "cleanup (uninstall)" if args.cleanup else "install"
    ns_text = args.namespace if args.namespace else "(default namespace)"
    vault_text = args.vault if args.vault else f"{DEFAULT_VAULT} (if present, otherwise no vault)"
    print(
        f"Planned operation: {operation}\n"
        f"  release:    {args.release}\n"
        f"  namespace:  {ns_text}\n"
        f"  chart:      {args.chart}\n"
        f"  values in:  {args.values}\n"
        f"  values out: {args.output}\n"
        f"  vault:      {vault_text}\n"
        f"  seed:       {args.seeding}\n"
    )

    try:
        input("Confirm by pressing enter\n")
    except (KeyboardInterrupt, EOFError):
        print("\nOperation cancelled")
        sys.exit(0)

    # If cleanup requested, just uninstall and exit
    if args.cleanup:
        run_helm_uninstall(args.release, args.namespace)
        return

    # Normal inject + install flow
    vault = load_vault(args.vault)
    inject_values(args.values, args.output, vault)
    for realm in REALM_FILES:
        inject_values(realm, realm, vault)

    print("Variable references not present in the vault were replaced with their variable names.")
    print("Example: <path:mypath/morepath#myvar> => myvar")

    tweak_rabbitmq_values(args.output)
    run_helm(args.release, args.namespace, args.chart, args.output, args.seeding, vault)
    # Ensure MQTT TCP Service exists
    ensure_rabbitmq_mqtt_service(args.release, args.namespace)


if __name__ == "__main__":
    main()