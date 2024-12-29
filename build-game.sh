#!/bin/bash

# Step 1: Create necessary directories if they don't exist
mkdir -p docker/{buildozer,gradle,ndk}

# Step 5: Build the game with Buildozer
sudo docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "$(pwd)/docker/gradle":/home/user/.gradle \
    -v "$(pwd)/game":/home/user/hostcwd \
    -v "/home/captaindeathead/.buildozer":/home/user/.buildozer \
    kivy/buildozer -v android debug
