import time
from typing import List

class TagSet:
    def __init__(self, tags=None):
        self.tags = tags if tags else []

class Task:
    def __init__(self, tagset: TagSet, name=""):
        self.name = name
        self.createdtime = str(time.ctime(time.time()))
        self.ID = -1
        self.tagset_data = tagset

def query_task_by_name(keyword: str, tasks: List[Task]) -> List[Task]:
    """
    根據關鍵字對 Task 名稱進行模糊搜尋。

    :param keyword: 關鍵字 (字串)
    :param tasks: 任務列表 (Task 物件的清單)
    :return: 匹配的 Task 物件清單
    """
    return [task for task in tasks if keyword.lower() in task.name.lower()]

# 測試範例
tagset = TagSet(["tag1", "tag2"])
tasks = [
    Task(tagset, name="Complete Report"),
    Task(tagset, name="Review Code"),
    Task(tagset, name="Weekly Meeting"),
    Task(tagset, name="Submit Assignment"),
]

keyword = input("")
matched_tasks = query_task_by_name(keyword, tasks)

print(f"搜尋關鍵字: '{keyword}'")
for task in matched_tasks:
    print(f"任務名稱: {task.name}, 建立時間: {task.createdtime}")