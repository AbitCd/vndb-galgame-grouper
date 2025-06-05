@echo off
echo Installing dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install pyinstaller

echo Building executable...
pyinstaller main.spec

echo Done! Check the dist folder for the output.
pause