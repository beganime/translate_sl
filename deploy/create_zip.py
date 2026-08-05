import sys
import zipfile
from pathlib import Path


source = Path(sys.argv[1]).resolve()
target = Path(sys.argv[2]).resolve()

with zipfile.ZipFile(target, "w", compression=zipfile.ZIP_DEFLATED, compresslevel=6) as archive:
    for path in sorted(source.rglob("*")):
        if path.is_file():
            archive.write(path, path.relative_to(source).as_posix())

print(target)
