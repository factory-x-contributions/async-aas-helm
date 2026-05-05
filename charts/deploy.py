#!/usr/bin/env python3

import argparse
import json
import subprocess
import sys
from pathlib import Path

DEFAULT_VAULT = "charts/vault.json"
DEFAULT_VALUES_YAML = "charts/async-aas-helm/values.yaml"
DEFAULT_VALUES_NEW_YAML = "charts/values_injected.yaml"
DEFAULT_CHART_PATH = "./charts/async-aas-helm"
DEFAULT_RELEASE = "async-aas-helm"

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


def inject_values(values_yaml: str, output_yaml: str, vault: dict) -> None:
    with open(values_yaml, "r") as templated_fd:
        templated_content = templated_fd.read().splitlines()

    nlines = []
    print("Injection could not find the following variables in the vault: [", end="", flush=True)
    for line in templated_content:
        nline = line + "\n"
        while _PATH_PATTERN in nline:
            start, stop = (nline.index("<"), nline.index(">"))

            variable_name = nline[start + len(_PATH_PATTERN) : stop]

            variable = replacement_strategy(variable_name, vault) or variable_name

            nline = f"{nline[:start]}{variable}{nline[stop+1:]}"

        nlines.append(nline)
    print("].\nInjection complete!")
    with open(output_yaml, "w+") as values_new_fd:
        values_new_fd.writelines(nlines)


def run_helm(release: str, namespace: str | None, chart: str, values_file: str, upgrade: bool) -> None:
    cmd = [
        "helm",
        "upgrade" if upgrade else "install",
        release,
        chart,
        "--values",
        values_file,
    ]
    if namespace:
        cmd.extend(["--namespace", namespace])

    print("\nRunning:", " ".join(cmd), "\n")
    try:
        subprocess.run(cmd, check=True)
    except subprocess.CalledProcessError:
        print("Deployment failed.")
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
        description="Inject values.yaml with secrets from vault.json and run helm install/upgrade/uninstall."
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
        "-u",
        "--upgrade",
        action="store_true",
        help="Use 'helm upgrade' instead of 'helm install'",
    )
    parser.add_argument(
        "-x",
        "--cleanup",
        action="store_true",
        help="Uninstall the Helm release and exit",
    )

    args = parser.parse_args()

    # Summary message
    operation = "cleanup (uninstall)" if args.cleanup else ("upgrade" if args.upgrade else "install")
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

    # Normal inject + install/upgrade flow
    vault = load_vault(args.vault)
    inject_values(args.values, args.output, vault)
    run_helm(args.release, args.namespace, args.chart, args.output, args.upgrade)


if __name__ == "__main__":
    main()