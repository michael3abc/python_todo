# scheduler.py
import copy
import numpy as np
import re


class Scheduler:
    def __init__(self, start_time=9, end_time=17, interval_minutes=30, fatigue_calculation=None):
        """
        Initialize the scheduler.

        :param start_time: Work start time (24-hour format), default is 9.
        :param end_time: Work end time (24-hour format), default is 17.
        :param interval_minutes: Minutes per time slot, default is 30.
        :param fatigue_calculation: User-defined fatigue calculation function.
        """
        if not (0 <= start_time < 24) or not (0 < end_time <= 24):
            raise ValueError("工作時間必須在0到24之間。")
        if start_time >= end_time:
            raise ValueError("開始時間必須早於結束時間。")
        if 60 % interval_minutes != 0:
            raise ValueError("時間間隔必須能被60整除。")

        self.start_time = start_time
        self.end_time = end_time
        self.interval_minutes = interval_minutes
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.num_intervals_per_day = int((self.end_time - self.start_time) * 60 / self.interval_minutes)

        # Initialize schedule structure: 7 days, each with a fixed number of time slots, default to None
        self.schedule = [[None for _ in range(self.num_intervals_per_day)] for _ in range(7)]

        self.tasks = []
        self.task_dict = {}
        self.fatigue_calculation = fatigue_calculation or self.default_fatigue_calculation

        # Variables for tracking the best schedule
        self.min_fatigue = float('inf')
        self.best_schedule = None

        # Variables for incremental fatigue calculation
        self.day_unique_tasks = [set() for _ in range(7)]
        self.day_difficulty_sum = [0 for _ in range(7)]
        self.day_fatigue_sum = [0.0 for _ in range(7)]
        self.day_fatigue = [0.0 for _ in range(7)]
        self.total_fatigue = 0.0

    def default_fatigue_calculation(self, task):
        """
        Default fatigue calculation: difficulty * time
        """
        return task.get("difficulty", 1) * task.get("time", 1)

    def calculate_fatigue(self):
        total_fatigue = 0
        task_mapping = {task['name']: task for task in self.tasks}

        for day_index, day_slots in enumerate(self.schedule):
            daily_fatigue = 0
            daily_difficulty_sum = 0
            unique_tasks = set()

            for slot in day_slots:
                if slot is not None:
                    unique_tasks.add(slot["name"])

            for task_name in unique_tasks:
                task = task_mapping[task_name]
                task_fatigue = self.fatigue_calculation(task)
                daily_fatigue += task_fatigue
                daily_difficulty_sum += task["difficulty"]

            daily_fatigue *= (1 + daily_difficulty_sum)
            total_fatigue += daily_fatigue

        return total_fatigue

    def assign_task(self, task):
        """
        Try to assign a task to the schedule.
        Assign higher priority tasks first.
        """
        duration = task["time"]  # Duration in hours
        num_slots = int(duration * (60 / self.interval_minutes))  # Convert to number of slots

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]  # e.g., ('Monday', 9, 0)
            day_index = self.days.index(day)
            start_slot = int(
                (start_hour - self.start_time) * (60 / self.interval_minutes) + start_minute / self.interval_minutes)
            if start_slot < 0 or start_slot + num_slots > self.num_intervals_per_day:
                return False  # Fixed time out of range

            # Check if the specified time slots are free
            for slot in range(start_slot, start_slot + num_slots):
                if self.schedule[day_index][slot] is not None:
                    return False  # Time slot already occupied

            # Assign task to the specified time slots
            for slot in range(start_slot, start_slot + num_slots):
                self.schedule[day_index][slot] = task
            return True
        else:
            # Try to find a suitable time slot throughout the week
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    # Check if all consecutive slots are free
                    if all(self.schedule[day_index][slot] is None for slot in range(start_slot, start_slot + num_slots)):
                        # Assign task
                        for slot in range(start_slot, start_slot + num_slots):
                            self.schedule[day_index][slot] = task
                        return True
            return False  # No available time slots

    def minimize_total_fatigue(self):
        """
        Find the schedule that minimizes total fatigue using backtracking.
        """
        # Precompute fatigue for each task
        for task in self.tasks:
            task["fatigue"] = self.fatigue_calculation(task)

        # Sort tasks by priority descending and then by the number of possible assignments ascending
        self.tasks.sort(key=lambda t: (-t.get("priority", 0), self.count_possible_assignments(t)))

        self.min_fatigue = float('inf')
        self.best_schedule = None
        self.total_fatigue = 0.0

        self.backtrack(0)
        return self.best_schedule, self.min_fatigue

    def backtrack(self, index):
        """
        Backtracking function to assign tasks and minimize fatigue.
        """
        if index >= len(self.tasks):
            if self.total_fatigue < self.min_fatigue:
                self.min_fatigue = self.total_fatigue
                self.best_schedule = [list(day) for day in self.schedule]
            return

        task = self.tasks[index]
        possible_assignments = self.get_possible_assignments(task)

        for day_index, start_slot, num_slots in possible_assignments:
            # Assign the task to the schedule
            for slot in range(start_slot, start_slot + num_slots):
                self.schedule[day_index][slot] = task

            # Determine if the task is new for the day
            is_new_task_for_day = task["name"] not in self.day_unique_tasks[day_index]

            if is_new_task_for_day:
                # Update per-day tracking
                self.day_unique_tasks[day_index].add(task["name"])
                self.day_difficulty_sum[day_index] += task["difficulty"]
                self.day_fatigue_sum[day_index] += task["fatigue"]
                old_day_fatigue = self.day_fatigue[day_index]
                self.day_fatigue[day_index] = self.day_fatigue_sum[day_index] * (1 + self.day_difficulty_sum[day_index])
                self.total_fatigue += self.day_fatigue[day_index] - old_day_fatigue

            # Prune if current total fatigue exceeds the minimum found
            if self.total_fatigue < self.min_fatigue:
                self.backtrack(index + 1)

            # Undo the assignment
            for slot in range(start_slot, start_slot + num_slots):
                self.schedule[day_index][slot] = None

            if is_new_task_for_day:
                # Revert per-day tracking
                self.day_unique_tasks[day_index].remove(task["name"])
                self.day_difficulty_sum[day_index] -= task["difficulty"]
                self.day_fatigue_sum[day_index] -= task["fatigue"]
                old_day_fatigue = self.day_fatigue[day_index]
                self.day_fatigue[day_index] = self.day_fatigue_sum[day_index] * (1 + self.day_difficulty_sum[day_index])
                self.total_fatigue += self.day_fatigue[day_index] - old_day_fatigue

    def count_possible_assignments(self, task):
        """
        Count the number of possible assignments for a task.
        This helps in sorting tasks with fewer options first.
        """
        return len(self.get_possible_assignments(task))

    def get_possible_assignments(self, task):
        """
        Get all possible assignments for a task.
        """
        assignments = []
        duration = task["time"]  # Duration in hours
        num_slots = int(duration * (60 / self.interval_minutes))  # Convert to number of slots

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]
            day_index = self.days.index(day)
            start_slot = int(
                (start_hour - self.start_time) * (60 / self.interval_minutes) + start_minute / self.interval_minutes)
            if 0 <= start_slot <= self.num_intervals_per_day - num_slots:
                if all(self.schedule[day_index][slot] is None for slot in range(start_slot, start_slot + num_slots)):
                    assignments.append((day_index, start_slot, num_slots))
        else:
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    if all(self.schedule[day_index][slot] is None for slot in range(start_slot, start_slot + num_slots)):
                        assignments.append((day_index, start_slot, num_slots))
        return assignments

    def generate_schedule_list(self, schedule=None):
        """
        Convert the schedule to a list format for GUI or printing.
        Default schedule is self.best_schedule.
        """
        if schedule is None:
            schedule = self.best_schedule
        if schedule is None:
            return []

        # Generate a 2D list, each day as a row
        # Print task names or '-' for empty slots
        result = []
        for day_index, slots in enumerate(schedule):
            day_slots = []
            for slot in slots:
                if slot is None:
                    day_slots.append('-')
                else:
                    day_slots.append(slot["name"])
            result.append(day_slots)
        return result

    def add_tasks(self, tasks):
        """
        Add tasks to the scheduler.
        """
        self.tasks.extend(tasks)
        for task in tasks:
            self.task_dict[task["name"]] = task

    def generate_fatigue_function(expression, allowed_vars, default_values=None):
        """
        Generate a fatigue calculation function based on a user-provided mathematical expression.

        :param expression: Mathematical expression as a string, e.g., 'difficulty * time * priority'
        :param allowed_vars: List of allowed variables, e.g., ['difficulty', 'time', 'priority', 'task_num']
        :param default_values: Dictionary of default values if a variable is missing in a task.
        :return: Generated fatigue calculation function.
        """

        # If no default values provided, set default mapping
        if default_values is None:
            default_values = {
                'difficulty': 1,
                'time': 1,
                'priority': 0,
                'task_num': 1
            }

        # Extract variables used in the expression
        tokens = re.findall(r'\b[A-Za-z_]\w*\b', expression)
        for token in tokens:
            if token not in allowed_vars:
                raise ValueError(f"數學式子中包含無效或未允許的變數: {token}")

        # Return a function that calculates fatigue based on the expression
        def fatigue_function(task):
            # Build the evaluation context
            eval_dict = {}
            for var in allowed_vars:
                eval_dict[var] = task.get(var, default_values.get(var, 1))
            return eval(expression, {}, eval_dict)

        return fatigue_function


if __name__ == "__main__":
    # User-specified allowed variables
    user_allowed_vars = ['difficulty', 'time', 'priority', 'task_num']
    # User-provided fatigue calculation expression
    # user_expression = "difficulty * time"  # Modify as needed
    user_expression = "difficulty * time / priority"

    # Generate the fatigue calculation function
    fatigue_function = Scheduler.generate_fatigue_function(user_expression, user_allowed_vars)

    # Define tasks
    tasks = [
        {
            "name": "Task 1",
            "time": 2,  # Duration 2 hours
            "difficulty": 4,
            "priority": 1,
            "fixed_time": None  # No fixed time, assign randomly
        },
        {
            "name": "Task 2",
            "time": 1,  # Duration 1 hour
            "difficulty": 6,
            "priority": 2,
            "fixed_time": None  # No fixed time, assign randomly
        },
        {
            "name": "Task 3",
            "time": 4,  # Duration 4 hours
            "difficulty": 4,
            "priority": 3,
            "fixed_time": None  # No fixed time, assign randomly
        },
        {
            "name": "Task 4",
            "time": 2,  # Duration 2 hours
            "difficulty": 4,
            "priority": 4,
            "fixed_time": ("Sunday", 9, 0)  # Fixed time
        },
        {
            "name": "Task 5",
            "time": 4,  # Duration 4 hours
            "difficulty": 1,
            "priority": 6,
            "fixed_time": None  # No fixed time, assign randomly
        },
    ]

    # Initialize the scheduler with the custom fatigue function
    scheduler = Scheduler(fatigue_calculation=fatigue_function)
    scheduler.add_tasks(tasks)

    # Minimize total fatigue
    best_schedule, min_fatigue = scheduler.minimize_total_fatigue()

    # Print the minimum fatigue value
    print("最小疲勞值:", min_fatigue)

    # Generate and print the final schedule list
    final_list = scheduler.generate_schedule_list(best_schedule)
    for day_idx, day_name in enumerate(scheduler.days):
        print(day_name, final_list[day_idx])
