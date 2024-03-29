from django.shortcuts import render
from django.http import HttpResponse
from . import forms
from .models import Farm

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
        
            print('start date: ',form.cleaned_data['StartDate'])
            print('end date: ',form.cleaned_data['EndDate'])

    context = {
        'farm':farm,
        'form': form
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
