#!/bin/bash

mkdir -p docker/{buildozer,gradle}
sudo docker run --rm \
    -u "$(id -u):$(id -g)" \
    -v "$(pwd)/docker/buildozer":/home/user/.buildozer \
    -v "$(pwd)/docker/gradle":/home/user/.gradle \
    -v "$(pwd)/game":/home/user/hostcwd \
    kivy/buildozer -v android debug
