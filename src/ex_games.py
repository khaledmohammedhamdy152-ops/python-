ITEMS = []


def add(cat, title, code, inputs=()):
    ITEMS.append((cat, title, code.strip("\n") + "\n", tuple(inputs)))


G = "ألعاب"
A = "خوارزميات"

add(G, "لعبة تخمين الرقم", r'''
import random

secret = random.randint(1, 20)
tries = 0
print("فكرت في رقم من 1 الى 20")

while True:
    guess = int(input("خمّن الرقم: "))
    tries += 1
    if guess > secret:
        print("اصغر من كده")
    elif guess < secret:
        print("اكبر من كده")
    else:
        print(f"صح! وصلت للرقم في {tries} محاولات")
        break
''', ["10", "5", "7"])

add(G, "حجر ورقة مقص", r'''
import random

choices = ["حجر", "ورقة", "مقص"]
beats = {"حجر": "مقص", "ورقة": "حجر", "مقص": "ورقة"}
you_score = 0
pc_score = 0

while True:
    you = input("اختر (حجر / ورقة / مقص) او خروج: ").strip()
    if you == "خروج":
        break
    if you not in choices:
        print("اختيار غير صحيح")
        continue
    pc = random.choice(choices)
    print("الكمبيوتر اختار:", pc)
    if you == pc:
        print("تعادل")
    elif beats[you] == pc:
        print("فزت!")
        you_score += 1
    else:
        print("خسرت")
        pc_score += 1
    print(f"النتيجة: انت {you_score} - الكمبيوتر {pc_score}")

print("شكرا للعب")
''', ["حجر", "ورقة", "غلط", "مقص", "خروج"])

add(G, "رمي النرد", r'''
import random

while True:
    cmd = input("اضغط Enter لرمي النرد او اكتب خروج: ")
    if cmd == "خروج":
        break
    a = random.randint(1, 6)
    b = random.randint(1, 6)
    print(f"النردان: {a} و {b}  -> المجموع {a + b}")
    if a == b:
        print("نفس الرقم! حظ سعيد")
''', ["", "", "خروج"])

add(G, "لعبة إكس أو (XO) للاعبين", r'''
board = [" "] * 9
WINS = [(0, 1, 2), (3, 4, 5), (6, 7, 8), (0, 3, 6),
        (1, 4, 7), (2, 5, 8), (0, 4, 8), (2, 4, 6)]


def show():
    print()
    for r in range(3):
        row = board[r * 3:r * 3 + 3]
        print(" " + " | ".join(row))
        if r < 2:
            print("---+---+---")
    print()


def winner():
    for a, b, c in WINS:
        if board[a] != " " and board[a] == board[b] == board[c]:
            return board[a]
    return None


player = "X"
for turn in range(9):
    show()
    while True:
        pos = input(f"دور {player} - اختر مكان من 1 الى 9: ")
        if pos.isdigit() and 1 <= int(pos) <= 9 and board[int(pos) - 1] == " ":
            board[int(pos) - 1] = player
            break
        print("مكان غير صالح")
    w = winner()
    if w:
        show()
        print("الفائز هو", w)
        break
    player = "O" if player == "X" else "X"
else:
    show()
    print("تعادل!")
''', ["1", "4", "2", "5", "3"])

add(G, "لعبة المشنقة", r'''
import random

words = ["python", "arabic", "keyboard", "program", "android"]
word = random.choice(words)
guessed = set()
lives = 6

while lives > 0:
    shown = " ".join(c if c in guessed else "_" for c in word)
    print()
    print(shown, "   | المحاولات المتبقية:", lives)
    if "_" not in shown:
        print("مبروك! الكلمة هي", word)
        break
    letter = input("اكتب حرفا: ").lower().strip()
    if len(letter) != 1 or not letter.isalpha():
        print("اكتب حرفا واحدا فقط")
        continue
    if letter in guessed:
        print("استخدمته من قبل")
        continue
    guessed.add(letter)
    if letter not in word:
        lives -= 1
        print("حرف غير موجود")
else:
    print("خسرت! الكلمة كانت", word)
''', ["p", "z", "y", "t", "h", "o", "n"])

add(G, "اختبار معلومات عامة", r'''
questions = [
    ("ما عاصمة مصر؟", ["القاهرة", "الاسكندرية", "الجيزة"], 1),
    ("كم عدد ايام الاسبوع؟", ["5", "7", "10"], 2),
    ("ما ناتج 8 x 7 ؟", ["54", "56", "64"], 2),
    ("ما اكبر كوكب في المجموعة الشمسية؟", ["المشتري", "زحل", "الارض"], 1),
]

score = 0
for q, options, correct in questions:
    print()
    print(q)
    for i, opt in enumerate(options, 1):
        print(f"  {i}) {opt}")
    ans = input("اجابتك (رقم): ").strip()
    if ans == str(correct):
        print("صحيح!")
        score += 1
    else:
        print("خطأ، الصحيح:", options[correct - 1])

print()
print(f"نتيجتك: {score} من {len(questions)}")
if score == len(questions):
    print("ممتاز!")
elif score >= len(questions) / 2:
    print("جيد")
else:
    print("حاول مرة اخرى")
''', ["1", "2", "2", "1"])

add(G, "تحدي الحساب الذهني", r'''
import random
import time

rounds = 3
score = 0
start = time.time()

for i in range(rounds):
    a = random.randint(1, 10)
    b = random.randint(1, 10)
    op = random.choice(["+", "-", "*"])
    answer = eval(f"{a} {op} {b}")
    user = input(f"السؤال {i + 1}: {a} {op} {b} = ")
    if user.strip().lstrip("-").isdigit() and int(user) == answer:
        print("صح")
        score += 1
    else:
        print("غلط، الاجابة", answer)

elapsed = time.time() - start
print(f"نتيجتك {score}/{rounds} في {elapsed:.1f} ثانية")
''', ["14", "14", "14"])

add(G, "ملء الفراغ (خمّن الحيوان)", r'''
animals = {
    "قط": "حيوان اليف يموء",
    "اسد": "ملك الغابة",
    "فيل": "اكبر حيوان بري وله خرطوم",
}

score = 0
for name, hint in animals.items():
    print()
    print("التلميح:", hint)
    ans = input("ما هو الحيوان؟ ").strip()
    if ans == name:
        print("احسنت!")
        score += 1
    else:
        print("الاجابة:", name)
print()
print("نتيجتك:", score, "/", len(animals))
''', ["قط", "نمر", "فيل"])

add(A, "هل الرقم أولي؟", r'''
def is_prime(n):
    if n < 2:
        return False
    i = 2
    while i * i <= n:
        if n % i == 0:
            return False
        i += 1
    return True


n = int(input("ادخل رقما: "))
if is_prime(n):
    print(n, "رقم اولي")
else:
    print(n, "ليس اوليا")
''', ["97"])

add(A, "المضروب (Factorial)", r'''
def fact(n):
    if n <= 1:
        return 1
    return n * fact(n - 1)


n = int(input("ادخل رقما: "))
print(f"{n}! =", fact(n))
''', ["10"])

add(A, "متتالية فيبوناتشي", r'''
n = int(input("كم رقما تريد؟ "))
a, b = 0, 1
result = []
for _ in range(n):
    result.append(a)
    a, b = b, a + b
print(result)
''', ["10"])

add(A, "القاسم المشترك الأكبر والأصغر مضاعف", r'''
import math

a = int(input("الرقم الاول: "))
b = int(input("الرقم الثاني: "))
g = math.gcd(a, b)
print("ق.م.أ =", g)
print("م.م.أ =", a * b // g)
''', ["12", "18"])

add(A, "الترتيب الفقاعي Bubble Sort", r'''
def bubble_sort(items):
    items = items[:]
    n = len(items)
    for i in range(n):
        swapped = False
        for j in range(n - i - 1):
            if items[j] > items[j + 1]:
                items[j], items[j + 1] = items[j + 1], items[j]
                swapped = True
        if not swapped:
            break
    return items


text = input("ادخل ارقاما مفصولة بمسافة: ")
nums = [int(x) for x in text.split()]
print("قبل:", nums)
print("بعد:", bubble_sort(nums))
''', ["5 2 9 1 7 3"])

add(A, "البحث الثنائي Binary Search", r'''
def binary_search(items, target):
    low, high = 0, len(items) - 1
    while low <= high:
        mid = (low + high) // 2
        if items[mid] == target:
            return mid
        if items[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1


nums = list(range(1, 101, 3))
print(nums)
target = int(input("ابحث عن رقم: "))
pos = binary_search(nums, target)
if pos == -1:
    print("غير موجود")
else:
    print("موجود في المكان", pos)
''', ["40"])

add(A, "هل الكلمة متناظرة (Palindrome)؟", r'''
def is_palindrome(text):
    clean = "".join(c.lower() for c in text if c.isalnum())
    return clean == clean[::-1]


while True:
    t = input("اكتب كلمة او جملة (او خروج): ")
    if t == "خروج":
        break
    if is_palindrome(t):
        print("متناظرة")
    else:
        print("غير متناظرة")
''', ["level", "ارز", "كلمة", "خروج"])

add(A, "غربال الأعداد الأولية", r'''
n = int(input("اوجد الاعداد الاولية حتى: "))
sieve = [True] * (n + 1)
sieve[0:2] = [False, False]
for i in range(2, int(n ** 0.5) + 1):
    if sieve[i]:
        for j in range(i * i, n + 1, i):
            sieve[j] = False
primes = [i for i, ok in enumerate(sieve) if ok]
print(primes)
print("العدد:", len(primes))
''', ["60"])

add(A, "عمليات على المصفوفات", r'''
A = [[1, 2], [3, 4]]
B = [[5, 6], [7, 8]]


def add(x, y):
    return [[x[i][j] + y[i][j] for j in range(2)] for i in range(2)]


def multiply(x, y):
    return [[sum(x[i][k] * y[k][j] for k in range(2)) for j in range(2)]
            for i in range(2)]


def transpose(x):
    return [list(r) for r in zip(*x)]


print("الجمع:", add(A, B))
print("الضرب:", multiply(A, B))
print("المنقولة:", transpose(A))
''')

add(A, "عدّ حروف العلة والعكس", r'''
text = input("اكتب جملة انجليزية: ")
vowels = [c for c in text.lower() if c in "aeiou"]
print("عدد حروف العلة:", len(vowels))
print("النص معكوسا:", text[::-1])
print("الكلمات معكوسة:", " ".join(w[::-1] for w in text.split()))
print("ترتيب الكلمات معكوسا:", " ".join(reversed(text.split())))
''', ["Hello Python World"])

add(A, "الأرقام المثالية والمتماثلة", r'''
limit = int(input("ابحث حتى: "))
print("الاعداد التامة:")
for n in range(2, limit + 1):
    if sum(d for d in range(1, n) if n % d == 0) == n:
        print(" ", n)

print("الاعداد المتناظرة حتى 200:")
print([n for n in range(10, 201) if str(n) == str(n)[::-1]])
''', ["500"])
