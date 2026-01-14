# Testing Guide for FA³ST Service with FA³ST Registry Integration

## Overview

This guide describes the integration of FA³ST Service with an AAS Registry following Platform Industrie 4.0 standards (FA³ST Registry).

## Registry Integration

### What is the RegistryClient?

The `RegistrySynchronization` module in FA³ST Service enables automatic synchronization of Asset Administration Shells (AAS) and Submodels with an external registry.

**The RegistryClient communicates with an AAS Registry following Platform Industrie 4.0 standards.**

### Supported APIs

The RegistryClient uses the standard Swagger APIs of Platform Industrie 4.0:

#### AAS Registry API
- **Endpoint**: `/api/v3.0/shell-descriptors`
- **Documentation**: https://factory-x-contributions.github.io/async-aas-helm/aas-repository/
- **Operations**:
  - POST: Register new AAS Descriptors
  - PUT: Update existing AAS Descriptors
  - DELETE: Remove AAS Descriptors

#### Submodel Registry API
- **Endpoint**: `/api/v3.0/submodel-descriptors`
- **Documentation**: 
  - https://factory-x-contributions.github.io/async-aas-helm/submodel-repository/
  - https://factory-x-contributions.github.io/async-aas-helm/submodel-repository-submodelelement/
- **Operations**:
  - POST: Register new Submodel Descriptors
  - PUT: Update existing Submodel Descriptors
  - DELETE: Remove Submodel Descriptors

## Configuration

### Helm Values

In `values.yaml` you can configure the Registry URLs:

```yaml
registry:
  # Base URL for the AAS Registry (FA³ST Registry) following Platform Industrie 4.0
  aasRegistryBaseUrl: "https://faaast-registry"
  # Base URL for the Submodel Registry (FA³ST Registry) following Platform Industrie 4.0
  submodelRegistryBaseUrl: "https://faaast-registry"
```

### Internal Service Communication

If you deploy the Registry within the same Kubernetes cluster, you can use internal service URLs:

```yaml
registry:
  aasRegistryBaseUrl: "https://faaast-registry"
  submodelRegistryBaseUrl: "https://faaast-registry"
```

## How It Works

### Event-based Synchronization

The RegistryClient listens on the internal Event Bus (MQTT) for the following Cloud Events according to AAS Async API specification:

1. **AAS Created Event**: Automatically registers a new AAS Descriptor in the Registry
2. **Submodel Created Event**: Automatically registers a new Submodel Descriptor in the Registry
3. **AAS Updated Event**: Updates an existing AAS Descriptor in the Registry
4. **Submodel Updated Event**: Updates an existing Submodel Descriptor in the Registry
5. **AAS Deleted Event**: Removes an AAS Descriptor from the Registry
6. **Submodel Deleted Event**: Removes a Submodel Descriptor from the Registry

### Startup Behavior

On startup of FA³ST Service, all existing AAS and Submodels are automatically registered in the configured Registry.

### Shutdown Behavior

On shutdown of FA³ST Service, all AAS and Submodels are automatically removed from the Registry (unregistration).

## Testing

### Prerequisites

1. Access to a Kubernetes Cluster
2. Helm 3.x installed
3. Access to the FA³ST Registry (either public or in-cluster)

### Installation

```bash
# Install the chart
helm install faaast-service ./charts/faaast-service \
  --set registry.aasRegistryBaseUrl="https://faaast-registry" \
  --set registry.submodelRegistryBaseUrl="https://faaast-registry"
```

### Verification

#### 1. Check FA³ST Service Logs

```bash
kubectl logs -f deployment/faaast-service
```

You should see log entries like:

```
INFO  - Registering all AssetAdministrationShells to the following registries:
INFO  -      https://faaast-registry
INFO  - Registering all submodels to the following registries:
INFO  -      https://faaast-registry
```

#### 2. Check the Registry

Query all registered AAS:

```bash
curl -X GET "https://faaast-registry/api/v3.0/shell-descriptors"
```

Query all registered Submodels:

```bash
curl -X GET "https://faaast-registry/api/v3.0/submodel-descriptors"
```

#### 3. Test Automatic Registration

Create a new AAS via FA³ST Service API:

```bash
# Example: POST to FA³ST Service
curl -X POST "http://faaast-service:8080/api/v3.0/shells" \
  -H "Content-Type: application/json" \
  -d '{
    "id": "https://example.com/ids/aas/test123",
    "idShort": "TestAAS",
    "assetInformation": {
      "assetKind": "Instance",
      "globalAssetId": "https://example.com/ids/asset/test123"
    }
  }'
```

Then verify that the AAS automatically appears in the Registry:

```bash
curl -X GET "https://faaast-registry/api/v3.0/shell-descriptors" | jq '.result[] | select(.id == "https://example.com/ids/aas/test123")'
```

## Cloud Events Specification

The complete specification of the AAS Async API can be found here:

- **AAS Events**: [async-aas-helm/specs/asyncapi_spec_aas.yaml](https://github.com/factory-x-contributions/async-aas-helm/tree/main/specs)
- **Submodel Events**: [async-aas-helm/specs/asyncapi_spec_submodel.yaml](https://github.com/factory-x-contributions/async-aas-helm/tree/main/specs)
- **Submodel Element Events**: [async-aas-helm/specs/asyncapi_spec_submodelelement.yaml](https://github.com/factory-x-contributions/async-aas-helm/tree/main/specs)

## Further Information

- **FA³ST Service Documentation**: https://faaast-service.readthedocs.io/
- **BaSyx Project**: https://www.eclipse.org/basyx/
- **Platform Industrie 4.0**: https://www.plattform-i40.de/
- **Factory-X Async AAS Helm**: https://github.com/factory-x-contributions/async-aas-helm
