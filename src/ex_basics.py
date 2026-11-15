ITEMS = []


def add(title, code, inputs=()):
    ITEMS.append(("أساسيات", title, code.strip("\n") + "\n", tuple(inputs)))


add("طباعة عربي وإنجليزي", r'''
print("خالد")
print("Khaled")
print("مرحبا بك في بايثون")
print("Hello", "World", sep=" - ")
print("السطر الاول\nالسطر الثاني")
''')

add("إدخال الاسم والعمر", r'''
name = input("ادخل اسمك: ")
print("اهلا بك يا", name)
age = int(input("ادخل عمرك: "))
print("بعد 10 سنوات سيكون عمرك", age + 10)
''', ["خالد", "20"])

add("المتغيرات والأنواع", r'''
x = 10
y = 3.5
name = "خالد"
ok = True
items = [1, 2, 3]
for v in (x, y, name, ok, items):
    print(v, "->", type(v).__name__)
''')

add("العمليات الحسابية", r'''
a = 17
b = 5
print("الجمع:", a + b)
print("الطرح:", a - b)
print("الضرب:", a * b)
print("القسمة:", a / b)
print("القسمة الصحيحة:", a // b)
print("الباقي:", a % b)
print("القوة:", a ** 2)
''')

add("الشرط if / elif / else", r'''
score = int(input("ادخل الدرجة من 100: "))
if score >= 90:
    print("ممتاز")
elif score >= 75:
    print("جيد جدا")
elif score >= 50:
    print("مقبول")
else:
    print("راسب")
''', ["85"])

add("حلقة for", r'''
for i in range(1, 6):
    print("الرقم", i)

for letter in "Python":
    print(letter)
''')

add("حلقة while", r'''
n = 3
while n > 0:
    print(n)
    n -= 1
print("انتهى")
''')

add("القوائم lists", r'''
fruits = ["تفاح", "موز", "برتقال"]
fruits.append("عنب")
fruits.insert(0, "مانجو")
fruits.remove("موز")
print(fruits)
print("العدد:", len(fruits))
print("اول عنصر:", fruits[0])
print("اخر عنصر:", fruits[-1])
fruits.sort()
print("بعد الترتيب:", fruits)
''')

add("القواميس dict", r'''
person = {"الاسم": "خالد", "العمر": 20}
person["المدينة"] = "القاهرة"
for key, value in person.items():
    print(key, ":", value)
print("المفاتيح:", list(person.keys()))
print("القيم:", list(person.values()))
print(person.get("الهاتف", "غير موجود"))
''')

add("المجموعات sets و tuples", r'''
a = {1, 2, 3, 4}
b = {3, 4, 5, 6}
print("الاتحاد:", a | b)
print("التقاطع:", a & b)
print("الفرق:", a - b)
point = (10, 20)
x, y = point
print("x =", x, "y =", y)
''')

add("الدوال", r'''
def hello(name):
    return "مرحبا " + name


def add(a, b=10):
    return a + b


print(hello("خالد"))
print(add(5))
print(add(5, 7))
''')

add("الكلاسات", r'''
class Person:
    def __init__(self, name, age):
        self.name = name
        self.age = age

    def say(self):
        print("انا", self.name, "وعمري", self.age)


p = Person("خالد", 20)
p.say()
''')

add("try / except", r'''
try:
    x = int(input("ادخل رقما: "))
    print(10 / x)
except ZeroDivisionError:
    print("لا يمكن القسمة على صفر")
except ValueError:
    print("ادخل رقما صحيحا")
finally:
    print("انتهى البرنامج")
''', ["0"])

add("List comprehension", r'''
squares = [x * x for x in range(1, 8)]
evens = [x for x in range(20) if x % 2 == 0]
words = [w.upper() for w in ["a", "b", "c"]]
print(squares)
print(evens)
print(words)
''')

add("تنسيق النصوص f-string", r'''
name = "خالد"
price = 1234.5678
print(f"الاسم: {name}")
print(f"السعر: {price:.2f}")
print(f"السعر بفواصل: {price:,.1f}")
print(f"{5:03d}")
print(f"{0.256:.1%}")
''')

add("العمل مع النصوص", r'''
text = "  Hello Python World  "
print(text.strip())
print(text.upper())
print(text.lower())
print(text.replace("World", "Arabic"))
print(text.split())
print("-".join(["a", "b", "c"]))
print("Python" in text)
print(len(text.strip()))
''')

add("lambda و map و filter و sorted", r'''
nums = [5, 2, 9, 1, 7]
print(sorted(nums))
print(sorted(nums, reverse=True))
print(list(map(lambda x: x * 2, nums)))
print(list(filter(lambda x: x > 4, nums)))
students = [("علي", 80), ("سارة", 95), ("خالد", 70)]
print(sorted(students, key=lambda s: s[1], reverse=True))
''')

add("قراءة وكتابة ملف", r'''
import os
import tempfile

path = os.path.join(tempfile.gettempdir(), "demo.txt")
with open(path, "w", encoding="utf-8") as f:
    f.write("السطر الاول\n")
    f.write("السطر الثاني\n")

with open(path, "r", encoding="utf-8") as f:
    for line in f:
        print(line.strip())
''')

add("ملفات JSON", r'''
import json

data = {"name": "خالد", "skills": ["python", "flet"], "age": 20}
text = json.dumps(data, ensure_ascii=False, indent=2)
print(text)
back = json.loads(text)
print(back["name"], len(back["skills"]))
''')

add("التاريخ والوقت", r'''
from datetime import datetime, timedelta

now = datetime.now()
print("الان:", now.strftime("%Y-%m-%d %H:%M"))
print("بعد 10 ايام:", (now + timedelta(days=10)).strftime("%Y-%m-%d"))
print("اليوم رقم:", now.timetuple().tm_yday, "من السنة")
''')

add("استيراد المكتبات", r'''
import math
import random

print(math.sqrt(144))
print(math.pi)
print(math.floor(3.7), math.ceil(3.2))
print(random.randint(1, 100))
print(random.choice(["احمر", "اخضر", "ازرق"]))
''')
