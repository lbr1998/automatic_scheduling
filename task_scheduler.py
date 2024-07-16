from datetime import datetime, timedelta
from typing import List, Tuple, Optional
from task import Task  # Import Task class
from employee import Employee  # Import Employee class
from google_maps_helper import calculate_travel_details  # Import Google Maps helper function

class TaskScheduler:
    def __init__(self, tasks: List[Task], employees: List[Employee]):
        """
        Initialize the task scheduler with a list of tasks and a list of employees.

        Args:
            tasks (List[Task]): List of tasks.
            employees (List[Employee]): List of employees.
        """
        self.tasks = tasks
        self.employees = employees
        self.assignments = []  # Record of task assignments
        self.failed_assignments = []  # Record of tasks that couldn't be assigned

    def can_assign(self, task: Task, employee: Employee) -> bool:
        """
        Check if a task can be assigned to an employee.

        Args:
            task (Task): Task instance.
            employee (Employee): Employee instance.

        Returns:
            bool: True if the task can be assigned, False otherwise.
        """
        # Check if the employee already has 5 tasks assigned for the day
        if len(employee.assigned_tasks) >= 4:
            return False
        
        # Check if the task priority is higher than the employee's max priority
        if task.priority < employee.max_priority:
            return False

        # Check if the task fits into any of the employee's available time slots
        for available_start, available_end in employee.available_times:
            if available_start <= task.departure_time <= available_end and available_start <= task.arrival_time <= available_end:
                return True
            
        # for available_start, available_end in employee.available_times:
        #     if available_start <= task.departure_time <= available_end and available_start <= task.arrival_time <= available_end:
        #         # Check if there is enough time for travel from the closest assigned task to the current task
        #         if employee.assigned_tasks:
        #             closest_task_1 = min(employee.assigned_tasks, key=lambda t: abs((t.arrival_time - task.departure_time).total_seconds()))
        #             _, travel_time_1, _, _ = calculate_travel_details(closest_task_1.end_location, task.start_location)
        #             closest_task_2 = min(employee.assigned_tasks, key=lambda t: abs((task.arrival_time - t.departure_time).total_seconds()))
        #             _, travel_time_2, _, _ = calculate_travel_details(task.end_location, closest_task_2.start_location)
        #             if (closest_task_1.arrival_time + timedelta(minutes=travel_time_1) > task.departure_time or
        #                 task.arrival_time + timedelta(minutes=travel_time_2) > closest_task_2.departure_time):
        #                 return False
        #         return True
        
        return False

    def assign_task(self, task: Task, employee: Employee, tasks_for_date: List[Task]):
        """
        Assign a task to an employee and update their available times and assignments.

        Args:
            task (Task): Task instance.
            employee (Employee): Employee instance.
            tasks_for_date (List[Task]): List of tasks for the specific date.
        """
        total_task_duration = task.duration

        # If the employee already has assigned tasks, calculate travel time from the last task
        if employee.assigned_tasks:
            previous_task = employee.assigned_tasks[-1]
            _, travel_time, _, _ = calculate_travel_details(previous_task.end_location, task.start_location)
            total_task_duration += travel_time
        
        # Deduct the total task duration from the employee's available hours
        employee.max_hours -= total_task_duration / 60
        self.assignments.append((task, employee.employee_id))
        employee.assigned_tasks.append(task)

        # Update the employee's available times
        new_available_times = []
        for available_start, available_end in employee.available_times:
            if available_start <= task.departure_time and task.arrival_time <= available_end:
                if available_start < task.departure_time:
                    new_available_times.append((available_start, task.departure_time))
                if task.arrival_time < available_end:
                    new_available_times.append((task.arrival_time, available_end))
            else:
                new_available_times.append((available_start, available_end))

        employee.available_times = new_available_times
        remaining_tasks = [t for t in tasks_for_date if t not in self.assignments and t not in self.failed_assignments]

        # Attempt to assign the closest subsequent task to the employee
        self.assign_closed_task(task, employee, remaining_tasks)

    def assign_tasks_for_date(self, date: datetime):
        """
        Assign tasks for a specific date.

        Args:
            date (datetime): The date for which tasks are to be assigned.
        """
        # Filter tasks for the specific date
        tasks_for_date = [task for task in self.tasks if (task.departure_time and task.departure_time.date() == date.date()) or 
                          (task.arrival_time and task.arrival_time.date() == date.date())]
        
        employees_for_date = [employee for employee in self.employees if (av_start.date() == date.date() for av_start, _ in employee.available_times)]

        remaining_tasks = self.assign_remaining_tasks(tasks_for_date, employees_for_date, self.can_assign, self.assign_task)

        # Attempt to reassign remaining tasks until no more progress can be made
        while remaining_tasks:
            new_remaining_tasks = self.assign_remaining_tasks(remaining_tasks, employees_for_date, self.can_assign, self.assign_task)
            if len(new_remaining_tasks) == len(remaining_tasks):
                break
            remaining_tasks = new_remaining_tasks

    def assign_closed_task(self, task: Task, employee: Employee, tasks_for_date: List[Task]):
        """
        Assign the closest subsequent task to the employee if possible.

        Args:
            task (Task): Task instance.
            employee (Employee): Employee instance.
            tasks_for_date (List[Task]): List of tasks for the specific date.
        """
        closed_task = None
        best_travel_time = float('inf')
        
        tasks_p = [t for t in tasks_for_date if t.priority == task.priority]
        # Find the closest task that fits into the employee's schedule
        for candidate_task in tasks_p:
            if candidate_task not in employee.assigned_tasks and candidate_task not in self.failed_assignments:
                candidate_start_time = candidate_task.departure_time
                
                if candidate_start_time:
                    _, travel_time, _, _ = calculate_travel_details(task.end_location, candidate_task.start_location)
                    interval_time = (candidate_start_time - task.arrival_time).total_seconds() / 60

                    if 0 < interval_time - travel_time <= 60 and travel_time < best_travel_time:
                        best_travel_time = travel_time
                        closed_task = candidate_task
        
        # If a suitable task is found, assign it to the employee
        if closed_task:
            if self.can_assign(closed_task, employee):
                self.assign_task(closed_task, employee, tasks_for_date)

    def assign_remaining_tasks(self, tasks_for_date: List[Task], employees: List[Employee], can_assign, assign_task):
        """
        Assign remaining tasks to employees, attempting to balance the workload.

        Args:
            tasks_for_date (List[Task]): List of tasks for the specific date.
            employees (List[Employee]): List of employees.
            can_assign (function): Function to check if a task can be assigned.
            assign_task (function): Function to assign a task.

        Returns:
            List[Task]: List of tasks that could not be assigned.
        """
        # Sort tasks by priority
        tasks_for_date.sort(key=lambda x: x.priority)

        # Sort employees by the number of tasks they have assigned
        employees.sort(key=lambda e: len(e.assigned_tasks))

        # Group tasks by user
        tasks_by_user = {}
        for task in tasks_for_date:
            if task.user_id not in tasks_by_user:
                tasks_by_user[task.user_id] = []
            tasks_by_user[task.user_id].append(task)

        new_tasks_for_date = []
        rollback_state = {}  # Dictionary to store the state of each employee before attempting to assign tasks

        for user_id, user_tasks in tasks_by_user.items():
            user_tasks.sort(key=lambda x: x.priority)
            assigned = False

            # Save the current state of each employee
            rollback_state.clear()
            for employee in employees:
                rollback_state[employee] = (employee.available_times[:], employee.max_hours, employee.assigned_tasks[:])

            # Try to assign tasks to employees
            for task in user_tasks:
                assigned_to_employee = False
                for employee in employees:
                    if can_assign(task, employee):
                        assign_task(task, employee, tasks_for_date)
                        assigned_to_employee = True
                        assigned = True
                        break
                if not assigned_to_employee:
                    self.failed_assignments.extend(user_tasks)

            # Rollback if not all tasks for this user_id were assigned
            if not assigned:
                print(f"Tasks for user {user_id} could not be assigned.")
                self.failed_assignments.extend(user_tasks)

                # Rollback each employee's state
                for employee, state in rollback_state.items():
                    employee.available_times = state[0]
                    employee.max_hours = state[1]
                    employee.assigned_tasks = state[2]

        return new_tasks_for_date
