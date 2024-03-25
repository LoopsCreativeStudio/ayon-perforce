# Perforce integration for AYON

[![Release](https://github.com/LoopsCreativeStudio/ayon-perforce/actions/workflows/release.yml/badge.svg?branch=main)](https://github.com/LoopsCreativeStudio/ayon-perforce/actions/workflows/release.yml)

This adds integration to [Perforce Version Control](https://www.perforce.com/products/helix-core).
The project provides two elements to manage Perforce synchronisation for your AYON pipeline:
 * client - The AYON desktop integration.
 * server - The AYON backend Addon.

## Client
This contains Perforce client integration used in AYON launchee which acts as a prelaunch hook to perform a Perforce synchronisation before opening applications.

## Server
Once loaded into the backend, restart your server to update addons and start to config your perforce addon settings.

### Settings
Settings let you define the client behavior by overrriding following P4 config variables:

 * P4PORT
 * P4CLIENT
 * P4USER

In order to execute the synchronization in your pipeline, you have to add hosts that use Perforce remote service like Unreal Editor.

This settings can be set at studio level or projects level in your projects settings.

Currently, you have te configure first your Perforce remote server and client user and workspace folder.

Make sure you have the Perforce folder with p4 executables in your PATH environment variable.


### Versioning

Follow [Semantic Versioning](https://semver.org/) and automate with [python semantic release](https://github.com/python-semantic-release/python-semantic-release)


### Authors

```
LoopsCreativeStudio

https://loopscreativestudio.com/
tech@loopscreativestudio.com
```