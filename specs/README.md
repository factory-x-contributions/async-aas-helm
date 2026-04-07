## Specification for Messaging with the Asset Administration Shell

# Introduction
The aim of this specification is to define a messaging mechanism through which events concerning resources from the Asset Administration Shell specification (IDTA-01001, IDTA-01002) can be communicated to interested data consumers.

This specification complements the AAS REST API by introducing a message payload for the events. While the REST API is designed to specify the synchronous retrieval and manipulation of data, the events enable notifications to data consumers. Specifically, it ensures that data consumers are immediately informed of any changes to the data in the AAS repository, thereby enhancing responsiveness and eliminating the need for frequent polling/scraping of the repository to discover data updates.

![MQTT Concept](./artifacts/aas-sync-mqtt-concept.svg)

## Normative Disclaimer 
The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

## Message Semantics

All messages in this specification conform to the CloudEvents 1.0 envelope format and carry a payload indicating a state change in an AAS repository. Each message is classified by the resource type it concerns and the lifecycle event that triggered it. Providers MUST use the payload's `type` field to signal the nature of the event to the consumers allowing them to decide on processing it without inspecting the rest of the payload.

---

## Events

Events represent notifications about changes that occur in an AAS repository. 
They are generated whenever the state of an AAS, a Submodel (SM), or a SubmodelElement (SME) changes.

Events allow external systems to observe these changes without continuously polling the repository. 
Instead, subscribers receive notifications through the messaging infrastructure whenever relevant updates occur.

This section clarifies when events should be emitted and how the different event types should be used.

### When Events Should Be Emitted

An implementation MUST emit an event whenever an observable state of the AAS repository changes.

Observable changes include:

- creation of AASs 
- updates to AASs
- deletion of AASs 
- creation of SMs or SMEs
- updates to SMs or SMEs 
- deletion of SMs or SMEs 

An event SHOULD NOT be emitted if an operation does not actually change the stored data.

### Generic Event Types

The messaging model distinguishes several event types that describe the type of change that occurred.

The following event types are used:

- `ElementCreated`
- `ElementDeleted`
- `ElementUpdated`
- `ValueChanged`

The chosen event type should reflect the semantic meaning of the change.

---

## Asset Administration Shell Events

#### AAS Element Created

`io.admin-shell.events.v1.created` — Emitted when a new AAS is persisted in the repository. If present, the `data` property contains the full representation of the newly created AAS, allowing consumers to immediately act on it without issuing a follow-up retrieval request. This event MUST be emitted exactly once per AAS creation and MUST NOT be emitted for subsequent modifications to the same AAS. The `dataschema` property can only reference the AAS metamodel element.

**Example:**
```REST
POST /shells
```

#### AAS Element Updated

`io.admin-shell.events.v1.updated` — Emitted when the metadata or structural composition of an existing AAS changes. Changes that trigger this event include modifications to the shell's administrative information, asset information, or the set of SM references it holds. If present, the `data` property contains the updated element in its entirety after the change. Consumers SHOULD treat receipt of this event as an authoritative replacement for any previously held state of the element identified by the same identifier. The `dataschema` property can only reference elements with their own HTTP endpoint and schema, for example `asset-information` or `submodel-refs`.

**Example:**
```REST
PATCH /shells/{id}
```

## Submodel Events

#### Submodel Created

`io.admin-shell.events.v1.created` — Emitted when a new SM is persisted in the repository. If present, the `data` property contains the full SM representation, including its semantic identification and all SM elements present at creation time. This event MUST be emitted exactly once when a SM is first created and MUST NOT be emitted for subsequent changes to that SM. The `dataschema` property can only reference the SM metamodel element.

**Example:**
```REST
POST /submodels
```

#### Submodel Updated

`io.admin-shell.events.v1.updated` — Emitted when the metadata of an existing SM changes. This event concerns structural or descriptive changes at the SM level itself — such as changes to its semantic identification, administrative information, or kind — and is distinct from any changes to individual SME within it. If present, the `data` property contains the updated SM representation. Consumers SHOULD treat receipt of this event as an authoritative replacement for any previously held state of the shell identified by the same identifier. The `dataschema` property can only reference the SM metamodel element as SMEs are handled elsewhere.

**Example:**
```REST
PATCH /submodels/{id}
```

#### Submodel Deleted

`io.admin-shell.events.v1.deleted` — Emitted when a SM is permanently removed from the repository. The AAS payload is absent; the identity of the deleted resource is conveyed through the `source` property in the envelope. Consumers MUST consider any locally cached state for the identified SM invalid upon receipt of this event.

**Example:**
```REST
DELETE /submodels/{id}
```

## SubmodelElement Events

#### SubmodelElement Created

`io.admin-shell.events.v1.created` — Emitted when a new SME is added to an existing Submodel. The source reference in the envelope identifies the containing element or Submodel into which the new element was inserted. The `data` property contains the full representation of the newly created SME. This event MUST be emitted exactly once per element creation.

**Example:**
```REST
POST /submodels/{id}/submodelElements
```

#### Value Changed

`io.admin-shell.events.v1.valueChanged` — Emitted when the value of a DataElement changes while the element itself remains structurally unmodified. If any other attribute changes, a SME Updated event is emitted. If present, the `data` property contains the SME in its updated state. Consumers SHOULD use this event as the primary mechanism for tracking live data updates in an AAS deployment.

**Example:**
```REST
PATCH /submodelElements/power/value
value = 10
```

#### SubmodelElement Updated

`io.admin-shell.events.v1.updated` — Emitted when the structure or metadata of an existing SME changes in a way other than a pure value change. This includes changes to semantic identification, qualifiers, or category. If present, the `data` property contains the updated element representation. Consumers SHOULD replace any previously held state of the identified element upon receipt.

**Example:**
```REST
PATCH /submodelElements/{id}
{
  "idShort": "newName"
}
```

#### SubmodelElement Deleted

`io.admin-shell.events.v1.deleted` — Emitted when a SME is removed from its containing Submodel, SubmodelElementList or SubmodelElementCollection. The `source` property in the envelope identifies the deleted SME. The SME payload is absent from the event. Consumers MUST invalidate any locally cached state for the deleted element upon receipt.

**Example:**
```REST
DELETE /submodelElements/{id}
```

#### Operation Invoked

`io.admin-shell.events.v1.invoked` — Emitted when an Operation SME is invoked by a client. If present, the `data` property contains the Operation element including the InputArguments and InoutputArguments supplied by the invoking client. Receipt of this event does not imply that the Operation has completed or succeeded.


#### Operation Finished

`io.admin-shell.events.v1.finished` — Emitted when an Operation completes, regardless of whether it succeeded or failed. If present, the `data` property contains the InoutputArguments and OutputArguments as produced as the operation result. Consumers correlate this event with a Operation using the `source` property in the envelope. This event MUST be emitted exactly once per completed Operation.




