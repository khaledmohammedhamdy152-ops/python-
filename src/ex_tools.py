ITEMS = []


def add(title, code, inputs=()):
    ITEMS.append(("أدوات", title, code.strip("\n") + "\n", tuple(inputs)))


add("فاحص قوة كلمة المرور", r'''
import re

COMMON = ["123456", "password", "qwerty", "111111", "123456789",
          "12345678", "abc123", "000000", "admin", "iloveyou"]


def check_password(pw):
    score = 0
    notes = []

    if pw.lower() in COMMON:
        return 0, ["كلمة مرور شائعة جدا ويسهل تخمينها"]

    if len(pw) >= 8:
        score += 1
    else:
        notes.append("اقل من 8 حروف")
    if len(pw) >= 12:
        score += 1
    if re.search(r"[a-z]", pw):
        score += 1
    else:
        notes.append("لا تحتوي حروف انجليزية صغيرة")
    if re.search(r"[A-Z]", pw):
        score += 1
    else:
        notes.append("لا تحتوي حروف انجليزية كبيرة")
    if re.search(r"[0-9]", pw):
        score += 1
    else:
        notes.append("لا تحتوي ارقاما")
    if re.search(r"[^A-Za-z0-9]", pw):
        score += 1
    else:
        notes.append("لا تحتوي رموزا مثل @ # !")
    if re.search(r"(.)\1\1", pw):
        score -= 1
        notes.append("فيها حرف مكرر 3 مرات متتالية")
    return max(score, 0), notes


while True:
    pw = input("ادخل كلمة المرور للفحص (او اكتب خروج): ")
    if pw == "خروج":
        break
    score, notes = check_password(pw)
    if score <= 2:
        verdict = "ضعيفة"
    elif score <= 4:
        verdict = "متوسطة"
    else:
        verdict = "قوية"
    print("النتيجة:", score, "من 6 ->", verdict)
    for n in notes:
        print(" - ", n)
    print()
''', ["123456", "Khaled2024", "K@haled#2024!Strong", "خروج"])

add("مولد كلمات مرور عشوائية", r'''
import random
import string

length = int(input("طول كلمة المرور: "))
count = int(input("كم كلمة تريد؟ "))
chars = string.ascii_letters + string.digits + "!@#$%&*?"

for i in range(count):
    pw = "".join(random.choice(chars) for _ in range(length))
    print(i + 1, "->", pw)
''', ["12", "3"])

add("آلة حاسبة متكاملة", r'''
import math

history = []


def ask_number(prompt):
    while True:
        text = input(prompt).strip()
        try:
            return float(text)
        except ValueError:
            print("رقم غير صحيح، حاول مرة اخرى")


def show(n):
    try:
        if n == int(n):
            return str(int(n))
    except (ValueError, OverflowError):
        pass
    return str(round(n, 6))


def calculate(op):
    if op == "6":
        a = ask_number("ادخل الرقم: ")
        if a < 0:
            return None, "لا يوجد جذر للعدد السالب"
        return math.sqrt(a), "جذر " + show(a)
    a = ask_number("الرقم الاول: ")
    b = ask_number("الرقم الثاني: ")
    if op == "1":
        return a + b, f"{show(a)} + {show(b)}"
    if op == "2":
        return a - b, f"{show(a)} - {show(b)}"
    if op == "3":
        return a * b, f"{show(a)} x {show(b)}"
    if op == "4":
        if b == 0:
            return None, "لا يمكن القسمة على صفر"
        return a / b, f"{show(a)} / {show(b)}"
    if op == "5":
        return a ** b, f"{show(a)} ^ {show(b)}"
    if op == "7":
        if b == 0:
            return None, "لا يمكن القسمة على صفر"
        return a % b, f"{show(a)} % {show(b)}"
    return None, "اختيار غير معروف"


MENU = """
===== الحاسبة =====
1 جمع     2 طرح
3 ضرب     4 قسمة
5 قوة     6 جذر تربيعي
7 باقي القسمة
8 عرض السجل
0 خروج"""

while True:
    print(MENU)
    op = input("اختر العملية: ").strip()
    if op == "0":
        print("مع السلامة")
        break
    if op == "8":
        if not history:
            print("السجل فارغ")
        for line in history:
            print(" ", line)
        continue
    value, label = calculate(op)
    if value is None:
        print("خطأ:", label)
    else:
        line = label + " = " + show(value)
        history.append(line)
        print("النتيجة:", line)
''', ["1", "5", "3", "4", "10", "0", "6", "-4", "8", "0"])

add("حاسبة كتلة الجسم BMI", r'''
weight = float(input("الوزن بالكيلوجرام: "))
height = float(input("الطول بالمتر: "))
bmi = weight / (height ** 2)
print(f"مؤشر كتلة الجسم: {bmi:.1f}")
if bmi < 18.5:
    print("نحافة")
elif bmi < 25:
    print("وزن طبيعي")
elif bmi < 30:
    print("وزن زائد")
else:
    print("سمنة")
''', ["70", "1.75"])

add("محول الوحدات", r'''
print("1) كيلومتر الى ميل")
print("2) كيلوجرام الى رطل")
print("3) مئوية الى فهرنهايت")
print("4) فهرنهايت الى مئوية")
choice = input("اختر: ")
value = float(input("القيمة: "))

if choice == "1":
    print(value, "كم =", round(value * 0.621371, 3), "ميل")
elif choice == "2":
    print(value, "كجم =", round(value * 2.20462, 3), "رطل")
elif choice == "3":
    print(value, "C =", round(value * 9 / 5 + 32, 2), "F")
elif choice == "4":
    print(value, "F =", round((value - 32) * 5 / 9, 2), "C")
else:
    print("اختيار غير صحيح")
''', ["3", "100"])

add("حاسبة العمر", r'''
from datetime import date

year = int(input("سنة الميلاد: "))
month = int(input("شهر الميلاد: "))
day = int(input("يوم الميلاد: "))

born = date(year, month, day)
today = date.today()
age = today.year - born.year
if (today.month, today.day) < (born.month, born.day):
    age -= 1
days = (today - born).days
print("عمرك بالسنوات:", age)
print("عمرك بالايام:", days)
''', ["2000", "5", "20"])

add("تقسيم الفاتورة والإكرامية", r'''
bill = float(input("قيمة الفاتورة: "))
tip_percent = float(input("نسبة الاكرامية %: "))
people = int(input("عدد الاشخاص: "))

tip = bill * tip_percent / 100
total = bill + tip
print(f"الاكرامية: {tip:.2f}")
print(f"الاجمالي: {total:.2f}")
print(f"نصيب كل شخص: {total / people:.2f}")
''', ["500", "10", "4"])

add("حاسبة الدرجات والمعدل", r'''
n = int(input("عدد المواد: "))
grades = []
for i in range(n):
    g = float(input(f"درجة المادة {i + 1}: "))
    grades.append(g)

avg = sum(grades) / len(grades)
print("المجموع:", sum(grades))
print("المعدل:", round(avg, 2))
print("اعلى درجة:", max(grades))
print("اقل درجة:", min(grades))
if avg >= 90:
    print("التقدير: امتياز")
elif avg >= 80:
    print("التقدير: جيد جدا")
elif avg >= 65:
    print("التقدير: جيد")
elif avg >= 50:
    print("التقدير: مقبول")
else:
    print("التقدير: راسب")
''', ["3", "90", "85", "70"])

add("تحليل نص", r'''
from collections import Counter

text = input("اكتب نصا للتحليل: ")
words = text.split()
letters = [c for c in text if c.isalpha()]

print("عدد الكلمات:", len(words))
print("عدد الحروف:", len(letters))
print("عدد المسافات:", text.count(" "))
if words:
    top = Counter(words).most_common(3)
    print("اكثر الكلمات تكرارا:")
    for word, count in top:
        print(" ", word, "->", count)
    print("اطول كلمة:", max(words, key=len))
''', ["انا احب بايثون وبايثون لغة جميلة وانا سعيد"])

add("فاحص البريد الإلكتروني", r'''
import re

pattern = r"^[\w.+-]+@[\w-]+\.[\w.-]+$"

while True:
    email = input("ادخل البريد (او خروج): ").strip()
    if email == "خروج":
        break
    if re.match(pattern, email):
        print("بريد صحيح")
    else:
        print("بريد غير صحيح")
''', ["khaled@gmail.com", "khaled@", "خروج"])

add("جدول الضرب", r'''
n = int(input("اي رقم تريد جدوله؟ "))
for i in range(1, 13):
    print(f"{n} x {i:2d} = {n * i}")
''', ["7"])

add("عداد تنازلي", r'''
import time

seconds = int(input("ادخل عدد الثواني: "))
while seconds > 0:
    print(seconds)
    time.sleep(1)
    seconds -= 1
print("انتهى الوقت!")
''', ["3"])

add("حاسبة المعادلة التربيعية", r'''
import math

print("المعادلة: ax2 + bx + c = 0")
a = float(input("a = "))
b = float(input("b = "))
c = float(input("c = "))

if a == 0:
    print("ليست معادلة تربيعية")
else:
    d = b * b - 4 * a * c
    if d > 0:
        x1 = (-b + math.sqrt(d)) / (2 * a)
        x2 = (-b - math.sqrt(d)) / (2 * a)
        print("حلان مختلفان:", x1, x2)
    elif d == 0:
        print("حل واحد:", -b / (2 * a))
    else:
        print("لا يوجد حل حقيقي")
''', ["1", "-5", "6"])

add("محول الأعداد (ثنائي وست عشري)", r'''
n = int(input("ادخل رقما بالنظام العشري: "))
print("ثنائي:", bin(n)[2:])
print("ثماني:", oct(n)[2:])
print("ست عشري:", hex(n)[2:].upper())

b = input("ادخل رقما ثنائيا للتحويل لعشري: ")
print("عشري:", int(b, 2))
''', ["255", "101010"])

add("تشفير قيصر", r'''
def caesar(text, shift):
    result = ""
    for ch in text:
        if ch.isalpha() and ch.isascii():
            base = ord("A") if ch.isupper() else ord("a")
            result += chr((ord(ch) - base + shift) % 26 + base)
        else:
            result += ch
    return result


text = input("النص (انجليزي): ")
shift = int(input("مقدار الازاحة: "))
enc = caesar(text, shift)
print("المشفر:", enc)
print("بعد فك التشفير:", caesar(enc, -shift))
''', ["Hello World", "3"])

add("شفرة مورس", r'''
MORSE = {
    "A": ".-", "B": "-...", "C": "-.-.", "D": "-..", "E": ".",
    "F": "..-.", "G": "--.", "H": "....", "I": "..", "J": ".---",
    "K": "-.-", "L": ".-..", "M": "--", "N": "-.", "O": "---",
    "P": ".--.", "Q": "--.-", "R": ".-.", "S": "...", "T": "-",
    "U": "..-", "V": "...-", "W": ".--", "X": "-..-", "Y": "-.--",
    "Z": "--..", "0": "-----", "1": ".----", "2": "..---",
    "3": "...--", "4": "....-", "5": ".....", "6": "-....",
    "7": "--...", "8": "---..", "9": "----.",
}

text = input("اكتب كلمة بالانجليزية: ").upper()
out = []
for ch in text:
    if ch == " ":
        out.append("/")
    elif ch in MORSE:
        out.append(MORSE[ch])
print(" ".join(out))
''', ["SOS 2024"])

add("قائمة مهام (To-Do)", r'''
tasks = []

while True:
    print()
    print("1 اضافة   2 عرض   3 انجاز   4 حذف   0 خروج")
    choice = input("اختر: ").strip()
    if choice == "1":
        title = input("المهمة: ")
        tasks.append({"title": title, "done": False})
        print("تمت الاضافة")
    elif choice == "2":
        if not tasks:
            print("لا توجد مهام")
        for i, t in enumerate(tasks, 1):
            mark = "[x]" if t["done"] else "[ ]"
            print(i, mark, t["title"])
    elif choice == "3":
        i = int(input("رقم المهمة: ")) - 1
        if 0 <= i < len(tasks):
            tasks[i]["done"] = True
            print("احسنت!")
        else:
            print("رقم غير موجود")
    elif choice == "4":
        i = int(input("رقم المهمة: ")) - 1
        if 0 <= i < len(tasks):
            print("تم حذف:", tasks.pop(i)["title"])
        else:
            print("رقم غير موجود")
    elif choice == "0":
        break
''', ["1", "مذاكرة بايثون", "1", "شراء خبز", "3", "1", "2", "4", "2", "2", "0"])

add("دفتر العناوين", r'''
contacts = {}

while True:
    print()
    print("1 اضافة   2 بحث   3 عرض الكل   0 خروج")
    choice = input("اختر: ").strip()
    if choice == "1":
        name = input("الاسم: ")
        phone = input("الهاتف: ")
        contacts[name] = phone
        print("تم الحفظ")
    elif choice == "2":
        name = input("اسم البحث: ")
        found = {k: v for k, v in contacts.items() if name in k}
        if found:
            for k, v in found.items():
                print(k, "->", v)
        else:
            print("غير موجود")
    elif choice == "3":
        for k, v in sorted(contacts.items()):
            print(k, "->", v)
        print("الاجمالي:", len(contacts))
    elif choice == "0":
        break
''', ["1", "علي", "0100", "1", "سارة", "0111", "2", "سا", "3", "0"])

add("الفرق بين تاريخين", r'''
from datetime import date

d1 = input("التاريخ الاول (YYYY-MM-DD): ")
d2 = input("التاريخ الثاني (YYYY-MM-DD): ")
a = date.fromisoformat(d1)
b = date.fromisoformat(d2)
diff = abs((b - a).days)
print("الفرق بالايام:", diff)
print("بالاسابيع:", diff // 7, "اسبوع و", diff % 7, "يوم")
print("تقريبا بالاشهر:", round(diff / 30.44, 1))
''', ["2024-01-01", "2024-12-25"])

add("الفائدة المركبة والقروض", r'''
principal = float(input("المبلغ الاساسي: "))
rate = float(input("نسبة الفائدة السنوية %: "))
years = int(input("عدد السنوات: "))

amount = principal
for year in range(1, years + 1):
    amount *= 1 + rate / 100
    print(f"نهاية السنة {year}: {amount:,.2f}")

print(f"الربح الكلي: {amount - principal:,.2f}")
''', ["10000", "8", "5"])

add("عدّاد الكلمات العربية", r'''
text = input("اكتب نصا عربيا: ")
words = text.split()
letters = [c for c in text if "ء" <= c <= "ي"]
print("عدد الكلمات:", len(words))
print("عدد الحروف العربية:", len(letters))
print("النص معكوسا:", text[::-1])
print("الكلمات معكوسة الترتيب:", " ".join(reversed(words)))
''', ["السلام عليكم ورحمة الله"])

add("إزالة التشكيل وتحويل الأرقام", r'''
import re

text = input("اكتب نصا بتشكيل: ")
clean = re.sub(r"[ً-ْٰ]", "", text)
print("بدون تشكيل:", clean)

indian = "٠١٢٣٤٥٦٧٨٩"
western = "0123456789"
table_to_west = str.maketrans(indian, western)
table_to_ind = str.maketrans(western, indian)
num = input("اكتب رقما (عربي او انجليزي): ")
print("بالانجليزي:", num.translate(table_to_west))
print("بالعربي:", num.translate(table_to_ind))
''', ["مَرْحَبًا بِكُمْ", "٢٠٢٤"])
