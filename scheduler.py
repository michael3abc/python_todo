# scheduler.py
import copy
import numpy as np

class Scheduler:
    def __init__(self, start_time=9, end_time=17, interval_minutes=30, fatigue_calculation=None):
        """
        初始化排程器。

        :param start_time: 工作開始時間（24小時制），預設為9。
        :param end_time: 工作結束時間（24小時制），預設為17。
        :param interval_minutes: 每個時間區間的分鐘數，預設為30。
        :param fatigue_calculation: 用戶自定義的疲勞計算函數。
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
        self.schedule = [[] for _ in range(7)]  # 0: Monday, ..., 6: Sunday
        self.tasks = []
        self.task_dict = {}  # 用於加速任務查找
        self.fatigue_calculation = fatigue_calculation or self.default_fatigue_calculation

    def default_fatigue_calculation(self, task):
        """
        默認的疲勞計算方式：difficulty * time

        :param task: 任務字典
        :return: 計算出的疲勞值
        """
        return task.get("difficulty", 1) * task.get("time", 1)

    def calculate_fatigue(self):
        total_fatigue = 0
        for day_tasks in self.schedule:
            daily_fatigue = 0
            daily_priority_sum = 0
            for task in day_tasks:
                task_fatigue = self.fatigue_calculation(task)
                daily_fatigue += task_fatigue
                daily_priority_sum += task.get("priority", 0)
            daily_fatigue *= (1 + daily_priority_sum)
            total_fatigue += daily_fatigue
        return total_fatigue

    def assign_task(self, task):
        """
        嘗試將任務分配到排程中。

        :param task: 任務字典
        :return: 是否成功分配
        """
        duration = int(task["time"])
        num_slots = duration * 2  # 30分鐘一個區間

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]  # e.g., ('Monday', 9, 0)
            day_index = self.days.index(day)
            start_slot = int((start_hour - self.start_time) * 2 + start_minute / self.interval_minutes)
            if start_slot < 0 or start_slot + num_slots > self.num_intervals_per_day:
                return False  # 固定時間超出範圍
            # 檢查是否有空閒
            for slot in range(start_slot, start_slot + num_slots):
                if self.schedule[day_index].count(slot) > 0:
                    return False  # 時間區間已被佔用
            # 分配任務
            for slot in range(start_slot, start_slot + num_slots):
                self.schedule[day_index].append(task)
            return True
        else:
            # 隨機或優先選擇可用的時間區間
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    # 檢查區間是否空閒
                    occupied = False
                    for slot in range(start_slot, start_slot + num_slots):
                        if any(existing_task for existing_task in self.schedule[day_index] if existing_task == task):
                            occupied = True
                            break
                    if not occupied:
                        # 分配任務
                        for slot in range(start_slot, start_slot + num_slots):
                            self.schedule[day_index].append(task)
                        return True
            return False  # 沒有可用的時間區間

    def minimize_total_fatigue(self):
        self.min_fatigue = float('inf')
        self.best_schedule = copy.deepcopy(self.schedule)
        self.backtrack(self.tasks, 0)
        return self.best_schedule, self.min_fatigue

    def backtrack(self, tasks, index):
        if index >= len(tasks):
            fatigue = self.calculate_fatigue()
            if fatigue < self.min_fatigue:
                self.min_fatigue = fatigue
                self.best_schedule = copy.deepcopy(self.schedule)
            return

        task = tasks[index]
        possible_assignments = self.get_possible_assignments(task)
        for day_index, start_slot in possible_assignments:
            # 分配任務
            for _ in range(int(task["time"] * 2)):
                self.schedule[day_index].append(task)
            # 繼續遞迴
            self.backtrack(tasks, index + 1)
            # 撤銷分配
            for _ in range(int(task["time"] * 2)):
                self.schedule[day_index].remove(task)

    def get_possible_assignments(self, task):
        """
        獲取任務可能的分配位置。

        :param task: 任務字典
        :return: 列表，包含 (day_index, start_slot) 的元組
        """
        assignments = []
        duration = int(task["time"])
        num_slots = duration * 2

        if task.get("fixed_time"):
            day, start_hour, start_minute = task["fixed_time"]
            day_index = self.days.index(day)
            start_slot = int((start_hour - self.start_time) * 2 + start_minute / self.interval_minutes)
            if 0 <= start_slot <= self.num_intervals_per_day - num_slots:
                # 檢查是否有空閒
                occupied = False
                for slot in range(start_slot, start_slot + num_slots):
                    if any(existing_task for existing_task in self.schedule[day_index] if existing_task == task):
                        occupied = True
                        break
                if not occupied:
                    assignments.append((day_index, start_slot))
        else:
            for day_index in range(7):
                for start_slot in range(self.num_intervals_per_day - num_slots + 1):
                    # 檢查是否有空閒
                    occupied = False
                    for slot in range(start_slot, start_slot + num_slots):
                        if any(existing_task for existing_task in self.schedule[day_index] if existing_task == task):
                            occupied = True
                            break
                    if not occupied:
                        assignments.append((day_index, start_slot))
        return assignments

    def generate_schedule_list(self):
        """
        將排程轉換為列表格式，便於 GUI 使用。

        :return: 二維列表，7天，每天16個時間區間
        """
        schedule_list = [[] for _ in range(7)]
        for day_index, day_tasks in enumerate(self.schedule):
            # 假設每個任務佔用固定的時間區間
            for task in day_tasks:
                # 根據任務的固定時間或隨機分配時間
                # 此處需要根據具體實現進行調整
                pass  # 詳細實現依賴於 assign_task 的具體邏輯
        return schedule_list

    def add_tasks(self, tasks):
        self.tasks.extend(tasks)
        for task in tasks:
            self.task_dict[task["name"]] = task


tasks = [
    {
        "name": "Task 1",
        "time": 4,  # 持續 2 小時
        "difficulty": 4,  # 難度 3
        "priority": 1,  # 優先級 1
        "fixed_time": ("Monday", 9, 0)  # 固定時間：星期一，從 9:00 開始
    },
    {
        "name": "Task 2",
        "time": 4,  # 持續 1 小時
        "difficulty": 4,
        "priority": 2,
        "fixed_time": ("Monday", 11, 0)
    },
    # {
    #     "name": "Task 3",
    #     "time": 1.5,  # 持續 1 小時 30 分鐘
    #     "difficulty": 4,
    #     "priority": 3,
    #     "fixed_time": ("Tuesday", 14, 30)
    # },
    # {
    #     "name": "Task 4",
    #     "time": 0.5,  # 持續 30 分鐘
    #     "difficulty": 1,
    #     "priority": 0,
    #     "fixed_time": None  # 無固定時間，隨機分配
    # },
    # {
    #     "name": "Task 5",
    #     "time": 2,
    #     "difficulty": 5,
    #     "priority": 2,
    #     "fixed_time": None  # 無固定時間，隨機分配
    # }
]

import re


def generate_fatigue_function(expression):
    """
    根據用戶輸入的數學式子生成一個疲勞計算函數。

    :param expression: 用戶輸入的數學式子，如 'difficulty * time * priority'
    :return: 生成的計算疲勞值的函數
    """

    # 檢查式子是否包含允許的變數
    valid_vars = ['difficulty', 'time', 'priority', 'task_num']
    pattern = r'\b(?:' + '|'.join(valid_vars) + r')\b'
    if not all(re.search(pattern, expr) for expr in expression.split('*')):
        raise ValueError("數學式子中包含無效變數，僅允許 difficulty, time, priority, task_num。")

    # 返回一個可以執行計算的函數
    def fatigue_function(task):
        # 使用 eval 來計算疲勞值，根據用戶輸入的表達式
        task_num = 1  # 默認的任務數量
        return eval(expression, {}, {
            'difficulty': task.get("difficulty", 1),
            'time': task.get("time", 1),
            'priority': task.get("priority", 0),
            'task_num': task_num
        })

    return fatigue_function


# 範例使用
if __name__ == "__main__":
    # 讓使用者輸入數學式子
    user_expression = input("請輸入疲勞計算公式（例如 'difficulty * time * priority'）：")

    # 生成自定義的疲勞計算函數
    fatigue_function = generate_fatigue_function(user_expression)

    # 範例任務
    task = {
        "name": "Task 1",
        "difficulty": 3,
        "time": 2,
        "priority": 1,
        "task_num": 2
    }

    # 使用自定義的疲勞計算函數計算疲勞值
    fatigue_value = fatigue_function(task)
    print(f"計算出的疲勞值: {fatigue_value}")
