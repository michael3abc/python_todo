import pandas as pd
from collections import defaultdict
import copy

class Scheduler():
    def __init__(self):
        self.start_time = 9
        self.end_time = 17
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
    {"name": "Task A", "difficulty": 4, "time": 4, "fixed_time": ('Friday',9), "dependencies": []},
    # {"name": "Task A", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    {"name": "Task B", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
    # {"name": "Task C", "difficulty": 2, "time": 2, "fixed_time": None, "dependencies": []},
    {"name": "Task C", "difficulty": 2, "time": 2, "fixed_time": ('Friday',13), "dependencies": []},
]
scheduler.all_tasks = copy.deepcopy(scheduler.tasks)

schedule_df, min_fatigue = scheduler.minimize_total_fatigue()
print("Best Schedule:\n", schedule_df)
print("Minimal Fatigue:", min_fatigue)



# import pandas as pd
# from collections import defaultdict
# import itertools
#
# class Scheduler():
#     def __init__(self):
#         # 初始化行程表和可用時間
#         self.schedule = defaultdict(list)  # 每天的行程表
#         start_time = 9
#         end_time = 17
#         self.available_hours = {
#             day: list(range(start_time, end_time)) for day in ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#         }
#         self.tasks = []  # 儲存所有任務
#         self.min_fatigue = float('inf')
#
#
#
#     def assign_fixed_tasks(self):
#         """
#         將固定時間的任務分配到行程表。
#         """
#         for task in self.tasks:
#             if task["fixed_time"]:  # 如果任務有固定時間
#                 day, start_time = task["fixed_time"]
#                 duration = int(task["time"])
#
#                 # 確保時間段足夠
#                 if all(hour in self.available_hours[day] for hour in range(start_time, start_time + duration)):
#                     # 分配到行程表
#                     self.schedule[day].append((start_time, task["name"]))
#
#                     # 更新可用時間
#                     for hour in range(start_time, start_time + duration):
#                         self.available_hours[day].remove(hour)
#
#     def resolve_dependencies(self):
#         """
#         根據依賴關係排序任務。
#         """
#         sorted_tasks = []
#         resolved = set()  # 已排序的任務名稱
#
#         while self.tasks:
#             for task in self.tasks:
#                 dependencies = task["dependencies"]
#                 if not dependencies or all(dep in resolved for dep in dependencies):
#                     sorted_tasks.append(task)
#                     resolved.add(task["name"])
#                     self.tasks.remove(task)
#                     break
#         self.tasks = sorted_tasks
#
#     def assign_general_tasks(self):
#         """
#         將非固定任務分配到行程表。
#         """
#         # 任務按難度和時間排序
#         # self.tasks = sorted(self.tasks, key=lambda x: (-x["difficulty"], -x["time"]))
#
#         for task in self.tasks:
#             duration = int(task["time"])
#             for day, hours in self.available_hours.items():
#                 # 嘗試找到連續的空閒時段
#                 for i in range(len(hours) - duration + 1):
#                     if hours[i:i + duration] == list(range(hours[i], hours[i] + duration)):
#                         # 分配到行程表
#                         self.schedule[day].append((hours[i], task["name"]))
#
#                         # 更新可用時間
#                         for hour in range(hours[i], hours[i] + duration):
#                             self.available_hours[day].remove(hour)
#                         break
#                 else:
#                     continue
#                 break
#
#     def calculate_fatigue(self):
#         """
#         計算整個行程表的總疲勞值。
#         """
#         total_fatigue = 0
#
#         for day, task_list in self.schedule.items():
#             daily_fatigue = 0
#             daily_difficulty_sum = 0
#
#             for start_time, task_name in task_list:
#                 # 找到對應的任務
#                 task = next(t for t in self.tasks if t["name"] == task_name)
#                 difficulty = task["difficulty"]
#                 time = task["time"]
#                 task_fatigue = difficulty * time
#
#                 daily_fatigue += task_fatigue
#                 daily_difficulty_sum += difficulty
#
#             daily_fatigue *= (1 + daily_difficulty_sum)
#             total_fatigue += daily_fatigue
#
#         return total_fatigue
#
#
#     # def schedule_tasks(self):
#     #     """
#     #     執行任務排序並計算疲勞值。
#     #     """
#     #     # 固定任務優先分配
#     #     self.assign_fixed_tasks()
#     #
#     #     # 解決任務的依賴關係
#     #     self.resolve_dependencies()
#     #
#     #     # 分配一般任務
#     #     self.assign_general_tasks()
#     #
#     #     # 計算總疲勞值
#     #     total_fatigue = self.calculate_fatigue()
#     #
#     #     return self.schedule, total_fatigue
#
#     # def minimize_total_fatigue(self):
#     #     """
#     #     遍歷任務排列組合，找到疲勞值最小的最佳行程表。
#     #     """
#     #     import itertools
#     #
#     #     if not self.tasks:
#     #         return None, 0  # 沒有任務時直接返回
#     #
#     #     all_combinations = itertools.permutations(self.tasks)
#     #
#     #     for combination in all_combinations:
#     #         # 重置行程表
#     #         self.schedule = defaultdict(list)
#     #         self.available_hours = {
#     #             day: list(range(9, 17)) for day in
#     #             ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#     #         }
#     #
#     #         # 更新任務排序並分配
#     #         self.tasks = list(combination)
#     #         self.assign_fixed_tasks()
#     #         self.assign_general_tasks()
#     #
#     #         # 計算疲勞值
#     #         fatigue = self.calculate_fatigue()
#     #
#     #         if fatigue < self.min_fatigue:
#     #             self.min_fatigue = fatigue
#     #             self.best_schedule = self.schedule.copy()
#     #
#     #     # 基於最佳結果生成行程表
#     #     best_schedule_df = self.generate_schedule_dataframe(schedule=self.best_schedule)
#     #     return best_schedule_df, self.min_fatigue
#     def minimize_total_fatigue(self):
#         """
#         遍歷跨天、跨時段的任務排列組合，找到疲勞值最小的行程表。
#         """
#         if not self.tasks:
#             return None, 0  # 沒有任務時直接返回
#
#         all_combinations = itertools.permutations(self.tasks)  # 所有任務的排列
#         min_fatigue = float('inf')
#         best_schedule = None
#
#         for combination in all_combinations:
#             # 每次排列都需初始化可用時間與行程表
#             self.schedule = defaultdict(list)
#             self.available_hours = {
#                 day: list(range(9, 17)) for day in
#                 ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#             }
#             self.tasks = list(combination)
#
#             # 逐日嘗試分配任務
#             self.assign_fixed_tasks()
#             self.assign_general_tasks()
#
#             # 計算疲勞值
#             fatigue = self.calculate_fatigue()
#
#             # 更新最小疲勞值
#             if fatigue < min_fatigue:
#                 min_fatigue = fatigue
#                 best_schedule = self.schedule.copy()
#
#         # 將結果轉換為 DataFrame
#         schedule_df = self.generate_schedule_dataframe(schedule=best_schedule)
#         return schedule_df, min_fatigue
#
#
#     def generate_schedule_dataframe(self, schedule=None):
#         """
#         將行程表轉換為 DataFrame 並排序。
#         """
#         if schedule is None:
#             schedule = self.schedule
#
#         time_slots = [f"{int(hour)}:{'30' if hour % 1 else '00'}" for hour in
#                       [round(9 + 0.5 * i, 1) for i in range(17)]]
#         days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#
#         df = pd.DataFrame(index = time_slots, columns = days)
#
#         remaining_tasks = []
#         for task in self.tasks:
#             if task["fixed_time"]:
#                 day, start_time = task["fixed_time"]
#                 duration_slots = int(task["time"] * 2)  # 每小時占用 2 個 0.5 小時段
#                 for i in range(duration_slots):
#                     time_slot = round(start_time + 0.5 * i, 1)
#                     time_str = f"{int(time_slot)}:{'30' if time_slot % 1 else '00'}"
#                     if time_str in df.index:
#                         df.at[time_str, day] = task["name"]
#             else:
#                 remaining_tasks.append(task)
#
#         for task in remaining_tasks:
#             for day in days:
#                 duration_slots = int(task["time"] * 2)
#                 available_slots = [
#                     time for time in time_slots if pd.isna(df.at[time, day]) or df.at[time, day] == ""
#                 ]
#                 # 找到連續的空閒時間段
#                 for i in range(len(available_slots) - duration_slots + 1):
#                     if all(available_slots[i + j] in time_slots for j in range(duration_slots)):
#                         # 填入多時段
#                         for j in range(duration_slots):
#                             df.at[available_slots[i + j], day] = task["name"]
#                         break
#                 else:
#                     continue
#                 break
#
#             # 填充空白單元格為空字符串
#         df.fillna("", inplace=True)
#         return df
#
#     def __repr__(self):
#         return f"Schedule:\n{dict(self.schedule)}"
#
# scheduler = Scheduler()
#
#
# scheduler.tasks = [
#     {"name": "Task A", "difficulty": 4, "time": 4, "fixed_time": ('Friday',9), "dependencies": []},
#     {"name": "Task B", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
#     {"name": "Task C", "difficulty": 4, "time": 4, "fixed_time": None, "dependencies": []},
# ]
#
# # 分配任務並計算疲勞值
# scheduler.assign_fixed_tasks()
# scheduler.assign_general_tasks()
# total_fatigue = scheduler.calculate_fatigue()
#
# print("Schedule:", scheduler.schedule)
# print("Total Fatigue:", total_fatigue)
#
# # 測試最佳化排程
# best_schedule_df, min_fatigue = scheduler.minimize_total_fatigue()
# print("Best Schedule:\n", best_schedule_df)
# print("Minimal Fatigue:", min_fatigue)
