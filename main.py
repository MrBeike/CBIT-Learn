from api import CBIT


cbit = CBIT()


def login_workflow(username:str,password:str):
    username = str(input("登录名: ")).strip()
    password = str(input("密码: ")).strip()
    code_byte = cbit.initialPage()
    code = cbit.codeRecognize(code_byte)
    login_data = cbit.login(username, password,code)
    if login_data["success"] == "False":
        print(login_data["msg"])
        login_workflow(username, password)
    else:
        cbit.getMyCenter(login_data)