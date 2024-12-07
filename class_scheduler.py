import pandas as pd
from collections import defaultdict
import copy

class Scheduler():
    def __init__(self,start_time = 9, end_time=17):
        self.start_time = start_time
        self.end_time = end_time
        self.days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        self.available_hours = {
            day: list(range(self.start_time, self.end_time)) for day in self.days
        }
        self.tasks = []
        self.all_tasks = []
        self.best_schedule = None
        self.min_fatigue = float('inf')

    def calculate_fatigue(self, schedule):
        total_fatigue = 0
        task_mapping = {task['name']: task for task in self.all_tasks}
        for day, tasks in schedule.items():
            daily_fatigue = 0
            daily_difficulty_sum = 0
            for start_time, task_name in tasks:
                task = task_mapping[task_name]
                difficulty = task["difficulty"]
                time = task["time"]
                task_fatigue = difficulty * time
                daily_fatigue += task_fatigue
                daily_difficulty_sum += difficulty
            daily_fatigue *= (1 + daily_difficulty_sum)
            total_fatigue += daily_fatigue
        return total_fatigue

    def is_time_slot_available(self, day, start_time, duration, available_hours):
        return all(hour in available_hours[day] for hour in range(start_time, start_time + duration))

    def assign_task(self, task, schedule, available_hours):
        assignments = []
        if task["fixed_time"]:
            day, start_time = task["fixed_time"]
            duration = int(task["time"])
            if self.is_time_slot_available(day, start_time, duration, available_hours):
                assignments.append((day, start_time))
        else:
            duration = int(task["time"])
            for day in self.days:
                for start_time in range(self.start_time, self.end_time - duration + 1):
                    if self.is_time_slot_available(day, start_time, duration, available_hours):
                        assignments.append((day, start_time))
        return assignments

    def backtrack(self, tasks, schedule, available_hours):
        if not tasks:
            fatigue = self.calculate_fatigue(schedule)
            if fatigue < self.min_fatigue:
                self.min_fatigue = fatigue
                self.best_schedule = copy.deepcopy(schedule)
            return

        task = tasks[0]
        possible_assignments = self.assign_task(task, schedule, available_hours)
        for day, start_time in possible_assignments:
            duration = int(task["time"])
            # Assign task
            schedule.setdefault(day, []).append((start_time, task["name"]))
            # Update available hours
            for hour in range(start_time, start_time + duration):
                available_hours[day].remove(hour)
            # Recurse
            self.backtrack(tasks[1:], schedule, available_hours)
            # Backtrack
            schedule[day].remove((start_time, task["name"]))
            for hour in range(start_time, start_time + duration):
                available_hours[day].append(hour)
                available_hours[day].sort()  # Keep hours sorted

    def minimize_total_fatigue(self):
        self.best_schedule = None
        self.min_fatigue = float('inf')
        available_hours = {day: list(range(self.start_time, self.end_time)) for day in self.days}
        self.backtrack(self.tasks, {}, available_hours)
        # Generate schedule dataframe
        schedule_df = self.generate_schedule_dataframe(schedule=self.best_schedule)
        return schedule_df, self.min_fatigue

    def generate_schedule_dataframe(self, schedule=None):
        if schedule is None:
            schedule = self.best_schedule
        time_slots = [f"{hour}:00" for hour in range(self.start_time, self.end_time)]
        df = pd.DataFrame('', index=time_slots, columns=self.days)
        for day in self.days:
            if day in schedule:
                for start_time, task_name in schedule[day]:
                    task = next(t for t in self.all_tasks if t["name"] == task_name)
                    duration = int(task["time"])
                    for hour in range(start_time, start_time + duration):
                        if f"{hour}:00" in df.index:
                            df.at[f"{hour}:00", day] = task_name
        return df

# Example usage
scheduler = Scheduler()
scheduler.tasks = [
    # {"name": "Task A", "difficulty": 4, "time": 4, "fixed_time": ('Friday',9), "dependencies": []},
    {"name": "Task A", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    {"name": "Task B", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    # # {"name": "Task C", "difficulty": 2, "time": 2, "fixed_time": None, "dependencies": []},
    # {"name": "Task C", "difficulty": 2, "time": 2, "fixed_time": ('Friday',13), "dependencies": []},
    # {"name": "Task D", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    # {"name": "Task E", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    # {"name": "Task F", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    # {"name": "Task G", "difficulty": 4, "time": 4, "fixed_time": ('Sunday', 9), "dependencies": []},
    # {"name": "Task H", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},


]
scheduler.all_tasks = copy.deepcopy(scheduler.tasks)

schedule_df, min_fatigue = scheduler.minimize_total_fatigue()
print("Best Schedule:\n", schedule_df)
print("Minimal Fatigue:", min_fatigue)

