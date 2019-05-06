class Student:
    def __init__(self, **args):
        self.info = args

    def __getattr__(self, name):
        return self.info[name]

stu = Student(name= 'jack', age = 18)
print(stu.name)