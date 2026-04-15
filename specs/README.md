# Specification for Messaging with the Asset Administration Shell

## Introduction

The aim of this specification is to define a messaging mechanism through which events concerning resources from the Asset Administration Shell specification (IDTA-01001, IDTA-01002) can be communicated to interested data consumers.

This specification complements the AAS REST API by introducing a message payload for the events. 
While the REST API is designed to specify the synchronous retrieval and manipulation of data, the events enable notifications to data consumers. 
Specifically, it ensures that data consumers are immediately informed of any changes to the data in the AAS repository, thereby enhancing responsiveness and eliminating the need for frequent polling/scraping of the repository to discover data updates.

![MQTT Concept](./artifacts/aas-sync-mqtt-concept.svg)

### Normative Disclaimer 
The key words **MUST**, **MUST NOT**, **SHOULD**, **SHOULD NOT**, and **MAY** in this document are to be interpreted as described in RFC 2119.

### Message Semantics

All messages in this specification conform to the CloudEvents 1.0 envelope format and carry a payload indicating a state change in an AAS repository. 
Each message is classified by the resource type it concerns and the lifecycle event that triggered it. 
Providers MUST use the payload's `type` field to signal the nature of the event to the consumers allowing them to decide on processing it without inspecting the rest of the payload.

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

### Generic AAS Interfaces

[IDTA](https://industrialdigitaltwin.org/) has specified generic interfaces for AAS and its corresponding software: [Details of the AAS, Part 2: Application Programming Interfaces](https://industrialdigitaltwin.io/aas-specifications/IDTA-01002/v3.1.1/query-language.html). 
The events in this repo are based on these abstract interfaces. 

![Specification](./artifacts/aasid-part2.png)

The specified generic interface methods are (based on, but not limited to, HTTP REST):

- `GET`: Returning a single resource based on an identifier.
- `GETALL`: Returning a list of resources.  
- `QUERY`: Returning a list of resources based on conditions based on a query language. 
- `PUT`: Replacing an existing resource or creating, if not found. 
- `PUTBULK`: Replacing multiple existing resources. 
- `POST`: Creating a new resource. 
- `POSTBULK`: Creating multiple new resources.
- `PATCH`: Updating an existing resource (e.g., changing a value). 
- `DELETE`: Deleting a single resource based on an identifier.
- `DELETEBULK`: Deleting multiple existing resources. 
- `INVOKE`: Invoking an operation.
- `INVOKEASYNC`: Asyncronously invoking an operation.
- `SEARCHALL`: Returning a list of resources based on asset links.

These interface methods are applied to all kinds of AAS-related resources, i.e. including Asset Administration Shells, Asset, Submodels, Submodel Elements, Descriptors, References, etc. - forming interface operations, e.g. `GetAllSubmodels`.  
Qualifiers define how the operation is carried out, e.g. `ById` or `ByPath`.
For instance, the operation for replacing a Submodel Element builds the operation `PutSubmodelElementByPath` *(Creates a new or replaces an existing submodel element at a specified path within the submodel element hierarchy)*.
The operation `DeleteAssetAdministrationShellById` deletes an AAS based on the unique AAS identifier.

### Relations of Event Types to AAS Interfaces

As specified before, this event-based messaging method for the AAS addresses following events: `ElementCreated`, `ElementDeleted`, `ElementUpdated`, `ValueChanged`. 
That means that some of the generic AAS interfaces are not utilized in this project, e.g. every operation featuring `GET`. 
Relevant for the asyncrounous event messaging remain: 

- `PUT`
- `POST`
- `PATCH`
- `DELETE`

However, a simple matching between the event `ElementUpdated` & the interface `PUT` (as well as between `ElementDeleted` & `DELETE`, `ElementCreated` & `POST` and `ValueCahnged` & `PATCH`) is not feasible.
Example: `PutAssetAdministrationShell` could cause `ElementUpdated` or `ElementDeleted` & `ElementCreated`, depending on whether ID of the AAS is new. 

---

## Asset Administration Shell Events

### AAS Element Created

`io.admin-shell.events.v1.created` — Emitted when a new AAS is persisted in the repository. 
If present, the `data` property contains the full representation of the newly created AAS, allowing consumers to immediately act on it without issuing a follow-up retrieval request. 
This event MUST be emitted exactly once per AAS creation and MUST NOT be emitted for subsequent modifications to the same AAS. 
The `dataschema` property can only reference the AAS metamodel element.

**HTTP REST Example:**
```REST
POST /shells
```

**The following interface operations will emit this event:**

- `PostAssetAdministrationShell`

    Creates a new Asset Administration Shell Descriptor, i.e., registers an AAS

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Administration Shell object*  | Status code*   |
    |   | 	Created Asset Administration Shell*   |
    

- `PutAssetAdministrationShell` 
*(in case an AAS with the ID specified in the payload is not existing yet)*

    Creates or replaces an existing Asset Administration Shell Descriptor, i.e., replaces registration information

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Administration Shell object*  | Status code*   |
    |   | 	Replaced Asset Administration Shell   |

- `PutAssetAdministrationShellById` 
*(in case an AAS with the ID specified in the operation (e.g., URL for HTTP REST) is not existing yet)*

    Creates or replaces an existing Asset Administration Shell

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Administration Shell object*  | Status code*   |
    |   | 	Replaced Asset Administration Shell   |

_("*" indicates a mandatory parameter)_


### AAS Element Updated

`io.admin-shell.events.v1.updated` — Emitted when the metadata or structural composition of an existing AAS changes. 
Changes that trigger this event include modifications to the AAS's administrative information, asset information, or the set of SM references it holds. 
If present, the `data` property contains the updated element in its entirety after the change. 
Consumers SHOULD treat receipt of this event as an authoritative replacement for any previously held state of the element identified by the same identifier. 
The `dataschema` property can only reference elements with their own HTTP endpoint and schema, for example `asset-information` or `submodel-refs`.

**HTTP REST Example:**
```REST
PATCH /shells/{id}
```

**The following interface operations will emit this event:**

- `PutAssetAdministrationShell` 
*(in case an AAS with the ID specified in the payload is not existing yet)*

    Creates or replaces an existing Asset Administration Shell Descriptor, i.e., replaces registration information

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Administration Shell object*  | Status code*   |
    |   | 	Replaced Asset Administration Shell   |

- `PutAssetAdministrationShellById` 
*(in case an AAS with the ID specified in the operation (e.g., URL for HTTP REST) is not existing yet)*

    Creates or replaces an existing Asset Administration Shell

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Administration Shell object*  | Status code*   |
    |   | 	Replaced Asset Administration Shell   |


- `PutAssetInformation`
    
    Replaces the Asset Information

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Asset Information object*  | Status code*   |
    
- `PutThumbnail`

    Replaces the thumbnail file

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Thumbnail file*  | Status code*   |

- `DeleteThumbnail`

    Deletes the thumbnail

    | Input Parameter | Output Parameter |
    |----------|----------|
    |  | Status code*   |

- `PostSubmodelReference`

    Creates a Submodel Reference at the Asset Administration Shell

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Reference to the Submodel*  | Status code*   |
    |  | Created Submodel Reference*   |

- `DeleteSubmodelReference`

    Deletes the Submodel Reference from the Asset Administration Shell

    | Input Parameter | Output Parameter |
    |----------|----------|
    | The unique ID of the Submodel for the reference to be deleted*  | Status code*   |


_("*" indicates a mandatory parameter)_

<!-- If submodel is newly created, does it automatically create a submodel reference eithin the AAS, i.e. updating the AAS? -->

## Submodel Events

### Submodel Created

`io.admin-shell.events.v1.created` — Emitted when a new SM is persisted in the repository. 
If present, the `data` property contains the full SM representation, including its semantic identification and all SM elements present at creation time. 
This event MUST be emitted exactly once when a SM is first created and MUST NOT be emitted for subsequent changes to that SM. 
The `dataschema` property can only reference the SM metamodel element.

**HTTP REST Example:**
```REST
POST /submodels
```

**The following interface operations will emit this event:**

- `PostSubmodel` 

    Creates a new Submodel. The id of the new submodel must be set in the payload.

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Created Submodel*   |

- `PutSubmodel`
*(in case a SM with the specified ID is not existing yet)*

    Replaces the Submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Replaced submodel*   |

_("*" indicates a mandatory parameter)_

### Submodel Updated

`io.admin-shell.events.v1.updated` — Emitted when the metadata of an existing SM changes. 
This event concerns structural or descriptive changes at the SM level itself — such as changes to its semantic identification, administrative information, or kind — and is distinct from any changes to individual SME within it. 
If present, the `data` property contains the updated SM representation. 
Consumers SHOULD treat receipt of this event as an authoritative replacement for any previously held state of the shell identified by the same identifier. 
The `dataschema` property can only reference the SM metamodel element as SMEs are handled elsewhere.

**HTTP REST Example:**
```REST
PATCH /submodels/{id}
```

**The following interface operations will emit this event:**

- `PatchSubmodel`

    Replaces the Submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Updated submodel*   |

- `PatchSubmodelById`

    Updates an existing submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Updated  submodel*   |

- `PutSubmodel`
*(in case a SM with the specified ID is already existing)*

    Replaces the Submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Replaced submodel*   |

_("*" indicates a mandatory parameter)_

<!-- If a new SubmodelElement is created (PostSubmodelElement) or deleted (DeleteSubmodelElementByPath), does this update the Submodel itself? -->

### Submodel Deleted

`io.admin-shell.events.v1.deleted` — Emitted when a SM is permanently removed from the repository. 
The AAS payload is absent; the identity of the deleted resource is conveyed through the `source` property in the envelope. 
Consumers MUST consider any locally cached state for the identified SM invalid upon receipt of this event.

**HTTP REST Example:**
```REST
DELETE /submodels/{id}
```

**The following interface operations will emit this event:**

- `DeleteSubmodelById`

    Deletes a Submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | The Submodel’s unique ID*  | Status code*   |

- `PutSubmodel`
*(in case a SM with the specified ID is already existing)*

    Replaces the Submodel

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel object*  | Status code*   |
    |   |  Replaced submodel*   |

_("*" indicates a mandatory parameter)_

## SubmodelElement Events

### SubmodelElement Created

`io.admin-shell.events.v1.created` — Emitted when a new SME is added to an existing Submodel. 
The source reference in the envelope identifies the containing element or Submodel into which the new element was inserted. 
The `data` property contains the full representation of the newly created SME. 
This event MUST be emitted exactly once per element creation.

**HTTP REST Example:**
```REST
POST /submodels/{id}/submodelElements
```

**The following interface operations will emit this event:**

- `PostSubmodelElement`

    Creates a new submodel element as a child of the submodel. The idShort of the new submodel element must be set in the payload.

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    |   |  Created submodel element*   |

- `PostSubmodelElementByPath`

    Creates a new submodel element at a specified path within the submodel element hierarchy. The idShort of the new submodel element must be set in the payload for non-identifiable Referables not being a direct child of a SubmodelElementList. For Elements being a direct child of a SubmodelElementList the input parameter index must be specified.

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element under which the new SubmodelElement shall be added*  |  Created submodel element*   |

- `PutSubmodelElementByPath`
*(in case a SME with the ID specified in the operation (e.g., URL for HTTP REST) is not existing yet)*

    Replaces an existing submodel element or creates a new submodel element at a specified path within the submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element which shall be replaced*  | New state of the submodel element   |

_("*" indicates a mandatory parameter)_

### Value Changed

`io.admin-shell.events.v1.valueChanged` — Emitted when the value of a DataElement changes while the element itself remains structurally unmodified. 
If any other attribute changes, a SME Updated event is emitted. 
If present, the `data` property contains the SME in its updated state. 
Consumers SHOULD use this event as the primary mechanism for tracking live data updates in an AAS deployment.

**HTTP REST Example:**
```REST
PATCH /submodelElements/power/value
value = 10
```

**The following interface operations will emit this event:**

- `PatchSubmodelElementByPath`

    Updates an existing submodel element or creates a new submodel element at a specified path within the submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element*  | Updated submodel element   |
    | Defines the format of the input* |   |

- `PatchSubmodelElementValueByPath`

    Sets the value of the submodel element at a specified path according to the ValueOnly-serialization as defined in [1]

    | Input Parameter | Output Parameter |
    |----------|----------|
    | The new value of the submodel element*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element*  |  |

- `PutSubmodelElementByPath`
*(in case a SME with the specified ID is already existing)*

    Replaces an existing submodel element or creates a new submodel element at a specified path within the submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element which shall be replaced*  | New state of the submodel element |

_("*" indicates a mandatory parameter)_

### SubmodelElement Updated

`io.admin-shell.events.v1.updated` — Emitted when the structure or metadata of an existing SME changes in a way other than a pure value change. 
This includes changes to semantic identification, qualifiers, or category. 
If present, the `data` property contains the updated element representation. Consumers SHOULD replace any previously held state of the identified element upon receipt.

**HTTP REST Example:**
```REST
PATCH /submodelElements/{id}
{
  "idShort": "newName"
}
```

**The following interface operations will emit this event:**

- `PutSubmodelElementByPath`

    Replaces an existing submodel element or creates a new submodel element at a specified path within the submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element which shall be replaced*  | New state of the submodel element |

_("*" indicates a mandatory parameter)_

### SubmodelElement Deleted

`io.admin-shell.events.v1.deleted` — Emitted when a SME is removed from its containing Submodel, SubmodelElementList or SubmodelElementCollection. 
The `source` property in the envelope identifies the deleted SME. 
The SME payload is absent from the event. 
Consumers MUST invalidate any locally cached state for the deleted element upon receipt.

**HTTP REST Example:**
```REST
DELETE /submodelElements/{id}
```

**The following interface operations will emit this event:**

- `DeleteSubmodelElementByPath`

    Deletes a submodel element at a specified path within submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | idShortPath via relative Reference/Keys to a submodel element*  | Status code*   |

- `PutSubmodelElementByPath`
*(in case a SME with the specified ID is already existing)*

    Replaces an existing submodel element or creates a new submodel element at a specified path within the submodel element hierarchy

    | Input Parameter | Output Parameter |
    |----------|----------|
    | Submodel element object*  | Status code*   |
    | idShortPath via relative Reference/Keys to a submodel element which shall be replaced*  | New state of the submodel element |

#### Operation Invoked

`io.admin-shell.events.v1.invoked` — Emitted when an Operation SME is invoked by a client. 
If present, the `data` property contains the Operation element including the InputArguments and InoutputArguments supplied by the invoking client. 
Receipt of this event does not imply that the Operation has completed or succeeded.

<!-- Invoking Operations are not specified in the Event Types -->

#### Operation Finished

`io.admin-shell.events.v1.finished` — Emitted when an Operation completes, regardless of whether it succeeded or failed. 
If present, the `data` property contains the InoutputArguments and OutputArguments as produced as the operation result. 
Consumers correlate this event with a Operation using the `source` property in the envelope. 
This event MUST be emitted exactly once per completed Operation.

<!-- Invoking Operations are not specified in the Event Types -->
