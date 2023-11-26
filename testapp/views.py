from django.shortcuts import render
from django.http import HttpResponse
from . import forms
from .models import Farm
from django.http import JsonResponse
import folium
from folium import plugins
import ee
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

            ndvi_ =  ndvi.ndvi(start_date, end_date, farm_id)
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


from . import ndvi

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
            return image.addBands(ndvi)

        # Map the function over the collection
        withNdvi = filtered.map(addNDVI)

        # ndvi image
        ndviImage = withNdvi.select('ndvi').median().clip(geometry)
        #Styling 
        palette = ['ffffff', 'ce7e45', 'df923d', 'f1b555', 'fcd163', '99b718', '74a901',
                '66a000', '529400', '3e8601', '207401', '056201', '004c00', '023b01',
                '012e01', '011d01', '011301']
        vis_paramsNDVI = {
            'min': 0,
            'max': 0.7,
            'palette': ['red', 'yellow', 'green']}

        #add the map to the the folium map
        map_id_dict = ee.Image(ndviImage).getMapId(vis_paramsNDVI)
        #print(map_id_dict['tile_fetcher'].url_format)

        folium.raster_layers.TileLayer(
                tiles=map_id_dict['tile_fetcher'].url_format,
                attr='Google Earth Engine',
                name='NDVI',
                overlay=True,
                control=True
            ).add_to(m)

        m.add_child(folium.LayerControl())
        bounds = geometry_.extent
        
        m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])

        # if dataset is not None:
        #     ndvi = dataset.select('NDVI')

        # if county:
        #     shapefile = County.objects.get(county_code=county)
        #     coordinates = shapefile.geom.coords[0]
        #     ee_polygon = ee.Geometry.Polygon(coordinates)
        #     ndvi = ndvi.clip(ee_polygon)

        #     palette = [
        #         'FFFFFF',  # no data
        #         'CE7E45',  # barren
        #         'FCD163',  # sparsely vegetated
        #         '66A000',  # moderately vegetated
        #         '207401',  # heavily vegetated
        #         '056201'  # very heavily vegetated
        #     ]

        #     vis_params = {
        #         'min': 0,
        #         'max': 9000,
        #         'palette': palette,
        #     }

        #     map_id_dict = ee.Image(ndvi).getMapId(vis_params)

        #     folium.raster_layers.TileLayer(
        #         tiles=map_id_dict['tile_fetcher'].url_format,
        #         attr='Google Earth Engine',
        #         name='NDVI',
        #         overlay=True,
        #         control=True
        #     ).add_to(m)

        #     m.add_child(folium.LayerControl())

        #     bounds = shapefile.geom.extent
        #     m.fit_bounds([[bounds[1], bounds[0]], [bounds[3], bounds[2]]])
            
        # start = datetime(2022, 1, 1)
        # end = datetime(2022, 12, 31)

        # ndvi_ee_polygon = ee.Geometry.Polygon(coords)

        # modis_ndvi = (ee.ImageCollection('MODIS/006/MOD13Q1')
        #                     .filterBounds(ndvi_ee_polygon)
        #                     .filterDate(start, end)
        #                     .select('NDVI'))


        #     def calculate_mean_monthly_ndvi(image):
        #         date = ee.Date(image.get('system:time_start'))
        #         month = date.get('month')
        #         year = date.get('year')

        #         return image.set({
        #             'year': year,
        #             'month': month,
        #             'date_string': date.format('YYYY-MM-dd'),
        #         })


        #     monthly_ndvi = modis_ndvi.map(calculate_mean_monthly_ndvi)


        #     ndvi_list = ee.List([])


        #     def append_ndvi(image, previous):
        #         ndvi = image.reduceRegion(ee.Reducer.mean(), ndvi_ee_polygon, 5000).get('NDVI')
        #         return ee.List(previous).add(ndvi)

        #     ndvi_list = ee.List(monthly_ndvi.iterate(append_ndvi, ndvi_list))

        #     dates = monthly_ndvi.aggregate_array('date_string').getInfo()

        #     ndvi_values = ndvi_list.getInfo()

            

        map = figure.render()

        context = {
            'form': form,
            'map': map,
            'start_date': start_date,
            'end_date': end_date,
            'farm_id': farm_id,
            # 'shapefile': shapefile if county else None,
            # 'dates': dates,
            # 'ndvi_values': ndvi_values,
        }

        return render(request, 'testapp/ndvi.html', context)
