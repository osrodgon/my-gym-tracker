#!/bin/bash

# 1. Update pip (optional but good practice)
python3 -m pip install --upgrade pip

# 2. Install dependencies
python3 -m pip install -r requirements.txt

# 3. Install system dependencies
sudo apt-get update
sudo apt-get install -y clang cmake ninja-build pkg-config libgtk-3-dev liblzma-dev

# 4. Install opencode
curl -fsSL https://opencode.ai/install | bash
