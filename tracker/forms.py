# tracker/forms.py
from django import forms

class CSVUploadForm(forms.Form):
    # This field will be rendered as an <input type="file">
    csv_file = forms.FileField()