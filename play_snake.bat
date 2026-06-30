@echo off
cd /d "%~dp0"
echo === Zoya Snake Game ===
echo.

pip show zoya-lang >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing Zoya...
    pip install -e .
)

pip show pygame-ce >nul 2>&1
if %errorlevel% neq 0 (
    echo Installing pygame-ce...
    pip install pygame-ce
)

echo Starting Snake - use arrow keys to move
python -m zoya examples\snake.zoya
pause
