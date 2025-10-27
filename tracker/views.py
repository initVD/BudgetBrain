from django.shortcuts import render, redirect
from django.contrib.auth import login
from django.contrib.auth.forms import UserCreationForm

def register(request):
    """Register a new user."""
    if request.method == 'POST':
        # The user submitted the form
        form = UserCreationForm(request.POST)
        if form.is_valid():
            # Form is valid, save the new user
            user = form.save()
            # Log the user in automatically
            login(request, user)
            # Send them to the dashboard (which we'll build next)
            return redirect('dashboard') 
    else:
        # The user is just visiting the page, show a blank form
        form = UserCreationForm()
        
    # Send the form to the HTML template
    context = {'form': form}
    return render(request, 'tracker/register.html', context)