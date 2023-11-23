from pathlib import Path
from django.contrib.gis.utils import LayerMapping
from .models import Farm

farm_mapping = {
    'farm_id': 'farm_id',
    'crop': 'crop',
    'size': 'Size',
    'geom': 'MULTIPOLYGON',
}

benue_farm_shp = Path(__file__).resolve().parent/'shapefile'/'aoi'/'Benue.shp'

def run(verbose=True):
    lm = LayerMapping(Farm, benue_farm_shp, farm_mapping, transform=False)
    lm.save(strict=True, verbose=verbose)