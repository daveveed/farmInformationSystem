from django import forms

# creating custom widget 

class DateInput(forms.DateInput):
    input_type = 'date'


class DateForm(forms.Form):
    
    StartDate = forms.DateField(widget=DateInput)
    EndDate = forms.DateField(widget=DateInput)