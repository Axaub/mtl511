from django.shortcuts import render

def simple_index_page(request):
    return render(request, 'geotrafic_index.html')
