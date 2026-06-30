@echo off
cd /d "%~dp0"
pip install -e . >nul 2>&1
pip install pygame-ce >nul 2>&1
cls
echo ========================================
echo    ZOYA SNAKE GAME
echo    Use arrow keys to move
echo    Press X on window to quit
echo ========================================
echo.
python -m zoya examples\snake.zoya
pause
