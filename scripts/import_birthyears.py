from pathlib import Path
import sys
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from clubscout.build import build
from clubscout.birthyears import import_uploads

root=Path(__file__).resolve().parents[1]
build(root)
print(import_uploads(root))
build(root)
