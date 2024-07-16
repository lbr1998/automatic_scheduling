from datetime import datetime
from typing import List, Tuple

class Employee:
    """
    Represents an employee with an ID, maximum working hours, maximum task priority they can handle, 
    available times, and assigned tasks.

    Attributes:
        employee_id (str): The ID of the employee.
        max_hours (int): The maximum number of working hours the employee can handle.
        max_priority (int): The maximum priority level of tasks the employee can handle.
        available_times (List[Tuple[datetime, datetime]]): The available time slots for the employee.
        assigned_tasks (List): The list of tasks assigned to the employee.
    """
    def __init__(self, employee_id: str, max_hours: float, max_priority: int, available_times: List[Tuple[datetime, datetime]]):
        self.employee_id = employee_id
        self.max_hours = max_hours
        self.max_priority = max_priority
        self.available_times = available_times
        self.assigned_tasks = []
