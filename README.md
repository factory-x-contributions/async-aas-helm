# AAS over MQTT

This repository contains material to discuss the current state of asynchronous communication with Asset Administration
Shell payloads. IDTA 01002-3-1 does not specify anything to this regard which is a major inhibitor for use-cases that
require low-overhead, high-veracity messaging. To serve such use-cases in the Factory-X project, this repository hosts
various resources.

1. Runnable Helm Chart

This repo is an umbrella helm chart that demonstrates interoperation (or lack thereof) between multiple AAS-implementations using RabbitMQ as the message broker.
Currently, it hosts two helm dependency charts. One for the FAAAST and one for Eclipse Basyx. The system uses RabbitMQ with MQTT protocol support for messaging. The Basyx helm chart is largely copied from upstream - only the values are different.
Once these open source projects expose their own helm repositories, the entire `charts` folder will be removed.

![aas-async-umbrella.png](./specs/artifacts/aas-async-umbrella.png)

2. Specification Documents

In order to provide implementations with an abstract spec document that they can use to implement, the `specs`
folder contains a set of [asyncAPI](https://www.asyncapi.com/) files that describe in a transport-agnostic manner the
payload and topic structure for AAS messages. There's a human-readable spec [deployed via github pages](https://factory-x-contributions.github.io/async-aas-helm).
The sources can be found on [Github](specs).

3. MongoDB Install

```bash
helm install -n basyx mongodb bitnami/mongodb --version 18.1.1 -f values.mongodb.yaml
```

## Chart Dependencies

This umbrella chart includes the following dependencies:

- **FAAAST Service**: Version 0.1.4 (tag:`cloudevents`, fx-fa³st fork)
- **Eclipse BaSyx v2**: Version 2.0.11  
- **MongoDB**: Version 18.1.1 (MongoDB 8.2.1, digest-pinned for stability)
- **RabbitMQ**: Version 16.0.14

## Prerequisites

- Kubernetes cluster
- Helm 3.x
- Docker (for image pulls)

## Quick Start

1. **Update dependencies:**

   ```bash
   helm dependency update
   ```

2. **Install the chart:**

   ```bash
   helm install async-aas-helm ./charts/async-aas-helm -n <namespace> --create-namespace
   ```

3. **Upgrade existing installation:**

   ```bash
   helm upgrade async-aas-helm ./charts/async-aas-helm -n <namespace>
   ```

## Service Dependencies

The services have the following startup order dependencies:

1. MongoDB (database)
2. RabbitMQ (message broker)  
3. Keycloak (authentication)
4. BaSyx services (AAS registry, discovery, environment)
5. FAAAST service
