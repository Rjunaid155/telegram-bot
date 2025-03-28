#!/bin/bash
echo "Installing dependencies..."
pip install --upgrade pip
pip install git+https://github.com/mempool/mempool-api.git
echo "Installation complete."
