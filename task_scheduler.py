# 初始化顯示字典
main_menu_display = {
    "1": "show_menu_task()",
    "2": "show_menu_tags()",
    "3": "show_menu_schdule()",
    "4": "show_menu_optimization()",
}

# 定義功能函數
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
    print(f"Task '{name}' added successfully!")

def show_menu_tags():
    print("Tags menu - not implemented yet!")

def show_menu_schdule():
    print("Schedule menu - not implemented yet!")

def show_menu_optimization():
    print("Optimization menu - not implemented yet!")

# 定義 Scheduler 類
class Scheduler:
    def __init__(self):
        self.tasks = []  # 儲存所有任務

    def add_task(self, name, difficulty, time, fixed_time=None, dependencies=[]):
        task = {
            "name": name,
            "difficulty": difficulty,
            "time": time,
            "fixed_time": fixed_time,
            "dependencies": dependencies,
        }
        self.tasks.append(task)

    def schedule_tasks(self):
        # 模擬排程邏輯（簡化示例）
        schedule = {task["name"]: task for task in self.tasks}
        total_fatigue = sum(task["difficulty"] * task["time"] for task in self.tasks)
        return schedule, total_fatigue

def show_menu_main():
    print("show_menu_main")
    print(main_menu_display)  # 印出顯示字典內容

# 主程式執行邏輯
def main():
    scheduler = Scheduler()  # 初始化 Scheduler 實例

    # 執行用字典
    main_menu_actions = {
        "1": lambda: task_add(scheduler),  # 傳遞 scheduler 實例到 task_add
        "2": show_menu_tags,
        "3": show_menu_schdule,
        "4": show_menu_optimization,
    }

    while True:
        show_menu_main()
        first_input = input("Choose an option (1-4, or 'q' to quit and schedule tasks): ")
        try:
            if first_input == "q":
                # 調用 Scheduler 排程
                print("Generating schedule...")
                schedule, total_fatigue = scheduler.schedule_tasks()
                print("\nGenerated Schedule:")
                print(schedule)
                print(f"\nTotal Fatigue: {total_fatigue}")
                break  # 結束程式
            elif first_input in main_menu_actions:
                main_menu_actions[first_input]()  # 執行對應功能
            else:
                print("Invalid option. Please choose again.")
        except Exception as e:
            print(f"An error occurred: {e}")

# 程式入口
if __name__ == "__main__":
    main()
