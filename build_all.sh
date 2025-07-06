echo "Building Linux..."
./build_linux.sh
zip -r Farm-CEO-Release-Linux64.zip Farm-CEO-Release-Linux64

echo "Building Windows..."
./build_windows.sh
zip -r Farm-CEO-Release-Win64.zip Farm-CEO-Release-Win64

echo "Building Android..."
cd game
buildozer -v android debug