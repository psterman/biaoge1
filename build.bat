@echo off
echo Cleaning up previous builds...
rmdir /s /q build dist
del /f /q *.spec

echo Creating virtual environment...
python -m venv venv
call venv\Scripts\activate

echo Installing requirements...
python -m pip install --upgrade pip
pip install -r requirements.txt

echo Building executable...
pyinstaller --clean ^
           --windowed ^
           --onefile ^
           --hidden-import PIL ^
           --hidden-import PIL._imagingtk ^
           --hidden-import PIL._tkinter_finder ^
           icon_downloader_gui.py ^
           --name "Icon Downloader"

echo Cleaning up...
call venv\Scripts\deactivate
rmdir /s /q venv

echo Done!
if exist "dist\Icon Downloader.exe" (
    echo Build successful! Executable is in the dist folder.
) else (
    echo Build failed! Please check the error messages above.
)
pause 