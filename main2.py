#region general
import time
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

    def add_task(self,task):
        task.ID=len(self.task_list)
        self.task_list.append(task)
        
        return
    def update_whole_list(self,tag:TagSet):
        for t in self.task_list:
            t.update_tag(tag)
    
    def load_csv(self,file):
        return

    def export_csv(self,file_location):
        return
    def __repr__(self) -> str:
        return str(self.task_list)


#region menu_dict區
main_menu_dict={
    "1":"show_menu_task()",
    "2":"show_menu_tags()",
    "3":"show_menu_schdule()",
    "4":"show_menu_optimization()",
}
task_menu_dict={
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
schudule_menu_dict={
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
    #測試區
    print(f"show_menu_main")
    print(main_menu_dict)
    #程式區
    
    return 
def show_menu_task():
    #測試區
    print(f"show_menu_task")
    #程式區
    while True:
        print(task_menu_dict)
        choice=input()

        try:
            exec(task_menu_dict[choice])
            
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
        print(schudule_menu_dict)

        choice=input()

        try:
            exec(schudule_menu_dict[choice])
            
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
def task_add(tagset):
    #創造task
    print(f"please enter task name:")
    task_name=input()
    creating_task=Task(tagset,task_name)
    #print(creating_task)
    temp_attribute_dict={
    }
    #print(tag.attributes)
    for temp_tag in tagset.tags:
        print(f"what value do you want to set to {temp_tag}?")
        print(f"the value should be type of {tagset.tags_type[temp_tag].__name__}")
        
        temp_attribute_value=input()
        temp_attribute_dict[temp_tag]=tagset.tags_type[temp_tag](temp_attribute_value)
        
        
    print(temp_attribute_dict,sep="\n")
    
    
    
    
    #寫入task
    try:
        creating_task.set_attributes(temp_attribute_dict)
    except:
        print("you have type error")
    #print(creating_task)
    #asdf
    print(creating_task)

    taskset.add_task(creating_task)
    print(*taskset.task_list,sep="\n")

    return

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
#endregion     

def main():    
    while True:
        show_menu_main()
        first_input = input("Choose an option (1-4): ")
        try:
            exec(main_menu_dict[first_input])
        except:
            if first_input=="q":
                break
            else:
                print(f"unvalid code!")

def test():
    
    return



if __name__ == "__main__":
    tagset=TagSet()
    taskset=TaskSet()
    test()
#test