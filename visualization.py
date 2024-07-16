import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime
from task_scheduler import TaskScheduler
from google_maps_helper import calculate_travel_details

def visualize_schedule(scheduler: TaskScheduler, schedule_date: datetime):
    """
    Visualize the task schedule for all employees on a given date.

    Args:
        scheduler (TaskScheduler): The task scheduler containing assignments.
        schedule_date (datetime): The date for which the schedule should be visualized.
    """
    fig, ax = plt.subplots(figsize=(15, 10))
    
    priority_colors = {
        1: 'tab:blue',
        2: 'tab:orange',
        3: 'tab:green',
        4: 'tab:red',
        5: 'tab:purple',
        6: 'tab:brown',
    }
    
    # Ensure all employees are shown on the y-axis
    employees_for_date = [employee for employee in scheduler.employees if any(av_start.date() == schedule_date.date() for av_start, _ in employee.available_times)]
    employee_ids = [employee.employee_id for employee in employees_for_date]
    employee_index = {employee_id: idx for idx, employee_id in enumerate(employee_ids)}
    
    for assignment in scheduler.assignments:
        task, employee_id = assignment
        if employee_id:
            _, _, departure_time, arrival_time = calculate_travel_details(task.start_location, task.end_location, task.departure_time or task.arrival_time)
            if departure_time.date() == schedule_date.date():
                start = mdates.date2num(departure_time)
                end = mdates.date2num(arrival_time)
                priority_color = priority_colors.get(task.priority, 'gray')
                
                ax.barh(employee_index[employee_id], end - start, left=start, color=priority_color, edgecolor='black', align='center', alpha=0.7)
                ax.text(start, employee_index[employee_id], f"{task.user_id}", va='center', ha='left', color='black')
    
    # Draw horizontal lines for each employee
    for idx in range(len(employee_ids)):
        ax.axhline(y=idx, color='gray', linestyle='--', linewidth=0.5)
    
    # Set y-axis labels to employee IDs
    ax.set_yticks(range(len(employee_ids)))
    ax.set_yticklabels(employee_ids)
    
    # Set x-axis range from 7 AM to 7 PM
    start_of_day = datetime(schedule_date.year, schedule_date.month, schedule_date.day, 7, 0)
    end_of_day = datetime(schedule_date.year, schedule_date.month, schedule_date.day, 19, 0)
    ax.set_xlim(mdates.date2num(start_of_day), mdates.date2num(end_of_day))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    
    plt.xticks(rotation=45)
    ax.set_xlabel('Time')
    ax.set_ylabel('Employees')
    ax.set_title('Task Schedule')
    
    legend_handles = []
    for priority, color in priority_colors.items():
        legend_handles.append(plt.Rectangle((0, 0), 1, 1, color=color, label=f'Priority {priority}'))
    ax.legend(handles=legend_handles, loc='upper left', bbox_to_anchor=(1, 1))

    plt.tight_layout()
    plt.show()
    
    #Print failed assignments
    failed = list(set(scheduler.failed_assignments))
    if failed:
        print("\nFailed Assignments:")
        for task in scheduler.failed_assignments:
            print(f"Task for {task.user_id} from {task.start_location} to {task.end_location} could not be assigned.")
