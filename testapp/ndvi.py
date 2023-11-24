import ee
from . models import Farm
from . import Form
ee.Initialize()

def ndvi(start_date, end_date, farm_id):
        # Moving-Window Temporal Smoothing 
        s2 = ee.ImageCollection("COPERNICUS/S2")
        geometry = Farm.objects.get(farm_id=farm_id)
        
        form = forms.DateForm()

        if request.method == 'POST':
            form = forms.DateForm(request.POST)

            if form.is_valid():
            
                start_date = form.cleaned_data['StartDate']
                end_date = form.cleaned_data['EndDate']
          

        rgbVis = {'min': 0.0, 'max': 3000, 'bands': ['B4', 'B3', 'B2']}

        filtered = s2
        .filter(ee.Filter.date(start_date, end_date))
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
        .filter(ee.Filter.bounds(geometry))

        # function for Cloud masking
        def maskS2clouds(image):
            qa = image.select('QA60')
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(
                        qa.bitwiseAnd(cirrusBitMask).eq(0))
            return image.updateMask(mask).divide(10000)
                .select("B.*")
                .copyProperties(image, ["system:time_start"])
        

        filtered = filtered.map(maskS2clouds)

        # Write a function that computes NDVI for an image and adds it as a band
        
        def addNDVI(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi')
            return image.addBands(ndvi)

        # Map the function over the collection
        withNdvi = filtered.map(addNDVI)

        # ndvi image
        ndviImage = withNdvi.select('ndvi').clip(geometry)
        #Styling 
        vis_paramsNDVI = {
            'min': 0,
            'max': 1,
            'palette': ['ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                '012e01', '011d01', '011301']}

        #add the map to the the folium map
        map_id_dict = ee.Image(ndviImage).getMapId(vis_paramsNDVI)
       
        #GEE raster data to TileLayer
        folium.raster_layers.TileLayer(
                    tiles = map_id_dict['tile_fetcher'].url_format,
                    attr = 'Google Earth Engine',
                    name = 'NDVI',
                    overlay = True,
                    control = True
                    )#.add_to(m)


        # Moving-Window Smoothing

        # Specify the time-window
        days = 30

        # We use a 'join' to find all images that are within
        # the time-window
        # The join will add all matching images into a
        # new property called 'images'

        join = ee.Join.saveAll({
        'matchesKey': 'images'
        })

        # This filter will match all images that are captured
        # within the specified day of the source image

        diffFilter = ee.Filter.maxDifference({
        'difference': 1000 * 60 * 60 * 24 * days,
        'leftField': 'system:time_start', 
        'rightField': 'system:time_start'
        })

        # Select the 'ndvi' band
        ndviCol = withNdvi.select('ndvi')

        joinedCollection = join.apply({
        'primary': ndviCol, 
        'secondary': ndviCol, 
        'condition': diffFilter
        })

        # Each image in the joined collection will contain
        # matching images in the 'images' property
        # Extract and return the mean of matched images
        smoothedCollection = ee.ImageCollection(joinedCollection.map(function(image) {
        collection = ee.ImageCollection.fromImages(image.get('images'))
        return ee.Image(image).addBands(collection.mean().rename('moving_average'))
        }))
        
        # Display a time-series chart
        chart = ui.Chart.image.series({
        'imageCollection': smoothedCollection.select(['ndvi', 'moving_average']),
        'region': geometry,
        'reducer': ee.Reducer.mean(),
        'scale': 20
        }).setOptions({
            'lineWidth': 1,
            'title': 'NDVI Time Series',
            'interpolateNulls': true,
            'vAxis': {'title': 'NDVI'},
            'hAxis': {'title': '', format: 'YYYY-MMM'},
            'series': {
                1: {'color': 'gray', lineDashStyle: [1, 1]}, // Original NDVI
                0: {'color': 'red', lineWidth: 2 }, // Smoothed NDVI
            },

            })
        print(chart)