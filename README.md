# Clipboard Sync Manager

Clipboard Sync Manager is a Python-based CLI application designed to facilitate clipboard synchronization between a host and its guests or virtual machines (VMs) through a client-server model. It leverages websockets for real-time communication, enabling seamless sharing of clipboard contents across diverse environments.

## Overview

The project is structured into a client (`client.py`) and a server (`server.py`) component, both written in Python. The `logger.py` module provides logging capabilities. Events such as `register`, `deregister`, and `clipboard` are processed by the server, which manages client connections and clipboard content distribution. The client, upon connecting to the server, listens for clipboard updates and also monitors local clipboard changes to broadcast.

## Features

- **Real-Time Clipboard Synchronization**: Synchronize clipboard contents across machines in real-time.
- **Event-Driven Communication**: Utilizes `register`, `deregister`, and `clipboard` events for managing connections and content distribution.
- **Robust Logging**: The `logger.py` module facilitates detailed logging for events and errors.
- **Systemd Service Support**: Includes systemd service files for easy management (start, stop, enable on boot) of client and server as system services.
- **Distributable Binaries**: Provides PyInstaller specifications for generating standalone executables for both client and server, simplifying deployment.

## Getting Started

### Requirements

- Python 3.6 or higher
- `websockets` Python library
- Linux utilities: `xclip` and `clipcat`

### Quickstart

1. Install the necessary Python packages:
   ```shell
   pip install -r requirements.txt
   ```
2. Start the server using:
   ```shell
   python server.py --address 0.0.0.0 --port 1234
   ```
3. Connect a client to the server:
   ```shell
   python client.py --server <server_ip> --port <port_number>
   ```

### License

Copyright (C) 2024 Michael Weichert.