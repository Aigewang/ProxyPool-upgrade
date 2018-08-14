

class strongMetaclass(type):
    def __new__(cls,name,bases,attrs):
        count = 0
        attrs['__strongskills__']=[]#增加一个名叫'__strongskills__'的属性，其值为强化的技能一览表
        for key,value in attrs.items():
            if 'strong_' in key:
                attrs['__strongskills__'].append(key)
                count +=1
        attrs['__strongskills_numbers__'] = count#增加一个名叫'__strongskills_numbers'的属性，其值为强化技能的数量
        return type.__new__(cls,name,bases,attrs)
class strong_solider(object,metaclass=strongMetaclass):
    def __init__(self,name=None):
        self.name = name
    def get_skills(self,callback):
        skills = []
        skill = eval("self.{}()".format(callback))
        skills.append(skill)
        return skills
    def strong_run(self):
        return 'runing'
    def strong_swing(self):
        return 'swimming'
    def strong_fly(self):
        return 'flying'
    def strong_eat(self):
        return 'eatting'
solider1 =strong_solider(name='小明')
for i in range(solider1.__strongskills_numbers__):
    callback=solider1.__strongskills__[i]
    z=solider1.get_skills(callback)
    print(z)