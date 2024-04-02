from api import CBIT
from prettytable import PrettyTable


def workflow():
    username = str(input("登录名: ").strip())
    password = str(input("密码: ").strip())
    code_byte = cbit.initialPage()
    code = cbit.codeRecognize(code_byte)
    login_data = cbit.login(username, password,code)
    classFlag = 1
    if login_data["success"] == False:
        print(login_data["msg"])
        workflow()
    else:
        while 1:
            if classFlag == 1:
                training_info = cbit.getMyCenter(login_data)
                my_trainings = training_info["mytrainingclass"]
                training_table = PrettyTable()
                training_table.field_names = ["序号","名称","总学时","学习进度"]
                for index,item in enumerate(my_trainings):
                    training_table.add_row([index,item["tc_name"],item["hour"],item["studyplan"]])
                print(training_table)
                classFlag += 1
            elif classFlag == 2:
                index = int(input("输入培训班序号: ").strip())
                training_detail = cbit.getTraining(training_info,index)
                training_lesson = training_detail["traininglesson"]
                lesson_table = PrettyTable()
                lesson_table.field_names = ["序号","名称","学习进度"]
                for index,item in enumerate(training_lesson):
                    studyplan = item.get("studyplan",0)
                    lesson_table.add_row([index, item["le_name"], studyplan])
                print(lesson_table)
                classFlag += 1
            elif classFlag == 3:
                index = int(input("输入课程序号: ").strip())
                lesson_detail = cbit.getLesson(training_detail, index)
                lesson_item = lesson_detail["lessonitem"]
                lesson_item_table = PrettyTable()
                lesson_item_table.field_names = ["序号","名称","学习进度"]
                for index,item in enumerate(lesson_item):
                    lesson_item_table.add_row([index, item["itemname"], item["studyplan"]])
                print(lesson_item_table)
                classFlag += 1
            elif classFlag == 4:
                index = int(input("输入视频序号: ").strip())
                video_detail = cbit.getVideo(lesson_detail, index)
                result = cbit.learn(video_detail)
                print(result)
                # TODO 如何实现学习完返回特定层级
                classFlag = int(input("输入返回层级:1回首页,2选培训班,3选课程，4选视频 ").strip())
        
if __name__ == "__main__":
    cbit = CBIT()
    workflow()