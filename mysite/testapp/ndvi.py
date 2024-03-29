import ee

ee.Initialize()

def ndvi(start_date, end_date, geometry):
        // Moving-Window Temporal Smoothing 
        var s2 = ee.ImageCollection("COPERNICUS/S2");
        // var geometry = geometry
        var start_date = start_date;  // YY-MM-DD
        var end_date = end_date; // YY-MM-DD

        var rgbVis = {min: 0.0, max: 3000, bands: ['B4', 'B3', 'B2']};

        var filtered = s2
        .filter(ee.Filter.date(start_date, end_date))
        .filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30))
        .filter(ee.Filter.bounds(geometry))

        // Write a function for Cloud masking
        function maskS2clouds(image) {
        var qa = image.select('QA60')
        var cloudBitMask = 1 << 10;
        var cirrusBitMask = 1 << 11;
        var mask = qa.bitwiseAnd(cloudBitMask).eq(0).and(
                    qa.bitwiseAnd(cirrusBitMask).eq(0))
        return image.updateMask(mask).divide(10000)
            .select("B.*")
            .copyProperties(image, ["system:time_start"])
        }

        var filtered = filtered.map(maskS2clouds)

        // Write a function that computes NDVI for an image and adds it as a band
        
        function addNDVI(image) {
        var ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi');
        return image.addBands(ndvi);
        }

        // Map the function over the collection
        var withNdvi = filtered.map(addNDVI);

        // Moving-Window Smoothing

        // Specify the time-window
        var days = 30

        // We use a 'join' to find all images that are within
        // the time-window
        // The join will add all matching images into a
        // new property called 'images'
        var join = ee.Join.saveAll({
        matchesKey: 'images'
        });

        // This filter will match all images that are captured
        // within the specified day of the source image
        var diffFilter = ee.Filter.maxDifference({
        difference: 1000 * 60 * 60 * 24 * days,
        leftField: 'system:time_start', 
        rightField: 'system:time_start'
        });

        // Select the 'ndvi' band
        var ndviCol = withNdvi.select('ndvi')

        var joinedCollection = join.apply({
        primary: ndviCol, 
        secondary: ndviCol, 
        condition: diffFilter
        });

        // Each image in the joined collection will contain
        // matching images in the 'images' property
        // Extract and return the mean of matched images
        var smoothedCollection = ee.ImageCollection(joinedCollection.map(function(image) {
        var collection = ee.ImageCollection.fromImages(image.get('images'));
        return ee.Image(image).addBands(collection.mean().rename('moving_average'));
        }))
        
        // Display a time-series chart
        var chart = ui.Chart.image.series({
        imageCollection: smoothedCollection.select(['ndvi', 'moving_average']),
        region: geometry,
        reducer: ee.Reducer.mean(),
        scale: 20
        }).setOptions({
            lineWidth: 1,
            title: 'NDVI Time Series',
            interpolateNulls: true,
            vAxis: {title: 'NDVI'},
            hAxis: {title: '', format: 'YYYY-MMM'},
            series: {
                1: {color: 'gray', lineDashStyle: [1, 1]}, // Original NDVI
                0: {color: 'red', lineWidth: 2 }, // Smoothed NDVI
            },

            })
        print(chart);