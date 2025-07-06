pyinstaller FarmCEO.spec
echo "Copying assets..."
cp -r game/assets dist/assets
echo "Renaming dist..."
rm -rf Farm-CEO-Release-Linux64/
mv dist/ Farm-CEO-Release-Linux64/
echo "Removing build..."
rm -rf build