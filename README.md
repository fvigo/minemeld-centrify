# minemeld-centrify

This repo contains the code for the MineMeld extension for Centrify.

The extension currently includes a single MineMeld Output node that enables the remediation use case: once an indicator of type "user-id" is sent to the Output node, the module invokes Centrify's API to add the user to a Centrify role (i.e. Quarantine).

The configuration can be set through the Web UI. Parameters include the Centrify tenant and Quarantine Role.

# EXPERIMENTAL

This software is experimental, use at your own risk!

