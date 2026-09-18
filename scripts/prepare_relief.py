"""Convert Natural Earth's unmodified global raster to a web delivery format."""
import argparse
from pathlib import Path
from zipfile import ZipFile
from PIL import Image

parser = argparse.ArgumentParser()
parser.add_argument('archive', type=Path)
args = parser.parse_args()
target = Path(__file__).resolve().parents[1] / 'docs/assets/earth-relief.webp'
with ZipFile(args.archive) as archive:
    name = next(n for n in archive.namelist() if n.lower().endswith('.tif'))
    with archive.open(name) as source, Image.open(source) as raster:
        raster.convert('RGB').save(target, 'WEBP', quality=85, method=6)
        print(raster.size, target, target.stat().st_size)
