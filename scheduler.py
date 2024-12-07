# scheduler.py
import copy
import numpy as np
import re
from functools import lru_cache
import json


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
        self.best_day_fatigue = None  # 用於存儲最佳排程時每天的疲勞值

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

        # Sort tasks by priority ascending (lower priority first), tasks with priority=None last
        self.tasks.sort(key=lambda t: (t.get("priority") is None, t.get("priority", 0), self.count_possible_assignments(t)))

        self.min_fatigue = float('inf')
        self.best_schedule = None
        self.best_day_fatigue = None  # 初始化最佳每天疲勞值
        self.total_fatigue = 0.0

        self.backtrack(0)
        return self.best_schedule, self.min_fatigue, self.best_day_fatigue  # 修改返回值

    def backtrack(self, index):
        """
        Backtracking function to assign tasks and minimize fatigue.
        """
        if index >= len(self.tasks):
            if self.total_fatigue < self.min_fatigue:
                self.min_fatigue = self.total_fatigue
                self.best_schedule = [list(day) for day in self.schedule]
                self.best_day_fatigue = copy.deepcopy(self.day_fatigue)  # 保存當前每天的疲勞值
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

    @staticmethod
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


# 定義轉換函數
def convert_tasklist(tasklist):
    tasks = []
    for task in tasklist:
        _, name, _, attributes = task

        # 創建一個新的字典，移除鍵中的前綴下劃線並重命名鍵
        scheduler_task = {}

        for key, value in attributes.items():
            # 移除鍵中的前綴下劃線
            new_key = key.lstrip('_')

            # 重命名特定的鍵
            if new_key == 'spent time':
                new_key = 'time'
            elif new_key == 'waiting':
                new_key = 'priority'

            scheduler_task[new_key] = value

        # 確保 'name' 欄位存在，並進行格式化
        if 'name' not in scheduler_task or not scheduler_task['name']:
            scheduler_task['name'] = name.capitalize().replace('_', ' ')
        else:
            scheduler_task['name'] = scheduler_task['name'].capitalize().replace('_', ' ')

        # 確保 'time' 和 'difficulty' 欄位存在，並設置默認值
        scheduler_task['time'] = scheduler_task.get('time', 1)
        scheduler_task['difficulty'] = scheduler_task.get('difficulty', 1)

        # 將 'priority' 設置為 None 如果它不存在
        scheduler_task['priority'] = scheduler_task.get('priority', None)

        # 處理 'fixed_time'（如果存在）
        scheduler_task['fixed_time'] = scheduler_task.get('fixed_time', None)

        tasks.append(scheduler_task)
    return tasks


# 您的 tasklist
tasklist = [
    [1, 'task1', 1733323532, {'_name': 'task1', '_difficulty': 5, '_spent time': 2, '_waiting': None}],
    [2, 'task2', 1733323532, {'_name': 'task2', '_difficulty': 5, '_spent time': 2, '_waiting': 1}],
    # [3, 'task3', 1733323535, {'_name': 'task3', '_difficulty': 5, '_spent time': 2, '_comments': 'this is too hard', '_waiting': 2}],
    # 新增更多屬性
    [4, 'task4', 1733323536, {'_name': 'task4', '_difficulty': 4, '_spent time': 3, '_waiting': 1, '_priority_level': 'high', '_deadline': '2024-12-31'}],
    # [5, 'task3', 1733323535, {'_name': 'task5', '_difficulty': 5, '_spent time': 2, '_comments': 'this is too hard','_priority_level': 'low', '_waiting': None}],
    [6, 'task3', 1733323535, {'_name': 'task6', '_difficulty': 5, '_spent time': 2, '_comments': 'this is too hard','_priority_level': 'high', '_waiting': None}],]

# 轉換 tasklist
tasks = convert_tasklist(tasklist)

# 輸出轉換後的 tasks
print("轉換後的 tasks 列表:")
for task in tasks:
    print(task)

# 初始化 Scheduler 並添加任務
if __name__ == "__main__":
    user_allowed_vars = ['difficulty', 'time', 'priority', 'task_num', 'priority_level', 'deadline']
    user_expression = "difficulty * time"

    # 生成疲勞函數
    fatigue_function = Scheduler.generate_fatigue_function(user_expression, user_allowed_vars)

    # 初始化 Scheduler
    scheduler = Scheduler(fatigue_calculation=fatigue_function)

    # 添加轉換後的任務
    scheduler.add_tasks(tasks)

    # 計算最佳排程
    best_schedule, min_fatigue, best_day_fatigue = scheduler.minimize_total_fatigue()

    print("\n最小疲勞值:", min_fatigue)

    # 生成並打印最終排程
    final_list = scheduler.generate_schedule_list(best_schedule)
    for day_idx, day_name in enumerate(scheduler.days):
        print(day_name, final_list[day_idx])

    # 打印每天的疲勞值
    print("\n每天的疲勞值:")
    for day_idx, day_name in enumerate(scheduler.days):
        daily_fatigue = best_day_fatigue[day_idx] if best_day_fatigue else 0
        print(f"{day_name}: {daily_fatigue}")

    # 可選：將結果儲存為 JSON 文件
    schedule_output = {
        "total_fatigue": min_fatigue,
        "daily_fatigue": {scheduler.days[i]: best_day_fatigue[i] for i in range(7)} if best_day_fatigue else {},
        "schedule": {scheduler.days[i]: final_list[i] for i in range(7)}
    }

    with open("schedule_output.json", "w") as f:
        json.dump(schedule_output, f, ensure_ascii=False, indent=4)

    print("\n排程結果已儲存至 schedule_output.json")
