#region general
import time
import pandas as pd
from tabulate import tabulate
from collections import defaultdict
import itertools

type_check_dictionary={"int": int, "float": float, "str": str, "bool": bool}
def type_checker(value):
    if isinstance(value, int):
        return "<class 'int'>"
    elif isinstance(value, float):
        return "<class 'float'>"
    elif isinstance(value, str):
        return "<class 'str'>"
    elif isinstance(value, bool):
        return "<class 'bool'>"
    elif isinstance(value, list):
        return "<class 'list'>"
    elif isinstance(value, dict):
        return "<class 'dict'>"
    elif isinstance(value, tuple):
        return "<class 'tuple'>"
    elif isinstance(value, set):
        return "<class 'set'>"
    else:
        return f"<class '{type(value).__name__}'>"

#endregion


class TagSet:
    def __init__(self):
        # 初始化一個空的字典用來存儲屬性
        self.tags = {
            "difficulty":None,
            "spent time estimate(hr)":None,
            "subject":None
            }
        self.tags_type={
            "difficulty":int,
            "spent time estimate(hr)":float,
            "subject":str
        }
        self.tags_visibility={
            #1是顯示 0是不顯示
            "difficulty":True,
            "spent time estimate(hr)":True,
            "subject":False

        }
        self.property_set={"name","type","visibility"}
        return
    
    
    
    def _has_tag_exist(self,tag):
        if tag in self.tags:
            return True
        else:
            return False    
    

    def _remove_tag_name(self,tag,*useless):
        if self._has_tag_exist(tag):
            self.tags.pop(tag)
        return 
    def _remove_tag_type(self,tag):
        if self._has_tag_exist(tag):
            self.tags_type.pop(tag)
        return
    def _remove_tag_visibility(self,tag):
        if self._has_tag_exist(tag):
            self.tags_visibility.pop(tag)
        return
    def remove_tag(self,tag):
        if self._has_tag_exist(tag):
            for i in self.property_set:
                method_name = f"_remove_tag_{i}"
                method = getattr(self, method_name)
                method(tag)

          
        return
    #把一個tag的其他propertydct刪掉

    def _set_tag_name(self,tag,*useless):
        if not self._has_tag_exist(tag):
            self.tags[tag]=None
        return 
    def _set_tag_type(self,tag,tag_type):
        if self._has_tag_exist(tag):
            self.tags_type[tag]=type_check_dictionary[tag_type]
        return
    def _set_tag_visibility(self,tag,tag_visibility):
        if self._has_tag_exist(tag):
            self.tags_visibility[tag]=tag_visibility
        return
    #set_tag會調用上面這些
    def set_tag(self,prop_dict:dict):
    #prop_dict={
    #    "name":"name",
    #    "type":"int",
    #    "visibility":0,
    #    ...    }
        current_name=prop_dict["name"]
    
        for key, value in prop_dict.items():
            method_name = f"_set_tag_{key}"
            # 使用 exec 動態調用方法
            method = getattr(self, method_name)
            method(current_name, value)
        return

    
    def __repr__(self):
        # 返回一個清楚顯示屬性值的字符串
        return f"{self.tags}"
    
class Task:
    def __init__(self,tagset:TagSet,name=""):
        # 初始化一個空的字典用來存儲屬性
        self.name=name
        self.createdtime=str(time.ctime(time.time()))
        self.ID=-1
        self.tagset_data=tagset
        #value 存在tagset_data.tags
        
    def set_attributes(self, value_dict:dict):
        self.tagset_data.tags=value_dict
        return
    
    def show_task(self,mode):
        #mode="simple" or "detail" 
        lines=[]
        lines.append(f"task name: {self.name}")
        lines.append(f"task create time: {self.createdtime}")
        lines.append(f"task ID: {self.ID}")
        lines.append("\n")
        if mode=="simple":
            for key,value in self.tagset_data.tags.items():
                if self.tagset_data.tags_visibility[key]:
                    lines.append(f"{key}: {value}")
                else:
                    pass
            return "  ".join(lines)
        elif mode=="detail":
            for key,value in self.tagset_data.tags.items():
                    lines.append(f"{key}: {value}")
        
            return "\n".join(lines)
    
    def update_tag(self,new_tagset:TagSet):
        temp_value_storage=self.tagset_data.tags
        self.tagset_data=new_tagset
        self.tagset_data.tags={key:temp_value_storage.setdefault(key,None) for key in self.tagset_data.tags.items()}
        return

    
    def __repr__(self):
        # 返回一個清楚顯示屬性值的字符串
        return self.show_task("simple")

class TaskSet:
    def __init__(self):
        self.task_list=[]

    # def add_task(self,task):
    #     task.ID=len(self.task_list)
    #     self.task_list.append(task)
    #
    #     return
    def add_task(self, name, difficulty, time, fixed_time=None, dependencies=[]):
        """
        新增一個任務到系統。
        :param name: 任務名稱 (str)
        :param difficulty: 任務難度 (int)
        :param time: 任務所需時間 (float)
        :param fixed_time: 固定時間 (tuple) e.g., ("Monday", 9) 或 None
        :param dependencies: 前置任務列表 (list) e.g., ["task_1"]
        """
        task = {
            "name": name,
            "difficulty": difficulty,
            "time": time,
            "fixed_time": fixed_time,
            "dependencies": dependencies,
        }
        self.tasks.append(task)

    # def add_task(scheduler):
    #     print("Enter task details:")
    #     name = input("Task name: ")
    #     difficulty = int(input("Difficulty (int): "))
    #     time = float(input("Time required (hours): "))
    #     fixed = input("Fixed time? (y/n): ").strip().lower() == "y"
    #     fixed_time = None
    #
    #     if fixed:
    #         day = input("Day (e.g., Monday): ")
    #         start_time = int(input("Start time (hour): "))
    #         fixed_time = (day, start_time)
    #
    #     dependencies = input("Dependencies (comma-separated, leave blank if none): ").split(",")
    #     dependencies = [d.strip() for d in dependencies if d.strip()]
    #
    #     scheduler.add_task(name, difficulty, time, fixed_time, dependencies)
    #     print(f"Task '{name}' added successfully!")
    #     return

    def update_whole_list(self,tag:TagSet):
        for t in self.task_list:
            t.update_tag(tag)
    
    def load_csv(self,file):
        return

    def export_csv(self,file_location):
        return
    def __repr__(self) -> str:
        return str(self.task_list)

from collections import defaultdict
import itertools
import pandas as pd


class Scheduler:
    def __init__(self):
        # 初始化行程表和可用時間
        self.schedule = defaultdict(list)  # 每天的行程表
        start_time = 9
        end_time = 17
        self.available_hours = {
            day: list(range(start_time, end_time)) for day in
            ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        }
        self.tasks = []  # 儲存所有任務
        self.min_fatigue = float('inf')

    def assign_fixed_tasks(self):
        """
        將固定時間的任務分配到行程表。
        """
        for task in list(self.tasks):  # 使用 list 避免修改迴圈中的物件
            if task["fixed_time"]:  # 如果任務有固定時間
                day, start_time = task["fixed_time"]
                duration = int(task["time"])

                # 確保時間段足夠
                if all(hour in self.available_hours[day] for hour in range(start_time, start_time + duration)):
                    # 分配到行程表
                    self.schedule[day].append((start_time, task["name"]))

                    # 更新可用時間
                    for hour in range(start_time, start_time + duration):
                        self.available_hours[day].remove(hour)

                    # 從任務清單中移除該任務
                    self.tasks.remove(task)

    def assign_general_tasks(self):
        """
        將非固定任務分配到行程表。
        """
        for task in list(self.tasks):
            duration = int(task["time"])
            for day, hours in self.available_hours.items():
                # 嘗試找到連續的空閒時段
                for i in range(len(hours) - duration + 1):
                    if hours[i:i + duration] == list(range(hours[i], hours[i] + duration)):
                        # 分配到行程表
                        self.schedule[day].append((hours[i], task["name"]))

                        # 更新可用時間
                        for hour in range(hours[i], hours[i] + duration):
                            self.available_hours[day].remove(hour)

                        # 從任務清單中移除該任務
                        self.tasks.remove(task)
                        break
                else:
                    continue
                break

    def calculate_fatigue(self):
        """
        計算整個行程表的總疲勞值。
        """
        total_fatigue = 0

        for day, task_list in self.schedule.items():
            daily_fatigue = 0
            daily_difficulty_sum = 0

            for start_time, task_name in task_list:
                # 根據任務名稱在初始任務清單中查找
                task = next(t for t in self.tasks + sum(self.schedule.values(), []) if t["name"] == task_name)
                difficulty = task["difficulty"]
                time = task["time"]
                task_fatigue = difficulty * time

                daily_fatigue += task_fatigue
                daily_difficulty_sum += difficulty

            # 基於每日難度進行加權
            daily_fatigue *= (1 + daily_difficulty_sum)
            total_fatigue += daily_fatigue

        return total_fatigue

    def minimize_total_fatigue(self):
        """
        遍歷跨天、跨時段的任務排列組合，找到疲勞值最小的行程表。
        """
        if not self.tasks:
            return None, 0  # 沒有任務時直接返回

        all_combinations = itertools.permutations(self.tasks)  # 所有任務的排列
        min_fatigue = float('inf')
        best_schedule = None

        for combination in all_combinations:
            # 每次排列都需初始化可用時間與行程表
            self.schedule = defaultdict(list)
            self.available_hours = {
                day: list(range(9, 17)) for day in
                ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            }
            self.tasks = list(combination)

            # 逐日嘗試分配任務
            self.assign_fixed_tasks()
            self.assign_general_tasks()

            # 計算疲勞值
            fatigue = self.calculate_fatigue()

            # 更新最小疲勞值
            if fatigue < min_fatigue:
                min_fatigue = fatigue
                best_schedule = self.schedule.copy()

        # 將結果轉換為 DataFrame
        schedule_df = self.generate_schedule_dataframe(schedule=best_schedule)
        return schedule_df, min_fatigue

    def generate_schedule_dataframe(self, schedule=None):
        """
        將行程表轉換為 DataFrame 並排序。
        """
        if schedule is None:
            schedule = self.schedule

        time_slots = [f"{int(hour)}:{'30' if hour % 1 else '00'}" for hour in
                      [round(9 + 0.5 * i, 1) for i in range(17)]]
        days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]

        df = pd.DataFrame(index=time_slots, columns=days)

        for day, tasks in schedule.items():
            for start_time, task_name in tasks:
                df.at[f"{start_time}:00", day] = task_name

        # 填充空白單元格為空字符串
        df.fillna("", inplace=True)
        return df

    def __repr__(self):
        return f"Schedule:\n{dict(self.schedule)}"


# class optimize(Scheduler):
#     def __init__(self):
#         super().__init__()  # 繼承 Scheduler 的屬性和方法
#         self.best_schedule = None  # 儲存最佳行程
#         self.min_fatigue = float('inf')  # 初始化最小疲勞值為正無窮大
#
#     def minimize_total_fatigue(self):
#         """
#         遍歷任務排列組合，找到疲勞值最小的最佳行程表。
#         """
#         import itertools
#
#         if not self.tasks:
#             return None, 0  # 沒有任務時直接返回
#
#         all_combinations = itertools.permutations(self.tasks)
#
#         for combination in all_combinations:
#             # 重置行程表
#             self.schedule = defaultdict(list)
#             self.available_hours = {
#                 day: list(range(9, 17)) for day in
#                 ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
#             }
#
#             # 更新任務排序並分配
#             self.tasks = list(combination)
#             self.assign_fixed_tasks()
#             self.assign_general_tasks()
#
#             # 計算疲勞值
#             fatigue = self.calculate_fatigue()
#
#             if fatigue < self.min_fatigue:
#                 self.min_fatigue = fatigue
#                 self.best_schedule = self.schedule.copy()
#
#         # 基於最佳結果生成行程表
#         best_schedule_df = self.generate_schedule_dataframe(schedule=self.best_schedule)
#         return best_schedule_df, self.min_fatigue


#region menu_dict區
main_menu_display = {
    "1": "Task Management",
    "2": "Tag Management",
    "3": "Schedule Management",
    "4": "Optimization",
}
# 顯示用字典



main_menu_dict={
    "1":"task_add(tagset)",
    "2":"task_remove()",
    "3":"task_search()",
    "4":"task_edit()",
    "5":"task_list()"
}
tags_menu_dict={
    "1":"tags_add(tagset)",
    "2":"tags_remove(tagset)",
    "3":"tags_list(tagset)",
    "4":"tags_edit(tagset)"
}

schedule_menu_dict={
    "1":"schudule_manual_arrange()",
    "2":"tags_auto_arrange()",
}
optimization_menu_dict={
    "1":"optimization_edit_fatigue_function()",
    "2":"optimization_edit_urgency_function()",
    "3":"optimization_edit_schudule_function()",
}
#endregion
#region menu區
def show_menu_main():
    print("\nMain Menu:")
    for key, value in main_menu_display.items():
        print(f"{key}. {value}")
    
    return 
def show_menu_task():
    #測試區
    print(f"show_menu_task")
    #程式區
    while True:
        print(main_menu_dict)
        choice=input()

        try:
            exec(main_menu_dict[choice])
            
        except Exception as e:
            print(e)
            if choice=="q":
                break
            else:
                print(f"unvalid code!")
    return
def show_menu_tags():
    #測試區
    print(f"show_menu_tags")
    #程式區
    while True:
        print(tags_menu_dict)

        choice=input()
        try:
            exec(tags_menu_dict[choice])
            
        except Exception as e:
            print(e)
            if choice=="q":
                break
            else:
                print(f"123")
        taskset.update_whole_list(tagset)
    return
def show_menu_schdule():
    #測試區
    print(f"show_menu_schdule")
    #程式區
    while True:
        print(schedule_menu_dict)

        choice=input()

        try:
            exec(schedule_menu_dict[choice])
            
        except:
            if choice=="q":
                break
            else:
                print(f"unvalid code!")
    return
def show_menu_optimization():
    #測試區
    print(f"show_menu_optimization")
    #程式區'
    while True:
        print(optimization_menu_dict)

        choice=input()

        try:
            exec(optimization_menu_dict[choice])
            
        except:
            if choice=="q":
                break
            else:
                print(f"unvalid code!")
    return
#endregion
#region task區
# def task_add(tagset):
#     #創造task
#     print(f"please enter task name:")
#     task_name=input()
#     creating_task=Task(tagset,task_name)
#     #print(creating_task)
#     temp_attribute_dict={
#     }
#     #print(tag.attributes)
#     for temp_tag in tagset.tags:
#         print(f"what value do you want to set to {temp_tag}?")
#         print(f"the value should be type of {tagset.tags_type[temp_tag].__name__}")
#
#         temp_attribute_value=input()
#         temp_attribute_dict[temp_tag]=tagset.tags_type[temp_tag](temp_attribute_value)
#
#
#     print(temp_attribute_dict,sep="\n")
    # 定義任務添加功能

# 定義任務添加功能
def task_add(scheduler):
    print("Enter task details:")
    name = input("Task name: ")
    difficulty = int(input("Difficulty (int): "))
    time = float(input("Time required (hours): "))
    fixed = input("Fixed time? (y/n): ").strip().lower() == "y"
    fixed_time = None

    if fixed:
        day = input("Day (e.g., Monday): ")
        start_time = int(input("Start time (hour): "))
        fixed_time = (day, start_time)

    dependencies = input("Dependencies (comma-separated, leave blank if none): ").split(",")
    dependencies = [d.strip() for d in dependencies if d.strip()]

    scheduler.add_task(name, difficulty, time, fixed_time, dependencies)
    print(f"Task '{name}' added successfully!\n")

#endregion

#region tag區
def tags_add(tagset:TagSet):
    temp_dict={key:None for key in tagset.property_set}
    print("input tag name and better write format after name")
    print("e.g. difficulty (int from 1 to 5)")
    print("tag name:")
    tag_name=input( )
    temp_dict["name"]=tag_name

    print(f"tag type(int,float,list,...):")
    tag_type=input()
    temp_dict["type"]=tag_type
    tagset.set_tag(temp_dict)
    return
def tags_list(tagset:TagSet):
    print(f"In sorted order")
    print()
    print(f"not functioning!!!!!!!!!!!!")
    ###改成字典後sorted要修
    ##或是做一個可以排名這些的order
    print(f"_________________________")
    
    print(f"In created order")
    print(f"_________________________")

    ###這裡要改美觀
    print(*(tagset.tags.keys()), sep="\n")
    print()
    return
def tags_remove(tagset:TagSet):
    tags_list(tagset)
    print(f"enter a attribute to remove:")
    removing_tag=input()
    if removing_tag in tagset.tags.keys():
        print(f"Are you sure you want to remove {removing_tag}? Enter 'y' to remove.")
        print(f"every task will lose the attribute")
        if input()=="y":
            tagset.remove_tag(removing_tag)
            print(f"remove successfully")
        else:
            print(f"the action is cancelled.")

    else:
        print(f"cannot find this attribute.")
    return
def task_menu(scheduler):
    while True:
        print("\nTask Menu:")
        for key, value in main_menu_dict.items():
            print(f"{key}. {value}")
        choice = input("Choose an option: ")
        if choice == "1":
            task_add(scheduler)
        elif choice == "2":
            scheduler.list_tasks()
        elif choice == "q":
            break
        else:
            print("Invalid option, please try again.")


#endregion     

# def main():
#     scheduler = Scheduler()
#     while True:
#         show_menu_main()
#         first_input = input("Choose an option (1-4): ")
#         try:
#             exec(main_menu_dict[first_input])
#         except:
#             if first_input=="q":
#                 break
#             else:
#                 print(f"unvalid code!")



# def main():
#     scheduler = Scheduler()
#     main_menu_actions = {
#         "1": lambda: task_add(scheduler),  # 傳遞 scheduler 實例到 task_add
#         "2": show_menu_tags,
#         "3": show_menu_schdule,
#         "4": show_menu_optimization,
#     }
#     while True:
#         show_menu_main()  # 顯示主選單
#         first_input = input("Choose an option (1-4, or 'q' to quit and schedule tasks): ")
#         try:
#             if first_input == "q":
#                 # 在退出前調用 Scheduler 進行排序
#                 print("Generating schedule...")
#                 schedule, total_fatigue = scheduler.schedule_tasks()
#                 print("\nGenerated Schedule:")
#                 print(schedule)
#                 print(f"\nTotal Fatigue: {total_fatigue}")
#                 break  # 結束程式
#             elif first_input in main_menu_actions:
#                 main_menu_actions[first_input]()  # 執行選單對應功能
#             else:
#                 print("Invalid option. Please choose again.")
#         except Exception as e:
#             print(f"An error occurred: {e}")



def main():
    scheduler = Scheduler()  # 初始化 Scheduler 實例

    while True:
        show_menu_main()
        first_input = input("Choose an option (1-4, or 'q' to quit): ")
        if first_input == "1":
            task_menu(scheduler)
        elif first_input == "2":
            print("Tag Management - Not implemented yet!")
            show_menu_tags()

        elif first_input == "3":
            print("Schedule Management - Not implemented yet!")

        elif first_input == "4":
            best_schedule_df, min_fatigue = scheduler.minimize_total_fatigue()

            if best_schedule_df is not None:
                print("\nOptimized Schedule:")
                print(tabulate(best_schedule_df, headers="keys", tablefmt="fancy_grid"))
                print(f"\nMinimum Fatigue: {min_fatigue}")
            else:
                print("No tasks available for optimization.")

            # print(scheduler.calculate_fatigue())

        elif first_input == "q":
            print("Exiting program...")
            break
        else:
            print("Invalid option, please try again.")



def test():
    main()
    return



if __name__ == "__main__":
    tagset=TagSet()
    taskset=TaskSet()
    test()

# if __name__ == "__main__":
#     main()