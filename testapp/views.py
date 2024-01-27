from django.shortcuts import render
from django.http import HttpResponse
from . import forms
from .models import Farm
from django.http import JsonResponse
import folium
from folium import plugins
import ee
from django.contrib.gis.geos import GEOSGeometry
from django.http import JsonResponse
# import pandas as pd
from datetime import datetime
from .forms import DateForm

ee.Initialize()

# Create your views here.
def home(request):
    context = {
        
    }
    return render(request, 'testapp/home.html', context)

def base(request):

    farms = Farm.objects.all()
    context = {
        'farms': farms
    }

    return render(request, 'testapp/base.html', context)

def get_shapefile_midpoint(request, farm_id):
    # Retrieve the shapefile from your model (modify as per your model structure)
    
    farms = Farm.objects.get(farm_id=farm_id)  # Modify this query to fetch the relevant shapefile
    
    if farms:
        # Load the shapefile's geometry
        shapefile_geometry = farms.geom  # Assuming shapefile is a geometry field
        
        # Calculate the midpoint coordinate
        midpoint = shapefile_geometry.centroid
        
        # Get the latitude and longitude of the midpoint
        latitude = midpoint.y
        longitude = midpoint.x
        
        # Return the midpoint coordinate as JSON response
        return JsonResponse({'lat': latitude, 'lon': longitude})
    else:
        return JsonResponse({'error': 'Shapefile data not found'})

def farm(request, farm_id):
    farm = Farm.objects.get(farm_id=farm_id)
    form = forms.DateForm()

    if request.method == 'POST':
        form = forms.DateForm(request.POST)

        if form.is_valid():
            
            start_date = str(form.cleaned_data['StartDate'])
            end_date = str(form.cleaned_data['EndDate'])
            
            print('start date: ',form.cleaned_data['StartDate'])
            print('end date: ',form.cleaned_data['EndDate'])

            form.cleaned_data['EndDate']

            # ndvi_ =  ndvi.ndvi(start_date, end_date, farm_id)
            # return JsonResponse({'StartDate':form.cleaned_data['StartDate'],
            #                      'EndDate': form.cleaned_data['EndDate']})

    context = {
        'farm':farm,
        'form': form,
    }
    return render(request, 'testapp/farm.html', context)


def DateFormview(request):
    form = forms.DateForm()

    if request.method == 'POST':
        form = forms.DateForm(request.POST)

        if form.is_valid():
        
            print('start date: ',form.cleaned_data['StartDate'])
            print('end date: ',form.cleaned_data['EndDate'])

    return render(request, 'testapp/form.html', {'form':form})


# from . import ndvi

# def ndviview(request):
#     ndvi_ = ndvi.ndvi()
#     context = {
#         'ndvi': ndvi
#     }
#     return render(request, 'testapp/ndvi.html', context)


def ndviview(request, farm_id):
    form = DateForm()

    if request.method == 'POST':
        form = forms.DateForm(request.POST)

        if form.is_valid():
            
            start_date = str(form.cleaned_data['StartDate'])
            end_date = str(form.cleaned_data['EndDate'])
        else:
            return

        geometry_ = Farm.objects.get(farm_id=farm_id).geom
        coords = list(geometry_.coords[0])
        geometry = ee.Geometry.Polygon(coords)

        figure = folium.Figure()
        m = folium.Map(
            location=[0.15236, 37.9062],
            zoom_start=6,
        )
        
        m.add_to(figure)

        s2 = ee.ImageCollection("COPERNICUS/S2")

        dataset = s2.filter(ee.Filter.date(start_date, end_date)).filter(ee.Filter.lt('CLOUDY_PIXEL_PERCENTAGE', 30)).filter(ee.Filter.bounds(geometry))

        def maskS2clouds(image):
            qa = image.select('QA60')
            cloudBitMask = 1 << 10
            cirrusBitMask = 1 << 11
            mask = qa.bitwiseAnd(cloudBitMask).eq(0).And(qa.bitwiseAnd(cirrusBitMask).eq(0))
            return image.updateMask(mask).divide(10000).select("B.*").copyProperties(image, ["system:time_start"])
        

        filtered = dataset.map(maskS2clouds)
        
        # Write a function that computes NDVI for an image and adds it as a band
        
        def addNDVI(image):
            ndvi = image.normalizedDifference(['B8', 'B4']).rename('ndvi')
            ndwi = image.normalizedDifference(['B3', 'B11']).rename('ndwi')
            evi = image.expression(
                '2.5 * ((NIR - RED) / (NIR + 6 * RED - 7.5 * BLUE + 1))', {
                    'NIR': image.select('B8'),
                    'RED': image.select('B4'),
                    'BLUE': image.select('B2')
                }).rename("evi")
            
            return image.addBands([ndvi, ndwi, evi])

        # Map the function over the collection
        withNdvi = filtered.map(addNDVI)
        # print(withNdvi.getInfo())
        # ndvi image
        ndviImage = withNdvi.select('ndvi').median().clip(geometry)
        ndwiImage = withNdvi.select('ndwi').median().clip(geometry)
        eviImage = withNdvi.select('evi').median().clip(geometry)
        #Styling 
        palette = ['ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                '012e01', '011d01', '011301']
        
        vis_paramsNDVI = {
            'min': 0,
            'max': 0.7,
            'palette': ['red','orange', 'yellow', 'green']}

        vis_paramsNDWI = {
            'min': -1,
            'max': 0,
            'palette': ['#080b6c','	#0229bf', '#3a80ec', '#89c5fd', '#bcf5f9']}

        vis_paramsEVI = {
            'min': -1,
            'max': 1,
            'palette': ['red','orange', 'yellow', 'green']}
        
        # Add custom base maps to folium
        basemaps = {
            'Google Satellite': folium.TileLayer(
                tiles = 'https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
                attr = 'Google',
                name = 'Google Satellite',
                overlay = True,
                control = True
            ),
            
            'Google Satellite Hybrid': folium.TileLayer(
                tiles = 'https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}',
                attr = 'Google',
                name = 'Google Satellite',
                overlay = True,
                control = True
            ),

            'Esri Satellite': folium.TileLayer(
                tiles = 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
                attr = 'Esri',
                name = 'Esri Satellite',
                overlay = True,
                control = True
            )
        }
        # Add custom basemaps
        
        basemaps['Esri Satellite'].add_to(m)


        #add the map to the the folium map
        map_id_dict = ee.Image(ndviImage).getMapId(vis_paramsNDVI)
        map_id_dict2 = ee.Image(ndwiImage).getMapId(vis_paramsNDWI)
        map_id_dict3 = ee.Image(eviImage).getMapId(vis_paramsEVI)
        #print(map_id_dict['tile_fetcher'].url_format)

        
        folium.raster_layers.TileLayer(
                tiles=map_id_dict2['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name='NDWI',
                overlay=True,
                control=True
            ).add_to(m)
        folium.raster_layers.TileLayer(
                tiles=map_id_dict3['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name='EVI',
                overlay=True,
                control=True
            ).add_to(m)
        folium.raster_layers.TileLayer(
                tiles=map_id_dict['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name='NDVI',
                overlay=True,
                control=True
            ).add_to(m)

        m.add_child(folium.LayerControl())

        #Add the draw 
        plugins.Draw(export=True, filename='data.geojson', position='topleft', draw_options=None, edit_options=None).add_to(m)

        bounds = geometry_.extent
        
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])


        # Add time series chart of NDVI from 2000 to 2020
        shapefile = geometry
        start = datetime(2022, 1, 1)
        end = datetime(2022, 12, 31)


        modis_ndvi = (ee.ImageCollection('MODIS/006/MOD13Q1')
            .filterBounds(shapefile)
            .filterDate(start, end)
            .select('NDVI'))

        sentinel_ndvi = withNdvi.select('ndvi')
        # print(sentinel_ndvi.getInfo())

        def calculate_mean_monthly_ndvi(image):
            date = ee.Date(image.get('system:time_start'))
            month = date.get('month')
            year = date.get('year')

            return image.set({
                'year': year,
                'month': month,
                'date_string': date.format('YYYY-MM-dd'),
            })


        monthly_ndvi = sentinel_ndvi.map(calculate_mean_monthly_ndvi)


        ndvi_list = ee.List([])

        
        def append_ndvi(image, previous):
            ndvi = image.reduceRegion(ee.Reducer.mean(), shapefile, 10).get('ndvi')
            # print(ndvi.getInfo())
            return ee.List(previous).add(ndvi)

        ndvi_list = ee.List(monthly_ndvi.iterate(append_ndvi, ndvi_list))

        dates = monthly_ndvi.aggregate_array('date_string').getInfo()
        
        ndvi_values = ndvi_list.getInfo()
            

        map = figure.render()

        context = {
            'form': form,
            'map': map,
            'start_date': start_date,
            'end_date': end_date,
            'farm_id': farm_id,
            'dates': dates,
            'ndvi_values': ndvi_values
            # 'shapefile': shapefile if county else None,
            # 'dates': dates,
            # 'ndvi_values': ndvi_values,
        }

        return render(request, 'testapp/ndvi.html', context)
    

def weather(request, farm_id):
    farm = Farm.objects.get(farm_id=farm_id)
    form = forms.DateForm()
    context = {
        'farm_id':farm_id,
        'farm': farm,
        'form': form
    }
    return render(request, 'testapp/weather.html', context)

def lulc(request, farm_id):
    form = DateForm()

    if request.method == 'POST':
        form = forms.DateForm(request.POST)

        if form.is_valid():
            
            start_date = str(form.cleaned_data['StartDate'])
            end_date = str(form.cleaned_data['EndDate'])
        else:
            return

    geometry_ = Farm.objects.get(farm_id=farm_id).geom
    coords = list(geometry_.coords[0])
    geometry = ee.Geometry.Polygon(coords)

    farm = Farm.objects.get(farm_id=farm_id)
    form = forms.DateForm()
    figure = folium.Figure()
    m = folium.Map(
            location=[7.423660, 8.748899],
            zoom_start=8
        )

    m.add_to(figure)
    
    # ESRI 10M lANDCOVER DATA SET
    esri_lulc10 = ee.ImageCollection("projects/sat-io/open-datasets/landcover/ESRI_Global-LULC_10m_TS").filterDate('2022-01-01','2022-12-31').mosaic()

    # esri_lulc10 = esri_lulc10.remap([1,2,4,5,7,8,9,10,11],[1,2,3,4,5,6,7,8,9])

    # dictionary which will be used to make visualize image on map
    dict = {
    "names": [
        "Water",
        "Trees",
        "Grass",
        "Flooded Vegetation",
        "Crops",
        "Scrub/Shrub",
        "Built Area",
        "Bare Ground",
        "Snow/Ice",
        "Clouds"
    ],
    "colors": [
        "#1A5BAB",
        "#358221",
        "#A7D282",
        "#87D19E",
        "#FFDB5C",
        "#EECFA8",
        "#ED022A",
        "#EDE9E4",
        "#F2FAFF",
        "#C8C8C8"
    ]
    }

    vis = {'min':1, 'max':10, 'palette':dict['colors']}

    #add the map to the the folium map
    map_id_dict = ee.Image(esri_lulc10).getMapId(vis)
    print(map_id_dict['tile_fetcher'].url_format)
    #GEE raster data to TileLayer
    folium.raster_layers.TileLayer(
                tiles = map_id_dict['tile_fetcher'].url_format,
                attr = 'Google Earth Engine',
                name = 'ESRI 2022 LC',
                overlay = True,
                control = True
                ).add_to(m)

    bounds = geometry_.extent
        
    m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
    #add Layer control
    m.add_child(folium.LayerControl())
    
    #figure 
    map = figure.render()

    context = {
        'map': map,
        'form': form,
        'farm': farm,
        # 'start_date': start_date,
        # 'end_date': end_date,
        'farm_id': farm_id,
    }

    return render(request, 'testapp/lulc.html', context)
