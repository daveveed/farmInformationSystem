import ee
from . models import Farm
ee.Initialize()

def ndvi(start_date, end_date, farm_id):
        # image collection
        s2 = ee.ImageCollection("COPERNICUS/S2")
        geometry = Farm.objects.get(farm_id=farm_id).geom
        coords = list(geometry.coords[0])
        geometry = ee.Geometry.Polygon(coords)
#         geom_ = ee.Geometry.Polygon([
#     [[82.60642647743225, 27.16350437805251],
#      [82.60984897613525, 27.1618529901377],
#      [82.61088967323303, 27.163695288375266],
#      [82.60757446289062, 27.16517483230927]]
# ])
        

        filtered = s2.filter(ee.Filter.date(start_date, end_date)).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).filter(ee.Filter.bounds(geometry))

        # function for Cloud masking
        def maskS2clouds(image):
            qa = image.select('QA60')
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
            return image.updateMask(mask).divide(10000).select("B.*").copyProperties(image, ["system:time_start"])
        

        filtered = filtered.map(maskS2clouds)

        # Write a function that computes NDVI for an image and adds it as a band
        
        def addNDVI(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi')
            return image.addBands(ndvi)

        # Map the function over the collection
        withNdvi = filtered.map(addNDVI)

        # ndvi image
        ndviImage = withNdvi.select('ndvi').median().clip(geometry)
        #Styling 
        vis_paramsNDVI = {
            'min': 0,
            'max': 1,
            'palette': ['ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                '012e01', '011d01', '011301']}

        #add the map to the the folium map
        map_id_dict = ee.Image(ndviImage).getMapId(vis_paramsNDVI)
        print(map_id_dict['tile_fetcher'].url_format)
        return map_id_dict['tile_fetcher'].url_format
       
        # #GEE raster data to TileLayer
        # folium.raster_layers.TileLayer(
        #             tiles = map_id_dict['tile_fetcher'].url_format,
        #             attr = 'Google Earth Engine',
        #             name = 'NDVI',
        #             overlay = True,
        #             control = True
        #             )#.add_to(m)


        # # Moving-Window Smoothing

        # # Specify the time-window
        # days = 30

        # # We use a 'join' to find all images that are within
        # # the time-window
        # # The join will add all matching images into a
        # # new property called 'images'

        # join = ee.Join.saveAll({
        # 'matchesKey': 'images'
        # })

        # # This filter will match all images that are captured
        # # within the specified day of the source image

        # diffFilter = ee.Filter.maxDifference({
        # 'difference': 1000 * 60 * 60 * 24 * days,
        # 'leftField': 'system:time_start', 
        # 'rightField': 'system:time_start'
        # })

        # # Select the 'ndvi' band
        # ndviCol = withNdvi.select('ndvi')

        # joinedCollection = join.apply({
        # 'primary': ndviCol, 
        # 'secondary': ndviCol, 
        # 'condition': diffFilter
        # })

        # # Each image in the joined collection will contain
        # # matching images in the 'images' property
        # # Extract and return the mean of matched images
        