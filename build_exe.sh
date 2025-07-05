pyinstaller FarmCEO.spec
echo "Copying assets..."
cp -r game/assets dist/assets
echo "Renaming dist..."
mv dist Farm-CEO-Release
echo "Removing build..."
rm -rf build