# Specification for Messaging with the Asset Administration Shell

## Introduction

The aim of this specification is to define a messaging mechanism through which events concerning resources from the
Asset Administration Shell specification (IDTA-01001, IDTA-01002) can be communicated to interested data consumers.

This specification complements the AAS REST API by introducing a message payload for the events. While the REST
API is designed to specify the synchronous retrieval and manipulation of data, the events enable notifications to data
consumers. Specifically, it ensures that data consumers are immediately informed of any changes to the data in the AAS 
repository, thereby enhancing responsiveness and eliminating the need for frequent polling/scraping of the repository 
to discover data updates.

![MQTT Concept](./artifacts/aas-sync-mqtt-concept.png)

### Message Semantics

