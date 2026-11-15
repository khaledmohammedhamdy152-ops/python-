import ctypes
import keyword
import math
import os
import re
import sys
import threading

import flet as ft

AR = re.compile(r"[\u0600-\u06FF\u0750-\u077F\uFB50-\uFDFF\uFE70-\uFEFF]")

DEFAULT_CODE = '''# اكتب كود بايثون هنا ثم اضغط زر التشغيل
name = input("ادخل اسمك: ")
print("اهلا", name)
print("Hello", name)
'''

EXAMPLES = {
    "طباعة عربي وانجليزي": 'print("خالد")\nprint("Khaled")\n',
    "إدخال من المستخدم": 'x = input("ادخل كلمة المرور: ")\nprint("كلمة المرور:", x)\n',
    "جمع رقمين": 'a = int(input("الرقم الاول: "))\nb = int(input("الرقم الثاني: "))\nprint("المجموع =", a + b)\n',
    "حلقة for": 'for i in range(1, 6):\n    print(i)\n',
    "حلقة while": 'n = 3\nwhile n > 0:\n    print(n)\n    n -= 1\nprint("انتهى")\n',
    "شرط if": 'age = int(input("عمرك: "))\nif age >= 18:\n    print("بالغ")\nelse:\n    print("قاصر")\n',
    "دالة": 'def hello(name):\n    return "مرحبا " + name\n\nprint(hello("خالد"))\n',
    "قائمة": 'fruits = ["تفاح", "موز", "برتقال"]\nfor f in fruits:\n    print(f)\nprint(len(fruits))\n',
    "قاموس": 'd = {"الاسم": "خالد", "العمر": 20}\nfor k, v in d.items():\n    print(k, v)\n',
    "كلاس": 'class Person:\n    def __init__(self, name):\n        self.name = name\n\n    def say(self):\n        print("انا", self.name)\n\nPerson("خالد").say()\n',
    "try / except": 'try:\n    x = int(input("رقم: "))\n    print(10 / x)\nexcept ZeroDivisionError:\n    print("لا يمكن القسمة على صفر")\nexcept ValueError:\n    print("ادخل رقم صحيح")\n',
    "عشوائي": 'import random\nprint(random.randint(1, 100))\n',
}

MODULES = {
    "math": "دوال رياضية: sqrt, sin, cos, pi, floor, ceil",
    "random": "أرقام واختيارات عشوائية: randint, choice, shuffle",
    "datetime": "التاريخ والوقت: datetime.now(), timedelta",
    "time": "الوقت والانتظار: time.sleep(), time.time()",
    "os": "التعامل مع النظام والملفات والمسارات",
    "sys": "معلومات المفسر والنظام: sys.argv, sys.exit()",
    "json": "قراءة وكتابة ملفات JSON: loads, dumps",
    "re": "التعابير النمطية للبحث في النصوص",
    "collections": "هياكل بيانات: Counter, deque, defaultdict",
    "itertools": "أدوات للتكرار: permutations, combinations",
    "functools": "أدوات للدوال: lru_cache, partial, reduce",
    "string": "ثوابت وأدوات النصوص: ascii_letters, digits",
    "statistics": "إحصاء: mean, median, stdev",
    "pathlib": "التعامل مع المسارات بشكل كائني",
    "csv": "قراءة وكتابة ملفات CSV",
    "sqlite3": "قاعدة بيانات SQLite داخلية",
    "threading": "تشغيل أكواد بالتوازي (خيوط)",
    "urllib": "طلبات الانترنت البسيطة",
    "hashlib": "التشفير والهاش: md5, sha256",
    "base64": "ترميز base64",
    "decimal": "أرقام عشرية دقيقة",
    "fractions": "كسور رياضية",
    "typing": "تلميحات الأنواع",
    "dataclasses": "كلاسات بيانات مختصرة",
    "enum": "التعدادات Enum",
    "copy": "نسخ الكائنات: copy, deepcopy",
    "textwrap": "تنسيق وقص النصوص",
    "calendar": "التقويم",
    "uuid": "معرفات فريدة",
    "unittest": "اختبار الأكواد",
}

ERRORS_AR = {
    "SyntaxError": "خطأ في كتابة الكود نفسه (قواعد اللغة). غالبا قوس ناقص أو نقطتين ':' ناقصة أو مسافة بادئة غلط.",
    "IndentationError": "المسافات في بداية السطر غير صحيحة. بعد ':' لازم السطر التالي يكون داخل بمسافات ثابتة.",
    "TabError": "خلط بين Tab والمسافات في بداية السطور.",
    "NameError": "استخدمت اسم متغير أو دالة غير معرّفة. اتأكد من الإملاء ومن انك عرّفته قبل استخدامه.",
    "TypeError": "نوع القيمة غير مناسب للعملية، مثل جمع نص مع رقم. حوّل النوع بـ int() او str().",
    "ValueError": "القيمة نوعها صحيح لكن محتواها غير مناسب، مثل int('abc').",
    "ZeroDivisionError": "لا يمكن القسمة على صفر.",
    "IndexError": "رقم العنصر خارج حدود القائمة. تذكر ان الفهرس يبدأ من 0.",
    "KeyError": "المفتاح غير موجود في القاموس.",
    "AttributeError": "الكائن لا يملك هذه الخاصية او الدالة. اتأكد من الإملاء ومن نوع الكائن.",
    "ImportError": "تعذر استيراد المكتبة او الاسم المطلوب منها.",
    "ModuleNotFoundError": "المكتبة غير موجودة او غير مثبتة.",
    "FileNotFoundError": "الملف او المسار غير موجود.",
    "RecursionError": "الدالة تستدعي نفسها بلا نهاية. تحتاج شرط توقف.",
    "OverflowError": "الرقم كبير جدا للعملية.",
    "EOFError": "المدخلات انتهت قبل ان يقرأ input().",
    "KeyboardInterrupt": "تم إيقاف البرنامج.",
}


def main(page: ft.Page):
    page.title = "محرر بايثون"
    page.padding = 0
    page.spacing = 0

    # ---------- التخزين ----------
    def sget(key, default):
        try:
            v = page.client_storage.get(key)
            return default if v is None else v
        except Exception:
            return default

    def sset(key, value):
        try:
            page.client_storage.set(key, value)
        except Exception:
            pass

    S = {
        "dark": bool(sget("dark", True)),
        "fs": float(sget("fs", 16)),
        "code": sget("code", DEFAULT_CODE),
        "path": sget("path", ""),
        "thread": None,
        "tid": None,
        "wait": None,
        "answer": "",
        "out": [],  # (text, kind)
    }

    def palette():
        if S["dark"]:
            return dict(bg="#000000", fg="#E6E6E6", bar="#111111", gutter="#707070",
                        panel="#0C0C0C", err="#FF6B6B", ok="#7EE787", line="#2A2A2A")
        return dict(bg="#FFFFFF", fg="#1A1A1A", bar="#EEEEEE", gutter="#8A8A8A",
                    panel="#F5F5F5", err="#C62828", ok="#2E7D32", line="#D0D0D0")

    P = palette()
    MONO = "monospace"

    # ---------- مكونات ----------
    editor = ft.TextField()
    gutter = ft.Text()
    out_list = ft.ListView(expand=True, auto_scroll=True, spacing=2, padding=10)
    run_btn = ft.IconButton()
    snack_text = ft.Text()

    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def notify(msg):
        page.open(ft.SnackBar(ft.Text(msg)))

    # ---------- أرقام الأسطر ----------
    def visual_lines(text):
        width = (page.width or 400) - 44 - 20
        cpl = max(8, int(width / (S["fs"] * 0.6)))
        counts = []
        for ln in text.split("\n"):
            counts.append(max(1, math.ceil(len(ln) / cpl)))
        return counts

    def refresh_gutter():
        counts = visual_lines(editor.value or "")
        parts = []
        for i, c in enumerate(counts, 1):
            parts.append(str(i))
            parts.extend([""] * (c - 1))
        gutter.value = "\n".join(parts)
        editor.min_lines = max(10, sum(counts) + 2)

    # ---------- الحفظ ----------
    def autosave():
        S["code"] = editor.value or ""
        sset("code", S["code"])

    def on_change(e):
        autosave()
        refresh_gutter()
        gutter.update()
        editor.update()

    def default_save_path():
        base = os.environ.get("FLET_APP_STORAGE_DATA") or os.environ.get("FLET_APP_STORAGE_TEMP") or os.getcwd()
        return os.path.join(base, "main.py")

    def save_file(e=None):
        autosave()
        path = S["path"] or default_save_path()
        try:
            with open(path, "w", encoding="utf-8") as f:
                f.write(editor.value or "")
            S["path"] = path
            sset("path", path)
            notify("تم الحفظ: " + path)
        except Exception as ex:
            notify("تعذر الحفظ: " + str(ex))

    def on_pick(e):
        if not e.files:
            return
        path = e.files[0].path
        try:
            with open(path, "r", encoding="utf-8") as f:
                editor.value = f.read()
            S["path"] = path
            sset("path", path)
            autosave()
            refresh_gutter()
            page.update()
        except Exception as ex:
            notify("تعذر فتح الملف: " + str(ex))

    file_picker.on_result = on_pick

    def open_file(e=None):
        file_picker.pick_files(allow_multiple=False)

    # ---------- المخرجات ----------
    def out_control(text, kind):
        P = palette()
        rtl = bool(AR.search(text))
        color = {"err": P["err"], "ok": P["ok"]}.get(kind, P["fg"])
        return ft.Container(
            content=ft.Text(text, selectable=True, color=color, size=S["fs"],
                            font_family=MONO, text_align=ft.TextAlign.RIGHT if rtl else ft.TextAlign.LEFT),
            alignment=ft.alignment.center_right if rtl else ft.alignment.center_left,
        )

    def add_line(text, kind="out"):
        S["out"].append((text, kind))
        out_list.controls.append(out_control(text, kind))
        page.update()

    def clear_out(e=None):
        S["out"].clear()
        out_list.controls.clear()
        page.update()

    class Out:
        def __init__(self):
            self.buf = ""

        def write(self, t):
            self.buf += t
            while "\n" in self.buf:
                line, self.buf = self.buf.split("\n", 1)
                add_line(line)
            return len(t)

        def flush(self):
            pass

        def done(self):
            if self.buf:
                add_line(self.buf)
                self.buf = ""

    writer = Out()

    # ---------- input ----------
    def my_input(prompt=""):
        text = writer.buf + str(prompt)
        writer.buf = ""
        rtl = bool(AR.search(text))
        P = palette()
        ev = threading.Event()
        S["wait"] = ev
        field = ft.TextField(
            dense=True, autofocus=True, expand=True, color=P["fg"], text_size=S["fs"],
            border_color=P["gutter"], text_align=ft.TextAlign.RIGHT if rtl else ft.TextAlign.LEFT,
        )
        label = ft.Text(text, color=P["fg"], size=S["fs"], font_family=MONO)

        def submit(e):
            S["answer"] = field.value or ""
            ev.set()

        field.on_submit = submit
        send = ft.IconButton(ft.Icons.SEND, on_click=submit, icon_color=P["ok"])
        row = ft.Row(
            ([send, field, label] if rtl else [label, field, send]),
            alignment=ft.MainAxisAlignment.END if rtl else ft.MainAxisAlignment.START,
        )
        out_list.controls.append(row)
        page.update()
        ev.wait()
        S["wait"] = None
        out_list.controls.remove(row)
        shown = text + S["answer"]
        S["out"].append((shown, "out"))
        out_list.controls.append(out_control(shown, "out"))
        page.update()
        if S.get("stopped"):
            raise KeyboardInterrupt()
        return S["answer"]

    # ---------- الأخطاء ----------
    def explain(ex, lineno):
        name = type(ex).__name__
        why = ERRORS_AR.get(name)
        if not why:
            for base in type(ex).__mro__:
                if base.__name__ in ERRORS_AR:
                    why = ERRORS_AR[base.__name__]
                    break
        why = why or "حصل خطأ غير متوقع. اقرأ الرسالة بالأسفل لمعرفة التفاصيل."
        head = f"خطأ ({name})" + (f" في السطر {lineno}" if lineno else "")
        add_line(head, "err")
        add_line("السبب: " + why, "err")
        detail = str(ex)
        if isinstance(ex, SyntaxError) and ex.msg:
            detail = ex.msg
        if detail:
            add_line("التفاصيل: " + detail, "err")

    def runtime_lineno(ex):
        tb = ex.__traceback__
        n = None
        while tb:
            if tb.tb_frame.f_code.co_filename == "main.py":
                n = tb.tb_lineno
            tb = tb.tb_next
        return n

    # ---------- التشغيل ----------
    def set_running(flag):
        P = palette()
        run_btn.icon = ft.Icons.STOP_CIRCLE if flag else ft.Icons.PLAY_ARROW
        run_btn.icon_color = P["err"] if flag else P["ok"]
        run_btn.tooltip = "إيقاف" if flag else "تشغيل"
        page.update()

    def run_clicked(e=None):
        t = S["thread"]
        if t and t.is_alive():
            stop()
            return
        clear_out()
        autosave()
        code = editor.value or ""
        try:
            compiled = compile(code, "main.py", "exec")
        except SyntaxError as ex:
            explain(ex, ex.lineno)
            return
        S["stopped"] = False

        def target():
            S["tid"] = threading.get_ident()
            old = (sys.stdout, sys.stderr)
            sys.stdout = sys.stderr = writer
            try:
                exec(compiled, {"__name__": "__main__", "input": my_input})
            except SystemExit:
                pass
            except KeyboardInterrupt:
                writer.done()
                add_line("تم إيقاف البرنامج", "err")
            except BaseException as ex:
                writer.done()
                explain(ex, runtime_lineno(ex))
            finally:
                writer.done()
                sys.stdout, sys.stderr = old
                set_running(False)

        th = threading.Thread(target=target, daemon=True)
        S["thread"] = th
        set_running(True)
        th.start()

    def stop():
        S["stopped"] = True
        ev = S.get("wait")
        if ev:
            ev.set()
        tid = S.get("tid")
        if tid:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid), ctypes.py_object(KeyboardInterrupt))

    # ---------- النوافذ ----------
    def dialog(title, content, height=None):
        dlg = ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(content=content, width=340, height=height),
            actions=[ft.TextButton("إغلاق", on_click=lambda e: page.close(dlg))],
        )
        page.open(dlg)
        return dlg

    def show_settings(e=None):
        size_label = ft.Text(f"حجم الخط: {int(S['fs'])}")

        def on_size(ev):
            S["fs"] = float(ev.control.value)
            sset("fs", S["fs"])
            size_label.value = f"حجم الخط: {int(S['fs'])}"
            apply_font()
            page.update()

        def on_theme(ev):
            S["dark"] = bool(ev.control.value)
            sset("dark", S["dark"])
            page.close(dlg)
            build()

        body = ft.Column([
            size_label,
            ft.Row([
                ft.IconButton(ft.Icons.TEXT_DECREASE, on_click=lambda ev: bump(-1, size_label)),
                ft.Slider(min=10, max=32, divisions=22, value=S["fs"], on_change=on_size, expand=True),
                ft.IconButton(ft.Icons.TEXT_INCREASE, on_click=lambda ev: bump(1, size_label)),
            ]),
            ft.Switch(label="الوضع الداكن (أسود)", value=S["dark"], on_change=on_theme),
        ], tight=True)
        dlg = dialog("الإعدادات والخط", body)

    def bump(d, label):
        S["fs"] = max(10, min(32, S["fs"] + d))
        sset("fs", S["fs"])
        label.value = f"حجم الخط: {int(S['fs'])}"
        apply_font()
        page.update()

    def show_examples(e=None):
        def pick(name):
            def h(ev):
                editor.value = EXAMPLES[name]
                autosave()
                refresh_gutter()
                page.close(dlg)
                page.update()
            return h

        lv = ft.ListView([ft.ListTile(title=ft.Text(n), on_click=pick(n)) for n in EXAMPLES], height=380)
        dlg = dialog("أمثلة جاهزة", lv)

    def show_keywords(e=None):
        words = list(keyword.kwlist) + [f"{w} (سياقية)" for w in keyword.softkwlist]
        chips = ft.Row([ft.Container(ft.Text(w, font_family=MONO, size=14), padding=8,
                                     border=ft.border.all(1, palette()["gutter"]), border_radius=8)
                        for w in words], wrap=True, spacing=6, run_spacing=6, scroll=ft.ScrollMode.AUTO)
        dialog("الكلمات المحجوزة في بايثون", chips, height=380)

    def show_modules(e=None):
        mods = sorted(MODULES)
        lv = ft.ListView([ft.ListTile(title=ft.Text(m, font_family=MONO), subtitle=ft.Text(MODULES[m]))
                          for m in mods], height=400)
        dialog("دليل المكتبات (Modules)", lv)

    # ---------- بناء الواجهة ----------
    def apply_font():
        style = ft.TextStyle(font_family=MONO, size=S["fs"], height=1.4)
        editor.text_style = style
        gutter.size = S["fs"]
        gutter.style = ft.TextStyle(font_family=MONO, size=S["fs"], height=1.4, color=palette()["gutter"])
        refresh_gutter()
        out_list.controls = [out_control(t, k) for t, k in S["out"]]

    def build():
        nonlocal P
        P = palette()
        page.theme_mode = ft.ThemeMode.DARK if S["dark"] else ft.ThemeMode.LIGHT
        page.bgcolor = P["bg"]

        editor.value = S["code"] if editor.value is None else editor.value
        editor.multiline = True
        editor.max_lines = None
        editor.expand = True
        editor.border = ft.InputBorder.NONE
        editor.content_padding = ft.padding.only(top=0, bottom=0, left=0, right=0)
        editor.color = P["fg"]
        editor.cursor_color = P["ok"]
        editor.keyboard_type = ft.KeyboardType.MULTILINE
        editor.on_change = on_change
        editor.autocorrect = False
        editor.enable_suggestions = False

        run_btn.icon = ft.Icons.PLAY_ARROW
        run_btn.icon_color = P["ok"]
        run_btn.icon_size = 30
        run_btn.tooltip = "تشغيل"
        run_btn.on_click = run_clicked

        menu = ft.PopupMenuButton(
            icon=ft.Icons.MORE_VERT,
            icon_color=P["fg"],
            items=[
                ft.PopupMenuItem(text="الإعدادات والخط", icon=ft.Icons.SETTINGS, on_click=show_settings),
                ft.PopupMenuItem(text="أمثلة جاهزة", icon=ft.Icons.LIGHTBULB, on_click=show_examples),
                ft.PopupMenuItem(text="الكلمات المحجوزة", icon=ft.Icons.KEY, on_click=show_keywords),
                ft.PopupMenuItem(text="دليل المكتبات", icon=ft.Icons.MENU_BOOK, on_click=show_modules),
                ft.PopupMenuItem(text="فتح ملف", icon=ft.Icons.FOLDER_OPEN, on_click=open_file),
                ft.PopupMenuItem(text="حفظ", icon=ft.Icons.SAVE, on_click=save_file),
            ],
        )

        appbar = ft.Container(
            content=ft.Row([
                run_btn,
                ft.Text("محرر بايثون", size=18, weight=ft.FontWeight.BOLD, color=P["fg"]),
                menu,
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=P["bar"], padding=ft.padding.symmetric(horizontal=6, vertical=4),
        )

        apply_font()

        editor_area = ft.Container(
            content=ft.Column(
                [ft.Row([ft.Container(gutter, width=36, alignment=ft.alignment.top_right), editor],
                        vertical_alignment=ft.CrossAxisAlignment.START, spacing=8)],
                scroll=ft.ScrollMode.AUTO,
            ),
            expand=3, padding=ft.padding.only(left=6, right=10, top=8, bottom=4), bgcolor=P["bg"],
        )

        out_header = ft.Container(
            content=ft.Row([
                ft.Text("المخرجات", color=P["fg"], weight=ft.FontWeight.BOLD),
                ft.IconButton(ft.Icons.DELETE_SWEEP, icon_color=P["fg"], on_click=clear_out, tooltip="مسح"),
            ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
            bgcolor=P["bar"], padding=ft.padding.symmetric(horizontal=12),
        )
        out_area = ft.Container(
            content=ft.Column([out_header, out_list], spacing=0, expand=True),
            expand=2, bgcolor=P["panel"], border=ft.border.only(top=ft.BorderSide(1, P["line"])),
        )

        page.controls.clear()
        page.add(ft.SafeArea(ft.Column([appbar, editor_area, out_area], spacing=0, expand=True), expand=True))
        page.update()

    def on_resize(e):
        refresh_gutter()
        page.update()

    page.on_resize = on_resize
    editor.value = S["code"]
    build()


ft.app(target=main)
