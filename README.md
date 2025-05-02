# AAS over MQTT

This is an umbrella helm chart that demonstrates interoperation (or lack thereof) between multiple AAS-implementations.
Currently, it hosts two helm dependency charts. One for the FAAAST and one for Eclipse Basyx. The latter hosts an MQTT
broker. The Basyx helm chart is largely copied from upstream - only the values are different. Once these open source 
projects expose their own helm repositories, the entire `charts` folder will be removed.
