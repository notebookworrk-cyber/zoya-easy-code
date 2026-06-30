import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from zoya import run

path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "examples", "snake.zoya")
with open(path, "r", encoding="utf-8") as f:
    source = f.read()
run(source, path)
