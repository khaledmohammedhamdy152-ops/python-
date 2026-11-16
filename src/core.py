"""منطق المحرر (بدون واجهة): تلوين، أقواس تلقائية، شرح الأخطاء والكود، أرقام الأسطر."""
import builtins
import keyword
import re

AR = re.compile(r"[؀-ۿݐ-ݿﭐ-﷿ﹰ-﻿]")

PAIRS = {"(": ")", "[": "]", "{": "}", '"': '"', "'": "'"}

# ------------------------------------------------------------------ التلوين
_KW = set(keyword.kwlist)
_SOFT = set(getattr(keyword, "softkwlist", []))
_BUILTINS = {n for n in dir(builtins) if not n.startswith("_")} - _KW

TOKEN_RE = re.compile(
    r"""
    (?P<comment>\#[^\n]*)
  | (?P<string>[rRbBuUfF]{0,2}(?:
        \"\"\"[\s\S]*?(?:\"\"\"|\Z)
      | '''[\s\S]*?(?:'''|\Z)
      | "(?:\\.|[^"\\\n])*(?:"|$)
      | '(?:\\.|[^'\\\n])*(?:'|$)
    ))
  | (?P<decorator>@[^\W\d][\w.]*)
  | (?P<number>\b\d[\d_]*(?:\.\d+)?(?:[eE][+-]?\d+)?\b)
  | (?P<name>[^\W\d]\w*)
    """,
    re.X | re.M,
)

MAX_HIGHLIGHT = 14000  # أكبر حجم نص يتم تلوينه حتى يبقى المحرر سريعا


def tokenize(text):
    """يعيد قائمة (النوع, البداية, النهاية). الأجزاء العادية kind='plain'."""
    out = []
    pos = 0
    prev_kw = ""
    for m in TOKEN_RE.finditer(text):
        s, e = m.span()
        if s > pos:
            out.append(("plain", pos, s))
        kind = m.lastgroup
        if kind == "name":
            word = m.group()
            if word in _KW:
                kind = "keyword"
                prev_kw = word
            elif word in _SOFT and _soft_context(text, e):
                kind = "keyword"
            elif prev_kw in ("def", "class"):
                kind = "defname"
                prev_kw = ""
            elif word in ("self", "cls"):
                kind = "self"
            elif word in _BUILTINS:
                kind = "builtin"
            elif text[e:e + 1] == "(":
                kind = "call"
            else:
                kind = "plain"
            if kind not in ("keyword",):
                prev_kw = ""
        else:
            prev_kw = ""
        out.append((kind, s, e))
        pos = e
    if pos < len(text):
        out.append(("plain", pos, len(text)))
    # دمج الأجزاء العادية المتجاورة
    merged = []
    for k, s, e in out:
        if merged and merged[-1][0] == "plain" and k == "plain":
            merged[-1] = ("plain", merged[-1][1], e)
        else:
            merged.append((k, s, e))
    return merged


def line_tokens(text, prev_state=0):
    """تلوين سطر واحد مع دعم النصوص الثلاثية متعددة الاسطر.

    prev_state: 0 عادي، 1 داخل \"\"\" ، 2 داخل '''.
    يعيد (قائمة (النوع, البداية, النهاية) لغير العادي, الحالة_الجديدة)."""
    spans = []
    start = 0
    if prev_state in (1, 2):
        delim = '"""' if prev_state == 1 else "'''"
        j = text.find(delim)
        if j == -1:
            return ([("string", 0, len(text))] if text else []), prev_state
        start = j + 3
        spans.append(("string", 0, start))
    seg = text[start:]
    state = 0
    for kind, s, e in tokenize(seg):
        if kind == "plain":
            continue
        spans.append((kind, start + s, start + e))
        if kind == "string":
            body = seg[s:e].lstrip("rRbBuUfF")
            for q, st in (('"""', 1), ("'''", 2)):
                if body.startswith(q) and (len(body) < 6 or not body.endswith(q)):
                    state = st
    return spans, state


def _soft_context(text, end):
    # match/case/_/type تُلوَّن فقط لو جاء بعدها شيء يدل على استخدامها ككلمة محجوزة
    nxt = text[end:end + 1]
    return nxt in (" ",) and not text[end:].lstrip(" ").startswith(("=", ".", "(", ","))


# ------------------------------------------------------------ اقواس تلقائية
_OPENER_OF = {")": "(", "]": "[", "}": "{", '"': '"', "'": "'"}


def auto_edit(old, new, cursor=None):
    """لو كانت الحروف المضافة تستدعي تعديلا (اغلاق قوس، مسافة بادئة...) يعيد (نص, مكان_المؤشر).

    cursor: اخر مكان معروف للمؤشر (اختياري) لحسم الالتباس عند تكرار نفس الحرف."""
    if len(new) != len(old) + 1:
        return None
    k = 0
    n = len(old)
    while k < n and old[k] == new[k]:
        k += 1
    if new[k + 1:] != old[k:]:
        return None
    ch = new[k]
    # كل الاماكن الممكنة لإدراج ch (لو تكرر نفس الحرف)
    lo = k
    while lo > 0 and old[lo - 1] == ch:
        lo -= 1
    cands = list(range(lo, k + 1))
    i = cands[-1]
    if len(cands) > 1:
        picked = None
        if cursor is not None:
            if cursor in cands:
                picked = cursor
            elif cursor - 1 in cands:
                picked = cursor - 1
        if picked is None and ch in _OPENER_OF:
            for j in cands:
                b = old[j - 1:j] if j > 0 else ""
                if old[j:j + 1] == ch and b == _OPENER_OF[ch]:
                    picked = j
                    break
        if picked is not None:
            i = picked
    after = old[i:i + 1]
    before = old[i - 1:i] if i > 0 else ""

    if ch in ")]}":
        if after == ch:
            return old, i + 1
        return None

    if ch in "\"'":
        if after == ch:
            return old, i + 1
        if before.isalnum() or before == "_":
            return None
        if i >= 2 and old[i - 2:i] == ch * 2:
            return None
        return new[:i + 1] + ch + new[i + 1:], i + 1

    if ch in "([{":
        if after and (after.isalnum() or after == "_"):
            return None
        return new[:i + 1] + PAIRS[ch] + new[i + 1:], i + 1

    if ch == "\n":
        line_start = old.rfind("\n", 0, i) + 1
        prev_line = old[line_start:i]
        indent = re.match(r"[ \t]*", prev_line).group()
        extra = "    " if prev_line.rstrip().endswith(":") else ""
        ins = indent + extra
        if ins:
            return new[:i + 1] + ins + new[i + 1:], i + 1 + len(ins)
    return None


def insert_symbol(text, s, e, sym):
    """إدراج رمز من شريط الرموز عند المؤشر. يعيد (نص, مكان_المؤشر)."""
    if s > e:
        s, e = e, s
    s = max(0, min(s, len(text)))
    e = max(0, min(e, len(text)))
    if sym == "TAB":
        sym = "    "
    if sym in ("(", "[", "{", '"', "'"):
        close = PAIRS[sym]
        if s == e:
            nxt = text[s:s + 1]
            if sym in "\"'" and nxt == sym:
                return text, s + 1
            return text[:s] + sym + close + text[e:], s + 1
        return text[:s] + sym + text[s:e] + close + text[e:], e + 2
    if sym in (")", "]", "}") and s == e and text[s:s + 1] == sym:
        return text, s + 1
    return text[:s] + sym + text[e:], s + len(sym)


# --------------------------------------------------------- ارقام الاسطر
def wrap_count(line, cpl):
    if len(line) <= cpl:
        return 1
    lines = 1
    cur = 0
    for tok in re.findall(r"\s+|\S+", line):
        n = len(tok)
        if tok.isspace():
            cur += n
            continue
        if cur + n <= cpl:
            cur += n
            continue
        if cur > 0:
            lines += 1
            cur = 0
        while n > cpl:
            lines += 1
            n -= cpl
        cur = n
    return lines


def gutter_text(text, cpl):
    parts = []
    for i, ln in enumerate(text.split("\n"), 1):
        parts.append(str(i))
        parts.extend([""] * (wrap_count(ln, cpl) - 1))
    return "\n".join(parts)


# ------------------------------------------------------------- اسماء الملفات
def unique_name(existing, base="new"):
    names = {n.lower() for n in existing}
    if base.lower() not in names:
        return base
    i = 2
    while f"{base}{i}".lower() in names:
        i += 1
    return f"{base}{i}"


def safe_filename(name):
    name = re.sub(r'[\\/:*?"<>|\n\r\t]+', "_", name.strip())
    name = name.strip(". ") or "new"
    if not name.lower().endswith(".py"):
        name += ".py"
    return name


# ------------------------------------------------------------ شرح الاخطاء
ERRORS_AR = {
    "SyntaxError": "خطأ في كتابة الكود نفسه (قواعد اللغة). غالبا قوس ناقص او نقطتين ':' ناقصة.",
    "IndentationError": "المسافات في بداية السطر غير صحيحة. بعد ':' لازم السطر التالي يكون مزاحا بمسافات ثابتة.",
    "TabError": "خلط بين Tab والمسافات في بداية السطور.",
    "NameError": "استخدمت اسم متغير او دالة غير معرّفة. تأكد من الاملاء ومن انك عرّفته قبل استخدامه.",
    "UnboundLocalError": "استخدمت متغيرا داخل دالة قبل ان تعطيه قيمة.",
    "TypeError": "نوع القيمة غير مناسب للعملية، مثل جمع نص مع رقم. حوّل النوع بـ int() او str().",
    "ValueError": "القيمة نوعها صحيح لكن محتواها غير مناسب، مثل int('abc').",
    "ZeroDivisionError": "لا يمكن القسمة على صفر.",
    "IndexError": "رقم العنصر خارج حدود القائمة. تذكر ان الفهرس يبدأ من 0.",
    "KeyError": "المفتاح غير موجود في القاموس.",
    "AttributeError": "الكائن لا يملك هذه الخاصية او الدالة. تأكد من الاملاء ومن نوع الكائن.",
    "ModuleNotFoundError": "المكتبة غير موجودة او غير مثبتة.",
    "ImportError": "تعذر استيراد المكتبة او الاسم المطلوب منها.",
    "FileNotFoundError": "الملف او المسار غير موجود.",
    "PermissionError": "لا توجد صلاحية للوصول لهذا الملف او المجلد.",
    "RecursionError": "الدالة تستدعي نفسها بلا نهاية. تحتاج شرط توقف.",
    "OverflowError": "الرقم كبير جدا للعملية.",
    "EOFError": "المدخلات انتهت قبل ان يقرأ input().",
    "KeyboardInterrupt": "تم ايقاف البرنامج.",
    "StopIteration": "لا توجد عناصر اخرى في المكرر.",
    "AssertionError": "فشل شرط assert.",
    "UnicodeDecodeError": "تعذر قراءة الملف بهذا الترميز. جرّب encoding='utf-8'.",
    "OSError": "خطأ في نظام التشغيل او الملفات او الشبكة.",
    "MemoryError": "الذاكرة غير كافية.",
}

SYNTAX_HINTS = [
    ("was never closed", "فيه قوس او اقتباس مفتوح ولم يُغلق. تأكد ان كل ( لها ) وكل [ لها ] وكل { لها }."),
    ("unterminated string literal", "نص بدأ بعلامة تنصيص ولم ينتهِ بنفس العلامة في نفس السطر."),
    ("unterminated triple-quoted", "نص متعدد الاسطر بدأ بثلاث علامات تنصيص ولم يُغلق."),
    ("expected ':'", "ناقص النقطتان : في نهاية السطر (بعد if او for او while او def او class)."),
    ("expected an indented block", "بعد السطر الذي ينتهي بـ : لازم السطر التالي يكون مزاحا لليمين (4 مسافات)."),
    ("unexpected indent", "هذا السطر فيه مسافات زائدة في بدايته بدون سبب."),
    ("unindent does not match", "مسافات بداية هذا السطر لا تطابق اي مستوى سابق. وحّد المسافات."),
    ("cannot assign to", "لا يمكن اسناد قيمة لهذا الجزء. غالبا تقصد == للمقارنة بدلا من =."),
    ("Missing parentheses in call to 'print'", "في بايثون 3 لازم الطباعة بأقواس: print(...)"),
    ("invalid decimal literal", "رقم متصل بحروف مثل 2a. افصل بينهما."),
    ("expected 'except' or 'finally'", "كتلة try لازم يليها except او finally."),
    ("invalid syntax. Perhaps you forgot a comma", "غالبا ناقص فاصلة , بين عنصرين."),
    ("invalid syntax", "كتابة غير صحيحة. راجع الاقواس والنقطتين وعلامات = و ==."),
    ("closing parenthesis", "قوس اغلاق لا يطابق قوس الفتح. راجع ترتيب الاقواس."),
]


def explain_error(ex, code=""):
    """يعيد dict: name, line, reason, hint, src."""
    import difflib

    name = type(ex).__name__
    reason = ERRORS_AR.get(name)
    if not reason:
        for base in type(ex).__mro__:
            if base.__name__ in ERRORS_AR:
                reason = ERRORS_AR[base.__name__]
                break
    reason = reason or "حصل خطأ غير متوقع. اقرأ التفاصيل بالاسفل."

    line = None
    if isinstance(ex, SyntaxError):
        line = ex.lineno
        msg = ex.msg or ""
    else:
        msg = str(ex)
        tb = ex.__traceback__
        while tb:
            if tb.tb_frame.f_code.co_filename == "main.py":
                line = tb.tb_lineno
            tb = tb.tb_next

    hint = ""
    low = msg.lower()
    if isinstance(ex, SyntaxError):
        for key, h in SYNTAX_HINTS:
            if key.lower() in low:
                hint = h
                break
    elif isinstance(ex, NameError):
        m = re.search(r"name '(\w+)' is not defined", msg)
        if m:
            bad = m.group(1)
            pool = set(re.findall(r"[^\W\d]\w*", code)) | _BUILTINS | _KW
            pool.discard(bad)
            close = difflib.get_close_matches(bad, sorted(pool), n=2, cutoff=0.7)
            hint = f"الاسم «{bad}» غير معرّف."
            if close:
                hint += " هل تقصد: " + " او ".join(close) + " ؟"
    elif isinstance(ex, TypeError):
        if "concatenate str" in msg:
            hint = "لا يمكن جمع نص مع رقم بعلامة +. حوّل الرقم بـ str() او استخدم f-string."
        elif "can only concatenate" in msg:
            hint = "لا يمكن جمع انواع مختلفة. حوّل القيم لنفس النوع."
        elif "not callable" in msg:
            hint = "تحاول استدعاء شيء كأنه دالة وهو ليس دالة. غالبا مسحت اسم الدالة بمتغير بنفس الاسم."
        elif "positional argument" in msg:
            hint = "عدد القيم الممررة للدالة لا يطابق عدد المعاملات التي عرّفتها."
        elif "not supported between" in msg:
            hint = "لا يمكن المقارنة بين نوعين مختلفين (مثل نص ورقم). حوّل احدهما."
        elif "unsupported operand" in msg:
            hint = "العملية غير مدعومة بين هذين النوعين. تأكد من تحويل الادخال بـ int() او float()."
    elif isinstance(ex, ValueError):
        if "invalid literal for int()" in msg:
            hint = "النص الذي ادخلته ليس رقما صحيحا، فلا يمكن تحويله بـ int()."
        elif "could not convert string to float" in msg:
            hint = "النص ليس رقما عشريا صحيحا."
        elif "unpack" in msg:
            hint = "عدد المتغيرات لا يطابق عدد القيم عند الفك."
    elif isinstance(ex, IndexError):
        hint = "حاولت الوصول لعنصر رقمه اكبر من حجم القائمة، او القائمة فارغة."
    elif isinstance(ex, KeyError):
        hint = f"المفتاح {msg} غير موجود. استخدم .get() لتفادي الخطأ."
    elif isinstance(ex, ModuleNotFoundError):
        m = re.search(r"No module named '([\w.]+)'", msg)
        if m:
            hint = (f"المكتبة {m.group(1)} غير مثبتة. من القائمة افتح «مدير المكتبات» "
                    "لتثبيتها (المكتبات النقية فقط).")
    elif isinstance(ex, FileNotFoundError):
        hint = "تأكد من اسم الملف والمسار. الملفات تُحفظ في مجلد التطبيق."
    elif isinstance(ex, RecursionError):
        hint = "تأكد من وجود حالة توقف (base case) في الدالة."
    elif isinstance(ex, EOFError):
        hint = "البرنامج طلب ادخالا لكن لا يوجد ادخال متاح."

    src = ""
    if line and code:
        lines = code.split("\n")
        if 1 <= line <= len(lines):
            src = lines[line - 1].strip()
    return {"name": name, "line": line, "reason": reason, "hint": hint,
            "detail": msg, "src": src}


# ------------------------------------------------------------ شرح الكود
MODULES = {
    "math": "دوال رياضية: sqrt, sin, cos, pi, floor, ceil, factorial",
    "random": "ارقام واختيارات عشوائية: randint, choice, shuffle, sample",
    "datetime": "التاريخ والوقت: datetime.now(), timedelta, date",
    "time": "الوقت والانتظار: time.sleep(), time.time()",
    "os": "التعامل مع النظام والملفات والمسارات",
    "sys": "معلومات المفسر والنظام: sys.argv, sys.exit()",
    "json": "قراءة وكتابة ملفات JSON: loads, dumps",
    "re": "التعابير النمطية للبحث والاستبدال في النصوص",
    "collections": "هياكل بيانات: Counter, deque, defaultdict, namedtuple",
    "itertools": "ادوات للتكرار: permutations, combinations, product",
    "functools": "ادوات للدوال: lru_cache, partial, reduce",
    "string": "ثوابت وادوات النصوص: ascii_letters, digits, punctuation",
    "statistics": "احصاء: mean, median, stdev, mode",
    "pathlib": "التعامل مع المسارات بشكل كائني",
    "csv": "قراءة وكتابة ملفات CSV",
    "sqlite3": "قاعدة بيانات SQLite داخلية",
    "threading": "تشغيل اكواد بالتوازي (خيوط)",
    "urllib": "طلبات الانترنت البسيطة: urllib.request.urlopen",
    "hashlib": "التشفير والهاش: md5, sha256",
    "base64": "ترميز base64",
    "decimal": "ارقام عشرية دقيقة",
    "fractions": "كسور رياضية",
    "typing": "تلميحات الانواع",
    "dataclasses": "كلاسات بيانات مختصرة",
    "enum": "التعدادات Enum",
    "copy": "نسخ الكائنات: copy, deepcopy",
    "textwrap": "تنسيق وقص النصوص",
    "calendar": "التقويم",
    "uuid": "معرفات فريدة",
    "unittest": "اختبار الاكواد",
    "secrets": "ارقام وكلمات سر عشوائية امنة للتشفير",
    "tempfile": "ملفات ومجلدات مؤقتة",
    "shutil": "نسخ ونقل وحذف الملفات والمجلدات",
    "glob": "البحث عن الملفات بنمط مثل *.py",
    "zipfile": "قراءة وكتابة ملفات zip",
    "argparse": "قراءة معاملات سطر الاوامر",
    "logging": "تسجيل رسائل البرنامج (log)",
    "operator": "دوال تقابل العمليات: add, itemgetter",
    "heapq": "طوابير الاولوية (heap)",
    "bisect": "البحث والادراج في قوائم مرتبة",
    "queue": "طوابير للتعامل مع الخيوط",
    "io": "التعامل مع تدفقات البيانات: StringIO, BytesIO",
    "pprint": "طباعة منسقة للبيانات",
    "html": "ترميز وفك رموز HTML",
    "xml": "قراءة ملفات XML",
    "socket": "اتصالات الشبكة منخفضة المستوى",
    "ssl": "اتصالات امنة",
    "inspect": "فحص الكائنات والدوال",
    "traceback": "طباعة تفاصيل الاخطاء",
    "timeit": "قياس سرعة الاكواد",
    "platform": "معلومات عن النظام",
}

KW_EXPLAIN = {
    "if": "شرط: ينفذ الكود التالي فقط لو كان الشرط صحيحا (True).",
    "elif": "شرط اضافي يُفحص لو لم يتحقق الشرط السابق.",
    "else": "ينفذ لو لم يتحقق اي شرط سابق.",
    "for": "حلقة تكرار: تمر على كل عنصر في قائمة او نص او range.",
    "while": "حلقة تكرار: تكرر الكود طالما الشرط صحيح.",
    "break": "توقف الحلقة فورا وتخرج منها.",
    "continue": "تتخطى باقي الحلقة الحالية وتبدأ الدورة التالية.",
    "pass": "لا تفعل شيئا. تُستخدم كمكان فارغ.",
    "def": "تعريف دالة جديدة يمكنك استدعاؤها بالاسم.",
    "return": "تعيد قيمة من الدالة وتنهي تنفيذها.",
    "class": "تعريف كلاس (قالب لإنشاء كائنات).",
    "lambda": "دالة صغيرة بدون اسم في سطر واحد.",
    "try": "جرّب تنفيذ هذا الكود، ولو حصل خطأ انتقل لـ except.",
    "except": "تلتقط الخطأ الذي حصل داخل try وتتعامل معه.",
    "finally": "ينفذ دائما سواء حصل خطأ ام لا.",
    "raise": "تُطلق خطأ بشكل متعمد.",
    "with": "تفتح مورد (مثل ملف) وتغلقه تلقائيا عند الانتهاء.",
    "import": "تستورد مكتبة جاهزة لاستخدام دوالها.",
    "from": "تستورد اجزاء محددة من مكتبة.",
    "in": "تفحص هل العنصر موجود داخل قائمة او نص، او تُستخدم مع for.",
    "not": "تعكس القيمة المنطقية.",
    "and": "تكون النتيجة صحيحة لو الشرطان صحيحان معا.",
    "or": "تكون النتيجة صحيحة لو احد الشرطين صحيح.",
    "is": "تقارن هل الكائنان هما نفس الكائن (وليس فقط متساويين).",
    "None": "قيمة تعني (لا شيء).",
    "True": "القيمة المنطقية صحيح.",
    "False": "القيمة المنطقية خطأ.",
    "global": "تسمح لك بتعديل متغير عام من داخل دالة.",
    "yield": "تُرجع قيمة وتكمل الدالة لاحقا (مولّد generator).",
    "assert": "تتأكد من صحة شرط وتوقف البرنامج لو كان خطأ.",
    "del": "تحذف متغيرا او عنصرا.",
    "async": "تعريف دالة غير متزامنة.",
    "await": "تنتظر نتيجة عملية غير متزامنة.",
    "as": "تعطي اسما مستعارا (مثل import x as y).",
}

BUILTIN_EXPLAIN = {
    "print": "تطبع القيم على الشاشة (المخرجات).",
    "input": "تطلب من المستخدم كتابة قيمة وتعيدها كنص. لتحويلها لرقم استخدم int() او float().",
    "len": "تعيد عدد عناصر القائمة او عدد حروف النص.",
    "range": "تنشئ سلسلة ارقام للحلقات. range(5) تعطي 0 الى 4.",
    "int": "تحول القيمة الى عدد صحيح.",
    "float": "تحول القيمة الى عدد عشري.",
    "str": "تحول القيمة الى نص.",
    "bool": "تحول القيمة الى صح/خطأ (True/False).",
    "list": "تنشئ قائمة او تحول شيئا الى قائمة.",
    "dict": "تنشئ قاموسا (مفتاح: قيمة).",
    "set": "تنشئ مجموعة عناصر فريدة بدون تكرار.",
    "tuple": "تنشئ صفا ثابتا لا يمكن تعديله.",
    "type": "تعيد نوع القيمة (int, str, list ...).",
    "sum": "تجمع عناصر قائمة ارقام.",
    "min": "تعيد اصغر قيمة.",
    "max": "تعيد اكبر قيمة.",
    "abs": "تعيد القيمة المطلقة (بدون اشارة سالبة).",
    "round": "تقرّب الرقم لعدد معين من الخانات.",
    "sorted": "تعيد قائمة جديدة مرتبة.",
    "reversed": "تعكس ترتيب العناصر.",
    "enumerate": "تعطيك رقم العنصر مع قيمته في الحلقة.",
    "zip": "تجمع عدة قوائم عنصرا بعنصر.",
    "map": "تطبق دالة على كل عناصر قائمة.",
    "filter": "تُبقي فقط العناصر التي تحقق شرطا.",
    "open": "تفتح ملفا للقراءة او الكتابة.",
    "isinstance": "تفحص هل القيمة من نوع معين.",
    "any": "صحيحة لو عنصر واحد على الاقل صحيح.",
    "all": "صحيحة لو كل العناصر صحيحة.",
    "chr": "تحول رقم الى الحرف المقابل له.",
    "ord": "تحول حرفا الى رقمه في جدول الترميز.",
    "bin": "تحول رقما الى نظام ثنائي.",
    "hex": "تحول رقما الى نظام ست عشري.",
    "oct": "تحول رقما الى نظام ثماني.",
    "pow": "ترفع رقما لقوة.",
    "divmod": "تعيد ناتج القسمة والباقي معا.",
    "eval": "تنفذ نصا كتعبير بايثون (استخدمها بحذر).",
    "exec": "تنفذ نصا ككود بايثون (استخدمها بحذر).",
    "format": "تنسق قيمة بشكل معين.",
    "id": "تعيد رقم هوية الكائن في الذاكرة.",
    "iter": "تنشئ مكررا للمرور على العناصر.",
    "next": "تأخذ العنصر التالي من مكرر.",
    "repr": "تعيد تمثيلا نصيا للكائن للمبرمجين.",
    "super": "تستدعي دوال الكلاس الاب.",
    "dir": "تعرض اسماء الدوال والخصائص المتاحة في كائن.",
    "help": "تعرض شرح دالة او كلاس.",
    "callable": "تفحص هل الشيء يمكن استدعاؤه كدالة.",
    "getattr": "تقرأ خاصية من كائن بالاسم.",
    "setattr": "تضبط خاصية في كائن بالاسم.",
    "hasattr": "تفحص هل الكائن له خاصية معينة.",
    "exit": "تنهي البرنامج.",
    "quit": "تنهي البرنامج.",
}

METHOD_EXPLAIN = {
    "append": "تضيف عنصرا في نهاية القائمة.",
    "extend": "تضيف عناصر قائمة اخرى في نهاية القائمة.",
    "insert": "تدرج عنصرا في مكان محدد بالقائمة.",
    "remove": "تحذف اول عنصر بقيمة معينة من القائمة.",
    "pop": "تحذف عنصرا من القائمة وتعيده (الاخير افتراضيا).",
    "sort": "ترتب القائمة نفسها.",
    "reverse": "تعكس ترتيب القائمة نفسها.",
    "index": "تعيد مكان اول ظهور لعنصر.",
    "count": "تعد كم مرة ظهر عنصر.",
    "clear": "تفرغ القائمة او القاموس.",
    "copy": "تعمل نسخة من القائمة او القاموس.",
    "split": "تقسم النص الى قائمة كلمات عند فاصل معين.",
    "join": "تجمع عناصر قائمة في نص واحد بفاصل بينها.",
    "strip": "تحذف المسافات من بداية ونهاية النص.",
    "lstrip": "تحذف المسافات من بداية النص.",
    "rstrip": "تحذف المسافات من نهاية النص.",
    "replace": "تستبدل جزءا من النص بجزء اخر.",
    "upper": "تحول الحروف الانجليزية لكبيرة.",
    "lower": "تحول الحروف الانجليزية لصغيرة.",
    "title": "تجعل اول حرف في كل كلمة كبيرا.",
    "capitalize": "تجعل اول حرف في النص كبيرا.",
    "startswith": "تفحص هل النص يبدأ بجزء معين.",
    "endswith": "تفحص هل النص ينتهي بجزء معين.",
    "find": "تبحث عن جزء في النص وتعيد مكانه (او -1).",
    "isdigit": "تفحص هل النص كله ارقام.",
    "isalpha": "تفحص هل النص كله حروف.",
    "format": "تضع قيما داخل النص في اماكن {}.",
    "keys": "تعيد مفاتيح القاموس.",
    "values": "تعيد قيم القاموس.",
    "items": "تعيد ازواج (مفتاح, قيمة) من القاموس.",
    "get": "تقرأ قيمة من القاموس بدون خطأ لو المفتاح غير موجود.",
    "update": "تحدّث القاموس او المجموعة بعناصر جديدة.",
    "add": "تضيف عنصرا الى مجموعة set.",
    "read": "تقرأ محتوى الملف.",
    "readline": "تقرأ سطرا واحدا من الملف.",
    "readlines": "تقرأ كل اسطر الملف في قائمة.",
    "write": "تكتب نصا في الملف.",
    "close": "تغلق الملف.",
}

NODE_EXPLAIN = {
    "FunctionDef": ("def", KW_EXPLAIN["def"]),
    "AsyncFunctionDef": ("async def", KW_EXPLAIN["def"]),
    "ClassDef": ("class", KW_EXPLAIN["class"]),
    "For": ("for", KW_EXPLAIN["for"]),
    "While": ("while", KW_EXPLAIN["while"]),
    "If": ("if", KW_EXPLAIN["if"]),
    "Try": ("try / except", KW_EXPLAIN["try"]),
    "With": ("with", KW_EXPLAIN["with"]),
    "Return": ("return", KW_EXPLAIN["return"]),
    "Lambda": ("lambda", KW_EXPLAIN["lambda"]),
    "Break": ("break", KW_EXPLAIN["break"]),
    "Continue": ("continue", KW_EXPLAIN["continue"]),
    "Pass": ("pass", KW_EXPLAIN["pass"]),
    "Raise": ("raise", KW_EXPLAIN["raise"]),
    "Assert": ("assert", KW_EXPLAIN["assert"]),
    "Global": ("global", KW_EXPLAIN["global"]),
    "Yield": ("yield", KW_EXPLAIN["yield"]),
    "Delete": ("del", KW_EXPLAIN["del"]),
    "ListComp": ("[x for x in ...]", "List comprehension: طريقة مختصرة لبناء قائمة في سطر واحد."),
    "DictComp": ("{k: v for ...}", "Dict comprehension: بناء قاموس في سطر واحد."),
    "SetComp": ("{x for ...}", "بناء مجموعة في سطر واحد."),
    "GeneratorExp": ("(x for ...)", "مولّد قيم يحسب العناصر عند الحاجة فقط."),
    "JoinedStr": ('f"..."', "f-string: نص يمكنك وضع متغيرات بداخله بين { }."),
    "AugAssign": ("+= -= ...", "تعديل قيمة متغير بعملية، مثل x += 1 تعني x = x + 1."),
    "Assign": ("=", "اسناد: تخزين قيمة في متغير."),
    "Subscript": ("[ ]", "الوصول لعنصر بالرقم او المفتاح، او اخذ جزء بـ [a:b]."),
    "Dict": ("{ : }", "قاموس: مجموعة من ازواج مفتاح/قيمة."),
    "List": ("[ ]", "قائمة: مجموعة عناصر مرتبة قابلة للتعديل."),
    "Tuple": ("( , )", "صف: مجموعة عناصر مرتبة لا تُعدَّل."),
    "Set": ("{ , }", "مجموعة: عناصر فريدة بدون ترتيب."),
    "BoolOp": ("and / or", "دمج شروط: and (الاثنان معا) او or (واحد على الاقل)."),
    "IfExp": ("x if c else y", "شرط في سطر واحد يختار بين قيمتين."),
    "Add": ("+", "الجمع (او دمج النصوص والقوائم)."),
    "Sub": ("-", "الطرح."),
    "Mult": ("*", "الضرب (او تكرار النص او القائمة)."),
    "Div": ("/", "القسمة (الناتج عشري دائما)."),
    "FloorDiv": ("//", "القسمة الصحيحة (بدون كسور)."),
    "Mod": ("%", "باقي القسمة."),
    "Pow": ("**", "القوة (الاس)."),
}


def explain_code(code):
    """يحلل الكود ويعيد dict: items=[(العنوان, الشرح, [الاسطر])], error=SyntaxError|None, lines=عدد."""
    import ast

    found = {}

    def hit(label, text, line):
        if label not in found:
            found[label] = [text, []]
        if line and line not in found[label][1] and len(found[label][1]) < 8:
            found[label][1].append(line)

    err = None
    try:
        tree = ast.parse(code)
    except SyntaxError as ex:
        tree = None
        err = ex

    if tree is not None:
        user_funcs = {n.name for n in ast.walk(tree)
                      if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))}
        user_classes = {n.name for n in ast.walk(tree) if isinstance(n, ast.ClassDef)}
        for node in ast.walk(tree):
            line = getattr(node, "lineno", None)
            t = type(node).__name__
            if isinstance(node, ast.Call):
                f = node.func
                if isinstance(f, ast.Name):
                    if f.id in BUILTIN_EXPLAIN:
                        hit(f.id + "()", BUILTIN_EXPLAIN[f.id], line)
                    elif f.id in user_funcs:
                        hit(f.id + "()", "استدعاء دالة عرّفتها انت في الكود.", line)
                    elif f.id in user_classes:
                        hit(f.id + "()", "انشاء كائن من كلاس عرّفته انت.", line)
                elif isinstance(f, ast.Attribute) and f.attr in METHOD_EXPLAIN:
                    hit("." + f.attr + "()", METHOD_EXPLAIN[f.attr], line)
            elif isinstance(node, ast.Import):
                for a in node.names:
                    base = a.name.split(".")[0]
                    hit("import " + a.name, MODULES.get(base, "استيراد مكتبة."), line)
            elif isinstance(node, ast.ImportFrom):
                base = (node.module or "").split(".")[0]
                hit("from " + (node.module or "") + " import",
                    MODULES.get(base, "استيراد اجزاء من مكتبة."), line)
            elif t in NODE_EXPLAIN:
                label, text = NODE_EXPLAIN[t]
                hit(label, text, line)
                if t in ("If", "For", "While") and node.orelse:
                    if t == "If" and len(node.orelse) == 1 and isinstance(node.orelse[0], ast.If):
                        hit("elif", KW_EXPLAIN["elif"], node.orelse[0].lineno)
                    else:
                        hit("else", KW_EXPLAIN["else"], node.orelse[0].lineno)
                if t == "Try" and node.finalbody:
                    hit("finally", KW_EXPLAIN["finally"], node.finalbody[0].lineno)
            elif isinstance(node, ast.BinOp):
                nm = type(node.op).__name__
                if nm in NODE_EXPLAIN:
                    hit(NODE_EXPLAIN[nm][0], NODE_EXPLAIN[nm][1], line)
            elif isinstance(node, ast.Compare):
                for op in node.ops:
                    if isinstance(op, (ast.In, ast.NotIn)):
                        hit("in", KW_EXPLAIN["in"], line)
            elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.Not):
                hit("not", KW_EXPLAIN["not"], line)
    else:
        # الكود به خطأ كتابة: نشرح الكلمات المعروفة بشكل بسيط
        for i, ln in enumerate(code.split("\n"), 1):
            for w in re.findall(r"[^\W\d]\w*", ln):
                if w in BUILTIN_EXPLAIN:
                    hit(w + "()", BUILTIN_EXPLAIN[w], i)
                elif w in KW_EXPLAIN:
                    hit(w, KW_EXPLAIN[w], i)

    items = sorted(((k, v[0], v[1]) for k, v in found.items()),
                   key=lambda x: (x[2][0] if x[2] else 9999, x[0]))
    return {"items": items, "error": err, "lines": len(code.split("\n"))}
