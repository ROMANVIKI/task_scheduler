from django.shortcuts import render
# tracker/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Sum, F
from datetime import timedelta
import pandas as pd
import plotly.express as px
import json

from .models import Task, Category, TimeEntry
from .forms import TaskForm, CategoryForm, TimeEntryForm


from django.db.models import Q


import json
import numpy as np

import pandas as pd
import plotly.express as px
from django.shortcuts import render
from django.http import JsonResponse
from django.db.models import Sum, F
from datetime import timedelta
from .models import Task, Category, TimeEntry
from django.db.models import Q
from django.contrib.auth.decorators import login_required

@login_required
def dashboard(request):
    # Get user's tasks and time entries
    tasks = Task.objects.filter(user=request.user)
    time_entries = TimeEntry.objects.filter(task__user=request.user)
    
    # Calculate total time spent
    total_time = time_entries.aggregate(
        total=Sum('duration', filter=~Q(duration=None))
    )['total'] or timedelta()
    
    # Get time spent per category
    category_times = {}
    for category in Category.objects.filter(user=request.user):
        category_time = TimeEntry.objects.filter(
            task__category=category,
            task__user=request.user
        ).aggregate(total=Sum('duration'))['total'] or timedelta()
        category_times[category.name] = category_time.total_seconds() / 3600  # Convert to hours
    
    # Create visualization using plotly
    if category_times:
        df = pd.DataFrame(list(category_times.items()), columns=['Category', 'Hours'])
        fig = px.pie(df, values='Hours', names='Category', title='Time Distribution by Category')

        # Convert plotly figure to a dict and handle potential ndarray serialization issue
        chart_dict = fig.to_dict()

        # Ensure that all NumPy ndarrays are converted to lists
        def convert_ndarray(obj):
            if isinstance(obj, list):
                return [convert_ndarray(i) for i in obj]  # Recursively handle nested lists
            elif isinstance(obj, dict):
                return {key: convert_ndarray(val) for key, val in obj.items()}
            elif isinstance(obj, np.ndarray):
                return obj.tolist()  # Convert ndarray to list
            return obj

        # Apply conversion function
        chart_json = json.dumps(convert_ndarray(chart_dict))
    else:
        chart_json = None
    
    context = {
        'tasks': tasks,
        'total_time': total_time,
        'chart_json': chart_json,
    }
    return render(request, 'tracker/dashboard.html', context)




@login_required
def task_list(request):
    tasks = Task.objects.filter(user=request.user)
    if request.method == 'POST':
        form = TaskForm(request.POST)
        if form.is_valid():
            task = form.save(commit=False)
            task.user = request.user
            task.save()
            messages.success(request, 'Task created successfully!')
            return redirect('task_list')
    else:
        form = TaskForm()
    
    return render(request, 'tracker/task_list.html', {
        'tasks': tasks,
        'form': form
    })

@login_required
def start_timer(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    time_entry = TimeEntry.objects.create(task=task, start_time=timezone.now())
    return JsonResponse({'status': 'success', 'time_entry_id': time_entry.id})

@login_required
def stop_timer(request, time_entry_id):
    time_entry = get_object_or_404(TimeEntry, id=time_entry_id, task__user=request.user)
    time_entry.stop_timer()
    return JsonResponse({
        'status': 'success',
        'duration': str(time_entry.duration)
    })

@login_required
def export_data(request):
    time_entries = TimeEntry.objects.filter(task__user=request.user)
    data = []
    
    for entry in time_entries:
        data.append({
            'task': entry.task.title,
            'category': entry.task.category.name if entry.task.category else 'Uncategorized',
            'start_time': entry.start_time,
            'end_time': entry.end_time,
            'duration_minutes': entry.get_duration_in_minutes()
        })
    
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="time_tracking_data.csv"'
    df.to_csv(response, index=False)
    return response
# Create your views here.
#
#
#
# Add these imports at the top of views.py
from datetime import datetime, timedelta
from django.db.models import Count
from django.db.models.functions import TruncDate

@login_required
def task_detail(request, task_id):
    task = get_object_or_404(Task, id=task_id, user=request.user)
    return render(request, 'tracker/task_detail.html', {'task': task})




from django.shortcuts import render
from django.contrib.auth.forms import UserCreationForm
from django.http import HttpResponseRedirect

def register(request):
    if request.method == "POST":
        form = UserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect('/accounts/login/')
    else:
        form = UserCreationForm()
    return render(request, 'registration/register.html', {'form': form})







import plotly.express as px
import plotly
import json
import pandas as pd
from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum, F
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from .models import TimeEntry, Task

@login_required
def reports(request):
    # Get date range from request parameters or use default (last 30 days)
    end_date = timezone.now()
    start_date = end_date - timedelta(days=30)
    
    if request.GET.get('start_date'):
        start_date = timezone.make_aware(datetime.strptime(request.GET['start_date'], '%Y-%m-%d'))
    if request.GET.get('end_date'):
        end_date = timezone.make_aware(datetime.strptime(request.GET['end_date'], '%Y-%m-%d'))
    
    # Filter time entries by date range
    time_entries = TimeEntry.objects.filter(
        task__user=request.user,
        start_time__gte=start_date,
        start_time__lte=end_date
    ).select_related('task', 'task__category')
    
    # Calculate total hours
    total_duration = time_entries.aggregate(total=Sum('duration'))['total'] or timedelta()
    total_hours = total_duration.total_seconds() / 3600
    
    # Get most active category
    category_times = {}
    for entry in time_entries:
        category_name = entry.task.category.name if entry.task.category else 'Uncategorized'
        if entry.duration:
            category_times[category_name] = category_times.get(category_name, timedelta()) + entry.duration
    
    most_active_category = max(category_times.items(), key=lambda x: x[1])[0] if category_times else None
    
    # Get active tasks count
    active_tasks_count = Task.objects.filter(
        user=request.user,
        time_entries__start_time__gte=start_date,
        time_entries__start_time__lte=end_date
    ).distinct().count()
    
    # Create category distribution chart
    if category_times:
        category_hours = {k: v.total_seconds() / 3600 for k, v in category_times.items()}
        df_category = pd.DataFrame(list(category_hours.items()), columns=['Category', 'Hours'])
        fig_category = px.pie(df_category, values='Hours', names='Category', 
                            title='Time Distribution by Category')
        category_chart_json = json.dumps(fig_category, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        category_chart_json = None
    
    # Create daily activity chart
    daily_data = (
        time_entries
        .annotate(date=TruncDate('start_time'))
        .values('date')
        .annotate(hours=Sum(F('duration')))
        .order_by('date')
    )
    
    if daily_data:
        df_daily = pd.DataFrame(daily_data)
        df_daily['hours'] = df_daily['hours'].apply(lambda x: x.total_seconds() / 3600 if x else 0)
        fig_daily = px.line(df_daily, x='date', y='hours', 
                          title='Daily Activity',
                          labels={'date': 'Date', 'hours': 'Hours'})
        daily_chart_json = json.dumps(fig_daily, cls=plotly.utils.PlotlyJSONEncoder)
    else:
        daily_chart_json = None
    
    context = {
        'start_date': start_date,
        'end_date': end_date,
        'total_hours': total_hours,
        'most_active_category': most_active_category,
        'active_tasks_count': active_tasks_count,
        'time_entries': time_entries,
        'category_chart_json': category_chart_json,
        'daily_chart_json': daily_chart_json,
    }
    
    return render(request, 'tracker/reports.html', context)

# views.py
from django.shortcuts import redirect
from django.contrib.auth import logout

def logout_view(request):
    logout(request)
    print('logged out')
    return redirect('logout_success')  # Redirect to the login page or homepage



# views.py

def logout_success(request):
    return render(request, 'registration/logout_success.html')

def logout_failed(request):
    return render(request, 'registration/logout_failed.html')

