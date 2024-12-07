import ast
import scheduler

test_data=[
    [1, "task1", 1733323532, {"difficulty": 5, "__spent time": 2, "__waiting": None}],
    [2, "task2", 1733323532, {"difficulty": 5, "__spent time": 2, "__waiting": 1}],
    [3, "task3", 1733323535, {"difficulty": 5, "spent time": 2, "comments": "this is too hard", "__waiting": None}],
]
a=[]

with open("./test_data.txt","w",encoding="utf-8") as file1:
    for i in test_data:
        file1.write(str(i)+",\n")
        scheduler = scheduler


with open("./test_data.txt","r",encoding="utf-8") as file1:
    x=file1.read()
    a=ast.literal_eval("["+x+"]")

print("++_________________")
for i in a:
    print(i)
    print(type(i[3]))