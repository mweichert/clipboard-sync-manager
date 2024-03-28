#!/bin/bash

# Build the server redistributable
echo "Building the server redistributable..."
pyinstaller server.spec
if [ $? -eq 0 ]; then
    echo "Server redistributable built successfully."
else
    echo "Failed to build the server redistributable."
    exit 1
fi

# Build the client redistributable
echo "Building the client redistributable..."
pyinstaller client.spec
if [ $? -eq 0 ]; then
    echo "Client redistributable built successfully."
else
    echo "Failed to build the client redistributable."
    exit 1
fi