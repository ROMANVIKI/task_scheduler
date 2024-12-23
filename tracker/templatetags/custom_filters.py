from django import template
from datetime import timedelta

register = template.Library()

@register.filter
def time_sum(time_entries):
    total_time = timedelta()
    for entry in time_entries:
        if entry.end_time:
            total_time += entry.end_time - entry.start_time
    return str(total_time)

