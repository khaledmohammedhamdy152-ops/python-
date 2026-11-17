ITEMS = []
B, T, G, A = "أساسيات", "أدوات", "ألعاب", "خوارزميات"


def add(cat, title, code, inputs=()):
    ITEMS.append((cat, title, code.strip("\n") + "\n", tuple(inputs)))


add(B, "الشرط المتداخل والعوامل المنطقية", r'''
age = int(input("ادخل عمرك: "))
has_id = input("هل معك هوية؟ (نعم/لا): ") == "نعم"
if age >= 18 and has_id:
    print("مسموح بالدخول")
elif age >= 18 or has_id:
    print("ينقصك شرط واحد")
else:
    print("غير مسموح")
''', ["20", "نعم"])

add(B, "break و continue", r'''
for i in range(1, 11):
    if i == 3:
        continue
    if i == 8:
        break
    print(i)
print("انتهت الحلقة")
''')

add(B, "الحلقات المتداخلة (مثلث نجوم)", r'''
n = int(input("ارتفاع المثلث: "))
for i in range(1, n + 1):
    print(" " * (n - i) + "*" * (2 * i - 1))
''', ["5"])

add(B, "الدوال والقيم الافتراضية", r'''
def greet(name, greeting="مرحبا"):
    return f"{greeting} يا {name}"

print(greet("خالد"))
print(greet("سارة", "اهلا"))
print(greet(greeting="يا هلا", name="علي"))
''')

add(B, "*args و **kwargs", r'''
def total(*nums):
    return sum(nums)

def show(**info):
    for k, v in info.items():
        print(k, "=", v)

print(total(1, 2, 3, 4))
show(name="خالد", age=20, city="القاهرة")
''')

add(B, "العودية (Recursion)", r'''
def countdown(n):
    if n == 0:
        print("انطلق!")
        return
    print(n)
    countdown(n - 1)

countdown(5)
''')

add(B, "الوراثة في الكلاسات", r'''
class Animal:
    def __init__(self, name):
        self.name = name
    def speak(self):
        return "..."

class Dog(Animal):
    def speak(self):
        return "هو هو"

class Cat(Animal):
    def speak(self):
        return "مياو"

for a in (Dog("بلاك"), Cat("لولو")):
    print(a.name, "يقول", a.speak())
''')

add(B, "قاموس متداخل وترتيب", r'''
students = {
    "علي": {"math": 90, "sci": 80},
    "سارة": {"math": 95, "sci": 85},
    "منى": {"math": 70, "sci": 99},
}
for name, g in students.items():
    print(name, "المجموع:", sum(g.values()))
best = max(students, key=lambda n: sum(students[n].values()))
print("الاول:", best)
''')

add(B, "المولدات والتكرار enumerate/zip", r'''
names = ["علي", "سارة", "منى"]
marks = [90, 85, 70]
for i, (n, m) in enumerate(zip(names, marks), 1):
    print(i, n, m)
print([x * x for x in range(1, 6)])
''')

add(B, "الاستثناءات المخصصة", r'''
class NegativeError(Exception):
    pass

def sqrt_int(n):
    if n < 0:
        raise NegativeError("لا جذر لرقم سالب")
    return int(n ** 0.5)

for v in (16, -4):
    try:
        print(v, "->", sqrt_int(v))
    except NegativeError as e:
        print("خطأ:", e)
''')

add(B, "الأرقام العشوائية", r'''
import random
print("رقم:", random.randint(1, 100))
print("اختيار:", random.choice(["تفاح", "موز", "عنب"]))
nums = list(range(1, 8))
random.shuffle(nums)
print("خلط:", nums)
print("عينة:", random.sample(range(1, 50), 6))
''')

add(B, "الدوال الرياضية math", r'''
import math
print("جذر 144:", math.sqrt(144))
print("باي:", round(math.pi, 4))
print("2 اس 10:", math.pow(2, 10))
print("تقريب لاعلى:", math.ceil(4.2), "لاسفل:", math.floor(4.8))
print("جيب 90:", round(math.sin(math.radians(90)), 2))
''')

add(T, "مؤقت وساعة", r'''
import time
n = int(input("عدد الثواني للعد: "))
for s in range(n, 0, -1):
    print(s)
    time.sleep(1)
print("انتهى الوقت!")
''', ["3"])

add(T, "حاسبة النسبة المئوية والخصم", r'''
price = float(input("السعر: "))
disc = float(input("نسبة الخصم %: "))
saved = price * disc / 100
print("وفرت:", round(saved, 2))
print("السعر بعد الخصم:", round(price - saved, 2))
''', ["500", "15"])

add(T, "تحويل درجات الحرارة", r'''
c = float(input("درجة الحرارة بالسيلزيوس: "))
print("فهرنهايت:", c * 9 / 5 + 32)
print("كلفن:", c + 273.15)
''', ["25"])

add(T, "حاسبة السرعة والمسافة والزمن", r'''
d = float(input("المسافة (كم): "))
t = float(input("الزمن (ساعة): "))
print("السرعة =", round(d / t, 2), "كم/س")
''', ["150", "2"])

add(T, "مولد جدول الضرب لأي رقم", r'''
n = int(input("اي رقم؟ "))
for i in range(1, 13):
    print(f"{n} × {i} = {n * i}")
''', ["7"])

add(T, "عدّاد الأحرف والكلمات والأسطر", r'''
text = input("اكتب نصا: ")
print("الاحرف:", len(text))
print("بدون مسافات:", len(text.replace(" ", "")))
print("الكلمات:", len(text.split()))
''', ["اهلا بك في بايثون"])

add(T, "قلب النص وتحويل الحالة", r'''
s = input("نص انجليزي: ")
print("معكوس:", s[::-1])
print("كبير:", s.upper())
print("صغير:", s.lower())
print("اول حرف كبير:", s.title())
''', ["hello World"])

add(T, "مفكرة بسيطة تحفظ في ملف", r'''
import os
path = "notes.txt"
note = input("اكتب ملاحظة: ")
with open(path, "a", encoding="utf-8") as f:
    f.write(note + "\n")
print("محتوى المفكرة:")
with open(path, encoding="utf-8") as f:
    for i, line in enumerate(f, 1):
        print(i, line.strip())
os.remove(path)
''', ["شراء خبز"])

add(T, "تحويل العملة", r'''
rates = {"USD": 1.0, "EUR": 0.92, "EGP": 48.0, "SAR": 3.75}
amount = float(input("المبلغ: "))
src = input("من (USD/EUR/EGP/SAR): ").upper()
dst = input("الى: ").upper()
if src in rates and dst in rates:
    print(round(amount / rates[src] * rates[dst], 2), dst)
else:
    print("عملة غير معروفة")
''', ["100", "USD", "EGP"])

add(T, "حاسبة الزكاة", r'''
money = float(input("المبلغ المدخر: "))
nisab = 85 * 4000
if money >= nisab:
    print("الزكاة:", round(money * 0.025, 2))
else:
    print("لم يبلغ النصاب (تقديري)")
''', ["500000"])

add(T, "عدّاد الأيام حتى تاريخ", r'''
from datetime import date
y = int(input("السنة: "))
m = int(input("الشهر: "))
d = int(input("اليوم: "))
diff = (date(y, m, d) - date.today()).days
print("المتبقي بالايام:", diff)
''', ["2030", "1", "1"])

add(T, "تحليل الأرقام (متوسط وأكبر وأصغر)", r'''
nums = [float(x) for x in input("ارقام مفصولة بمسافة: ").split()]
print("المجموع:", sum(nums))
print("المتوسط:", sum(nums) / len(nums))
print("الاكبر:", max(nums), "الاصغر:", min(nums))
print("مرتبة:", sorted(nums))
''', ["4 8 15 16 23 42"])

add(G, "لعبة سباق الارقام", r'''
import random
score = 0
for r in range(1, 4):
    a, b = random.randint(1, 9), random.randint(1, 9)
    ans = int(input(f"سؤال {r}: {a} + {b} = "))
    if ans == a + b:
        score += 1
        print("صحيح")
    else:
        print("خطأ، الاجابة", a + b)
print("نتيجتك:", score, "من 3")
''', ["14", "14", "14"])

add(G, "لعبة الكلمة المبعثرة", r'''
import random
words = ["python", "program", "keyboard", "computer"]
w = random.choice(words)
letters = list(w)
random.shuffle(letters)
print("رتّب الحروف:", "".join(letters))
g = input("اجابتك: ")
print("صحيح!" if g == w else f"خطأ، الكلمة هي {w}")
''', ["python"])

add(G, "اختر مغامرتك", r'''
print("انت امام بابين: 1) احمر  2) ازرق")
c = input("اختر 1 او 2: ")
if c == "1":
    print("وجدت كنزا!")
elif c == "2":
    print("سقطت في حفرة :(")
else:
    print("لم تختر شيئا فبقيت مكانك")
''', ["1"])

add(G, "رمي العملة والاحصاء", r'''
import random
heads = tails = 0
for _ in range(100):
    if random.choice(["H", "T"]) == "H":
        heads += 1
    else:
        tails += 1
print("صورة:", heads, "كتابة:", tails)
''')

add(A, "ترتيب الاختيار Selection Sort", r'''
a = [64, 25, 12, 22, 11]
for i in range(len(a)):
    m = i
    for j in range(i + 1, len(a)):
        if a[j] < a[m]:
            m = j
    a[i], a[m] = a[m], a[i]
print(a)
''')

add(A, "الترتيب السريع Quick Sort", r'''
def qs(a):
    if len(a) <= 1:
        return a
    p = a[0]
    return qs([x for x in a[1:] if x < p]) + [p] + qs([x for x in a[1:] if x >= p])

print(qs([9, 3, 7, 1, 8, 2, 5]))
''')

add(A, "البحث الخطي واعداد المرات", r'''
a = [3, 7, 3, 9, 3, 1]
x = 3
print("اول ظهور عند:", a.index(x))
print("عدد المرات:", a.count(x))
print("كل المواضع:", [i for i, v in enumerate(a) if v == x])
''')

add(A, "تحويل الرقم الى كلمات (1-99)", r'''
ones = ["", "واحد", "اثنان", "ثلاثة", "اربعة", "خمسة", "ستة", "سبعة", "ثمانية", "تسعة"]
tens = ["", "عشرة", "عشرون", "ثلاثون", "اربعون", "خمسون", "ستون", "سبعون", "ثمانون", "تسعون"]
n = int(input("رقم من 1 الى 99: "))
if n < 10:
    print(ones[n])
elif n % 10 == 0:
    print(tens[n // 10])
elif n < 20:
    print(ones[n % 10], "عشر")
else:
    print(ones[n % 10], "و", tens[n // 10])
''', ["45"])

add(A, "عدد الاعداد الاولية حتى N", r'''
n = int(input("N = "))
primes = [x for x in range(2, n + 1) if all(x % d for d in range(2, int(x ** 0.5) + 1))]
print(len(primes), "عددا اوليا:", primes)
''', ["50"])

add(A, "تحويل رقم لروماني", r'''
vals = [(1000, "M"), (900, "CM"), (500, "D"), (400, "CD"), (100, "C"), (90, "XC"),
        (50, "L"), (40, "XL"), (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I")]
n = int(input("رقم: "))
out = ""
for v, s in vals:
    while n >= v:
        out += s
        n -= v
print(out)
''', ["1994"])

add(A, "الاقواس المتوازنة (Stack)", r'''
s = input("عبارة اقواس: ")
stack = []
pairs = {")": "(", "]": "[", "}": "{"}
ok = True
for ch in s:
    if ch in "([{":
        stack.append(ch)
    elif ch in pairs:
        if not stack or stack.pop() != pairs[ch]:
            ok = False
            break
print("متوازنة" if ok and not stack else "غير متوازنة")
''', ["{[()]}"])
