"""محرر بايثون للموبايل (Flet 1.x + flet-code-editor).

المحرر نفسه مكتبة حقيقية (CodeEditor): تلوين، ارقام اسطر، مؤشر طبيعي.
زر التشغيل يفتح شاشة منفصلة للنتيجة او الخطأ.
"""
import asyncio
import json
import os
import sys
import threading

import flet as ft
import flet_code_editor as fce

import core

AR = core.AR
MONO = "monospace"

BASE = (os.environ.get("FLET_APP_STORAGE_DATA") or os.environ.get("FLET_APP_STORAGE_TEMP")
        or os.path.join(os.path.expanduser("~"), ".pyeditor"))
SITE = os.path.join(BASE, "site-packages")
if os.path.isdir(SITE) and SITE not in sys.path:
    sys.path.append(SITE)

DEFAULT_CODE = '''# اكتب كود بايثون هنا ثم اضغط زر التشغيل
name = input("ادخل اسمك: ")
print("اهلا", name)
print("Hello", name)
'''

SYMBOLS = ["TAB", "(", ")", "[", "]", "{", "}", '"', "'", ":", "=", "+", "-", "*", "/", "%",
           "#", ",", ".", "_", "<", ">", "!", "&", "|", "\\", "@", "$", ";", "?", "~", "^"]


def ic(name):
    return getattr(ft.Icons, name, ft.Icons.CIRCLE)


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def pick_theme(dark):
    """ثيم مخصص (خلفية سوداء + الوان صريحة لكل شيء). لو فشل نرجع للثيم الجاهز."""
    import re as _re
    if dark:
        col = dict(keyword="#FF7B72", built_in="#79C0FF", title="#D2A8FF", function="#D2A8FF",
                   string="#A5D6FF", number="#FFA657", literal="#FFA657", comment="#8B949E",
                   type="#79C0FF", params="#E6E6E6", meta="#FF7B72", symbol="#A5D6FF",
                   name="#E6E6E6", variable="#E6E6E6", attr="#79C0FF", attribute="#79C0FF",
                   subst="#E6E6E6", class_name="#FFA657", section="#D2A8FF")
        fg, bg = "#E6E6E6", "#000000"
    else:
        col = dict(keyword="#CF222E", built_in="#0550AE", title="#8250DF", function="#8250DF",
                   string="#0A3069", number="#953800", literal="#953800", comment="#6E7781",
                   type="#0550AE", params="#1A1A1A", meta="#CF222E", symbol="#0A3069",
                   name="#1A1A1A", variable="#1A1A1A", attr="#0550AE", attribute="#0550AE",
                   subst="#1A1A1A", class_name="#953800", section="#8250DF")
        fg, bg = "#1A1A1A", "#FFFFFF"
    kw = {k: ft.TextStyle(color=v) for k, v in col.items()}
    kw["root"] = ft.TextStyle(color=fg, bgcolor=bg)
    for _ in range(len(kw) + 1):
        try:
            return fce.CustomCodeTheme(**kw)
        except TypeError as ex:
            m = _re.search(r"argument '(\w+)'", str(ex))
            if m and m.group(1) in kw:
                kw.pop(m.group(1))
                continue
            break
        except Exception:
            break
    for n in (("ATOM_ONE_DARK", "MONOKAI", "DRACULA") if dark else ("ATOM_ONE_LIGHT", "GITHUB")):
        t = getattr(fce.CodeTheme, n, None)
        if t is not None:
            return t
    return fce.CodeTheme.ATOM_ONE_LIGHT


def palette(dark):
    if dark:
        return dict(bg="#000000", fg="#E6E6E6", bar="#111111", gutter="#8A8A8A",
                    panel="#0C0C0C", err="#FF6B6B", ok="#7EE787", hint="#E3B341",
                    line="#2A2A2A", tab="#161616", tabsel="#2A2A2A", sym="#1E1E1E")
    return dict(bg="#FFFFFF", fg="#1A1A1A", bar="#EEEEEE", gutter="#6A6A6A",
                panel="#F5F5F5", err="#C62828", ok="#2E7D32", hint="#B26A00",
                line="#D0D0D0", tab="#E6E6E6", tabsel="#FFFFFF", sym="#E2E2E2")


async def main(page: ft.Page):
    page.title = "محرر بايثون"
    page.padding = 0
    page.spacing = 0

    prefs = ft.SharedPreferences()

    S = {
        "dark": True, "fs": 16.0, "ac": True, "autofile": True,
        "tabs": [], "active": 0,
        "last": "", "sel": None, "cursor": 0,
        "savev": 0,
        "thread": None, "tid": None, "wait": None, "answer": "", "stopped": False,
        "out": [], "pending": [], "flush_scheduled": False, "lock": threading.Lock(),
        "screen": "editor",
    }
    C = palette(True)
    W = {}  # عناصر الواجهة الحالية

    # ------------------------------------------------------------ التخزين
    try:
        raw = await prefs.get("state")
        data = json.loads(raw) if raw else {}
    except Exception:
        data = {}
    for k in ("dark", "fs", "ac", "autofile"):
        if k in data:
            S[k] = data[k]
    S["fs"] = float(S["fs"])
    if data.get("tabs"):
        S["tabs"] = data["tabs"]
        S["active"] = clamp(int(data.get("active", 0)), 0, len(S["tabs"]) - 1)
    else:
        S["tabs"] = [{"name": "new", "path": "", "code": DEFAULT_CODE, "saved": ""}]
        S["active"] = 0
    C.update(palette(S["dark"]))

    def files_dir():
        d = os.path.join(BASE, "files")
        os.makedirs(d, exist_ok=True)
        return d

    def cur():
        if not S["tabs"]:
            S["tabs"].append({"name": "new", "path": "", "code": "", "saved": ""})
        S["active"] = clamp(S["active"], 0, len(S["tabs"]) - 1)
        return S["tabs"][S["active"]]

    async def persist():
        t = cur()
        if S["autofile"] and t.get("path"):
            try:
                with open(t["path"], "w", encoding="utf-8") as f:
                    f.write(t["code"])
                t["saved"] = t["code"]
            except Exception:
                pass
        try:
            await prefs.set("state", json.dumps({
                "dark": S["dark"], "fs": S["fs"], "ac": S["ac"], "autofile": S["autofile"],
                "tabs": S["tabs"], "active": S["active"]}, ensure_ascii=False))
        except Exception:
            pass

    def schedule_save(now=False):
        if now:
            page.run_task(persist)
            return
        S["savev"] += 1
        v = S["savev"]

        async def later():
            await asyncio.sleep(0.8)
            if v == S["savev"]:
                await persist()

        page.run_task(later)

    def notify(msg):
        try:
            page.show_dialog(ft.SnackBar(ft.Text(msg)))
        except Exception:
            pass

    # --------------------------------------------------------- المحرر
    def gutter_width():
        digits = max(2, len(str(max(1, (cur()["code"] or "").count("\n") + 1))))
        return float(14 + digits * (max(10.0, S["fs"] - 3) * 0.62 + 2))

    def base_words():
        import keyword
        return list(keyword.kwlist) + list(core.BUILTIN_EXPLAIN.keys())

    def words_now():
        try:
            mine = core.defined_names(W["editor"].value or "")
        except Exception:
            mine = []
        return sorted(set(base_words()) | set(mine))

    def gutter():
        return fce.GutterStyle(
            text_style=ft.TextStyle(font_family=MONO, size=max(10.0, S["fs"] - 3),
                                    color=C["gutter"]),
            show_line_numbers=True, show_folding_handles=False, width=gutter_width())

    def make_editor():
        kw = dict(
            language=fce.CodeLanguage.PYTHON,
            code_theme=pick_theme(S["dark"]),
            value=cur()["code"],
            expand=True,
            text_style=ft.TextStyle(font_family=MONO, size=S["fs"]),
            on_change=on_change,
            on_selection_change=on_sel,
            autocomplete=True,
            autocomplete_words=sorted(set(base_words()) | set(core.defined_names(cur()["code"]))),
            wrap=True,
        )
        try:
            kw["gutter_style"] = gutter()
        except Exception:
            pass
        import re as _re
        for _ in range(len(kw) + 1):
            try:
                return fce.CodeEditor(**kw)
            except TypeError as ex:
                m = _re.search(r"argument '(\w+)'", str(ex))
                if m and m.group(1) in kw and m.group(1) not in ("language", "value"):
                    kw.pop(m.group(1))
                    continue
                raise

    def set_caret(pos):
        S["sel"] = (pos, pos)
        S["cursor"] = pos
        try:
            W["editor"].selection = ft.TextSelection(base_offset=pos, extent_offset=pos)
        except Exception:
            pass

    def set_text(text, pos=None):
        W["editor"].value = text
        S["last"] = text
        cur()["code"] = text
        if pos is not None:
            set_caret(pos)

    def on_change(e):
        new = W["editor"].value or ""
        old = S["last"]
        if new == old:
            return
        res = core.auto_newline(old, new)
        if res is None and S["ac"]:
            res = core.auto_edit(old, new, S["cursor"])
        if res:
            if True:
                new, pos = res
                W["editor"].value = new
                set_caret(pos)
        S["last"] = new
        t = cur()
        t["code"] = new
        render_tabs()
        schedule_save(now=(new.count("\n") != old.count("\n")))
        S["wv"] = S.get("wv", 0) + 1
        wv = S["wv"]

        async def refresh_words():
            await asyncio.sleep(1.2)
            if wv != S["wv"]:
                return
            try:
                ed = W["editor"]
                ed.autocomplete_words = words_now()
                ed.gutter_style = gutter()
                page.update()
            except Exception:
                pass

        page.run_task(refresh_words)

    def on_sel(e):
        try:
            sel = e.selection
            a = getattr(sel, "base_offset", None)
            b = getattr(sel, "extent_offset", None)
            if a is None:
                a = getattr(sel, "start", None)
                b = getattr(sel, "end", None)
            if a is not None and b is not None:
                S["sel"] = (int(a), int(b))
                S["cursor"] = int(b)
        except Exception:
            pass

    def on_sym(sym):
        text = W["editor"].value or ""
        a, b = S["sel"] if S["sel"] else (len(text), len(text))
        a, b = clamp(a, 0, len(text)), clamp(b, 0, len(text))
        new, pos = core.insert_symbol(text, min(a, b), max(a, b), sym)
        set_text(new, pos)
        schedule_save()
        page.update()

    # -------------------------------------------------------- التبويبات
    def tab_title(t):
        dirty = bool(t.get("path")) and t["code"] != t.get("saved")
        return t["name"] + (" •" if dirty else "")

    def render_tabs():
        row = W.get("tabs")
        if row is None:
            return
        items = []
        for i, t in enumerate(S["tabs"]):
            sel = i == S["active"]
            items.append(ft.Container(
                content=ft.Row([
                    ft.Text(tab_title(t), size=13, color=C["fg"]),
                    ft.Container(content=ft.Icon(ic("CLOSE"), size=14, color=C["gutter"]),
                                 padding=ft.Padding.all(4),
                                 on_click=lambda e, i=i: close_tab(i)),
                ], spacing=2, tight=True),
                bgcolor=C["tabsel"] if sel else C["tab"],
                padding=ft.Padding.symmetric(vertical=4, horizontal=10),
                border_radius=ft.BorderRadius.all(8),
                on_click=lambda e, i=i: switch_tab(i)))
        items.append(ft.Container(content=ft.Icon(ic("ADD"), size=20, color=C["fg"]),
                                  padding=ft.Padding.all(6), on_click=lambda e: new_tab()))
        row.controls = items

    def switch_tab(i):
        if i == S["active"] or not (0 <= i < len(S["tabs"])):
            return
        cur()["code"] = W["editor"].value or ""
        S["active"] = i
        set_text(cur()["code"], 0)
        render_tabs()
        schedule_save(now=True)
        page.update()

    def new_tab(name=None, code="", path=""):
        cur()["code"] = W["editor"].value or ""
        names = [t["name"] for t in S["tabs"]]
        name = name or core.unique_name(names, "new")
        if name in names and not path:
            name = core.unique_name(names, name)
        S["tabs"].append({"name": name, "path": path, "code": code, "saved": code if path else ""})
        S["active"] = len(S["tabs"]) - 1
        set_text(code, 0)
        render_tabs()
        schedule_save(now=True)
        page.update()

    def really_close(i):
        S["tabs"].pop(i)
        if not S["tabs"]:
            S["tabs"].append({"name": "new", "path": "", "code": "", "saved": ""})
            S["active"] = 0
        elif i < S["active"]:
            S["active"] -= 1
        elif i == S["active"]:
            S["active"] = min(i, len(S["tabs"]) - 1)
        set_text(cur()["code"], 0)
        render_tabs()
        schedule_save(now=True)
        page.update()

    def close_tab(i):
        if i == S["active"]:
            cur()["code"] = W["editor"].value or ""
        t = S["tabs"][i]
        unsaved = t["code"].strip() != "" and (not t.get("path") or t["code"] != t.get("saved"))
        if not unsaved:
            really_close(i)
            return

        def yes(e):
            page.pop_dialog()
            really_close(i)

        dlg = ft.AlertDialog(
            title=ft.Text("اغلاق التبويب؟"),
            content=ft.Text(f"الملف «{t['name']}» لم يُحفظ في ملف. سيُفقد محتواه عند الاغلاق."),
            actions=[ft.TextButton(content="الغاء", on_click=lambda e: page.pop_dialog()),
                     ft.TextButton(content="اغلاق بدون حفظ", on_click=yes)])
        page.show_dialog(dlg)

    # ------------------------------------------------------------ الملفات
    file_picker = ft.FilePicker()

    def save_current(e=None):
        t = cur()
        t["code"] = W["editor"].value or ""
        if not t.get("path"):
            save_as()
            return
        try:
            with open(t["path"], "w", encoding="utf-8") as f:
                f.write(t["code"])
            t["saved"] = t["code"]
            render_tabs()
            schedule_save(now=True)
            notify("تم الحفظ: " + os.path.basename(t["path"]))
            page.update()
        except Exception as ex:
            notify("تعذر الحفظ: " + str(ex))

    def save_as(e=None):
        t = cur()
        t["code"] = W["editor"].value or ""
        field = ft.TextField(value=core.safe_filename(t["name"]), autofocus=True, dense=True)

        def do_save(ev):
            fname = core.safe_filename(field.value or "new")
            path = os.path.join(files_dir(), fname)
            if os.path.exists(path) and path != t.get("path"):
                stem, ext = os.path.splitext(fname)
                k = 2
                while os.path.exists(os.path.join(files_dir(), f"{stem}_{k}{ext}")):
                    k += 1
                fname = f"{stem}_{k}{ext}"
                path = os.path.join(files_dir(), fname)
            try:
                with open(path, "w", encoding="utf-8") as f:
                    f.write(t["code"])
                t["path"], t["name"], t["saved"] = path, fname, t["code"]
                page.pop_dialog()
                render_tabs()
                schedule_save(now=True)
                notify("تم الحفظ باسم " + fname)
                page.update()
            except Exception as ex:
                notify("تعذر الحفظ: " + str(ex))

        field.on_submit = do_save
        page.show_dialog(ft.AlertDialog(
            title=ft.Text("حفظ الملف"),
            content=ft.Column([ft.Text("اسم الملف:"), field], tight=True),
            actions=[ft.TextButton(content="الغاء", on_click=lambda ev: page.pop_dialog()),
                     ft.TextButton(content="حفظ", on_click=do_save)]))

    def open_path(path):
        for i, t in enumerate(S["tabs"]):
            if t.get("path") == path:
                switch_tab(i)
                return
        try:
            with open(path, "r", encoding="utf-8") as fh:
                code = fh.read()
        except Exception as ex:
            notify("تعذر فتح الملف: " + str(ex))
            return
        new_tab(name=os.path.basename(path), code=code, path=path)

    async def open_picker(e=None):
        try:
            files = await file_picker.pick_files(allow_multiple=False)
        except Exception as ex:
            notify("تعذر فتح الملف: " + str(ex))
            return
        if not files:
            return
        f = files[0]
        code = None
        if getattr(f, "path", None):
            try:
                with open(f.path, "r", encoding="utf-8") as fh:
                    code = fh.read()
            except Exception:
                code = None
        if code is None and getattr(f, "bytes", None):
            code = bytes(f.bytes).decode("utf-8", "replace")
        if code is None:
            notify("تعذر قراءة الملف")
            return
        new_tab(name=f.name, code=code, path=getattr(f, "path", "") or "")

    # --------------------------------------------------- شاشة النتيجة
    def out_row(text, kind):
        rtl = bool(AR.search(text))
        color = {"err": C["err"], "ok": C["ok"], "hint": C["hint"],
                 "dim": C["gutter"]}.get(kind, C["fg"])
        return ft.Row([ft.Text(text, selectable=True, color=color, size=S["fs"],
                               font_family=MONO, expand=True,
                               text_align=ft.TextAlign.RIGHT if rtl else ft.TextAlign.LEFT)])

    def flush_ui():
        with S["lock"]:
            items = S["pending"][:]
            S["pending"].clear()
            S["flush_scheduled"] = False
        out = W.get("out")
        for text, kind in items:
            S["out"].append((text, kind))
            if out is not None:
                out.controls.append(out_row(text, kind))
        if len(S["out"]) > 2000:
            del S["out"][:300]
            if out is not None:
                del out.controls[:300]
        if S["screen"] == "run":
            page.update()

    def post_line(text, kind="out"):
        """آمنة للاستدعاء من اي خيط."""
        with S["lock"]:
            S["pending"].append((text, kind))
            if S["flush_scheduled"]:
                return
            S["flush_scheduled"] = True
        page.loop.call_soon_threadsafe(lambda: page.loop.call_later(0.05, flush_ui))

    def on_loop(fn):
        page.loop.call_soon_threadsafe(fn)

    class Out:
        def __init__(self):
            self.buf = ""

        def write(self, t):
            self.buf += t
            while "\n" in self.buf:
                line, self.buf = self.buf.split("\n", 1)
                post_line(line)
            return len(t)

        def flush(self):
            pass

        def done(self):
            if self.buf:
                post_line(self.buf)
                self.buf = ""

    writer = Out()

    def show_input_row(prompt, ev):
        out = W.get("out")
        if out is None:
            ev.set()
            return
        field = ft.TextField(
            value="", autofocus=True, expand=True, dense=True, text_size=S["fs"],
            border_color=ft.Colors.TRANSPARENT, color=C["ok"],
            text_style=ft.TextStyle(font_family=MONO, size=S["fs"]),
            content_padding=ft.Padding.symmetric(vertical=0, horizontal=4))
        label = ft.Text(prompt, color=C["fg"], size=S["fs"], font_family=MONO)
        marker = ft.Text("\u203a", color=C["hint"], size=S["fs"] + 4, font_family=MONO)
        row = ft.Row([marker, label, field], spacing=4,
                     vertical_alignment=ft.CrossAxisAlignment.CENTER)

        def submit(e):
            S["answer"] = field.value or ""
            try:
                out.controls.remove(row)
            except ValueError:
                pass
            shown = prompt + S["answer"]
            S["out"].append((shown, "out"))
            out.controls.append(out_row(shown, "out"))
            page.update()
            ev.set()

        field.on_submit = submit
        out.controls.append(row)
        page.update()
        try:
            page.run_task(field.focus)
        except Exception:
            pass

    def my_input(prompt=""):
        text = writer.buf + str(prompt)
        writer.buf = ""
        flush_pending_sync()
        ev = threading.Event()
        S["wait"] = ev
        on_loop(lambda: show_input_row(text, ev))
        ev.wait()
        S["wait"] = None
        if S["stopped"]:
            raise KeyboardInterrupt()
        return S["answer"]

    def flush_pending_sync():
        # نتأكد ان كل ما طُبع قبل الادخال ظهر قبل مربع الادخال
        done = threading.Event()

        def go():
            flush_ui()
            done.set()

        on_loop(go)
        done.wait(2)

    def show_error(ex, code):
        info = core.explain_error(ex, code)
        head = f"خطأ ({info['name']})"
        if info["line"]:
            head += f" في السطر {info['line']}"
        post_line(head, "err")
        if info["src"]:
            post_line("   " + info["src"], "dim")
        post_line("السبب: " + info["reason"], "err")
        if info["hint"]:
            post_line("الحل المقترح: " + info["hint"], "hint")

    def set_running(flag):
        btn = W.get("run_btn")
        if btn is not None:
            btn.icon = ic("STOP_CIRCLE") if flag else ic("PLAY_ARROW")
            btn.icon_color = C["err"] if flag else C["ok"]
        W["running"] = flag
        try:
            page.update()
        except Exception:
            pass

    def stop():
        S["stopped"] = True
        ev = S.get("wait")
        if ev:
            ev.set()
        tid = S.get("tid")
        if tid:
            import ctypes
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid),
                                                       ctypes.py_object(KeyboardInterrupt))

    def run_clicked(e=None):
        code = W["editor"].value or "" if "editor" in W else cur()["code"]
        cur()["code"] = code
        schedule_save(now=True)
        build_run_screen()
        try:
            compiled = compile(code, "main.py", "exec")
        except SyntaxError as ex:
            show_error(ex, code)
            flush_ui()
            return
        start_thread(compiled, code)

    def start_thread(compiled, code):
        S["stopped"] = False
        S["out"].clear()
        W["out"].controls.clear()
        try:
            for ln, kind, reason, hint in core.diagnose(code):
                if kind == "warn":
                    post_line(f"تنبيه (السطر {ln}): {reason} {hint}", "hint")
        except Exception:
            pass

        def target():
            S["tid"] = threading.get_ident()
            old = (sys.stdout, sys.stderr)
            sys.stdout = sys.stderr = writer
            try:
                exec(compiled, {"__name__": "__main__", "__file__": "main.py",
                                "input": my_input})
            except SystemExit:
                pass
            except KeyboardInterrupt:
                writer.done()
                post_line("تم ايقاف البرنامج", "err")
            except BaseException as ex:  # noqa: BLE001
                writer.done()
                show_error(ex, code)
            finally:
                writer.done()
                sys.stdout, sys.stderr = old
                on_loop(lambda: (flush_ui(), set_running(False)))

        th = threading.Thread(target=target, daemon=True)
        S["thread"] = th
        set_running(True)
        th.start()

    def run_btn_clicked(e=None):
        th = S["thread"]
        if th and th.is_alive():
            stop()
        else:
            code = cur()["code"]
            try:
                compiled = compile(code, "main.py", "exec")
            except SyntaxError as ex:
                W["out"].controls.clear()
                S["out"].clear()
                show_error(ex, code)
                flush_ui()
                return
            start_thread(compiled, code)

    def restart(e=None):
        async def go():
            if S["thread"] and S["thread"].is_alive():
                stop()
                for _ in range(40):
                    if not S["thread"].is_alive():
                        break
                    await asyncio.sleep(0.1)
            cur_code = cur()["code"]
            W["out"].controls.clear()
            S["out"].clear()
            try:
                compiled = compile(cur_code, "main.py", "exec")
            except SyntaxError as ex:
                show_error(ex, cur_code)
                flush_ui()
                return
            start_thread(compiled, cur_code)

        page.run_task(go)

    def back_to_editor(e=None):
        th = S["thread"]
        if th and th.is_alive():
            stop()
        build_editor_screen()

    def build_run_screen():
        S["screen"] = "run"
        out = ft.ListView(expand=True, auto_scroll=True, spacing=2, padding=ft.Padding.all(10))
        W["out"] = out
        W["run_btn"] = ft.IconButton(icon=ic("STOP_CIRCLE"), icon_color=C["err"], icon_size=30,
                                     on_click=run_btn_clicked, tooltip="ايقاف / اعادة")
        header = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ic("ARROW_BACK"), icon_color=C["fg"], on_click=back_to_editor,
                              tooltip="رجوع للمحرر"),
                ft.Text("النتيجة", size=18, weight=ft.FontWeight.BOLD, color=C["fg"], expand=True),
                ft.IconButton(icon=ic("REPLAY"), icon_color=C["fg"], on_click=restart,
                              tooltip="اعادة التشغيل من جديد"),
                W["run_btn"],
            ], spacing=0),
            bgcolor=C["bar"], padding=ft.Padding.symmetric(vertical=2, horizontal=6))
        body = ft.Column([header, ft.Container(content=out, expand=True, bgcolor=C["panel"])],
                         spacing=0, expand=True)
        show_screen(body)

    # ------------------------------------------------------------ النوافذ
    def dlg_width():
        return min(380, int((page.width or 400) - 40))

    def lv_height(frac=0.6):
        return int((page.height or 700) * frac)

    def dialog(title, content, height=None):
        page.show_dialog(ft.AlertDialog(
            title=ft.Text(title),
            content=ft.Container(content=content, width=dlg_width(), height=height),
            actions=[ft.TextButton(content="اغلاق", on_click=lambda e: page.pop_dialog())]))

    def show_settings(e=None):
        size_label = ft.Text(f"حجم الخط: {int(S['fs'])}")

        def apply_font():
            ed = W["editor"]
            ed.text_style = ft.TextStyle(font_family=MONO, size=S["fs"])
            try:
                ed.gutter_style = gutter()
            except Exception:
                pass

        def set_size(v):
            S["fs"] = clamp(float(v), 10, 32)
            size_label.value = f"حجم الخط: {int(S['fs'])}"
            apply_font()
            schedule_save(now=True)
            page.update()

        slider = ft.Slider(min=10, max=32, divisions=22, value=S["fs"],
                           on_change=lambda ev: set_size(ev.control.value), expand=True)

        def bump(d):
            set_size(S["fs"] + d)
            slider.value = S["fs"]
            page.update()

        def on_theme(ev):
            S["dark"] = bool(ev.control.value)
            C.clear()
            C.update(palette(S["dark"]))
            schedule_save(now=True)
            page.pop_dialog()
            build_editor_screen()

        def on_ac(ev):
            S["ac"] = bool(ev.control.value)
            schedule_save(now=True)

        def on_af(ev):
            S["autofile"] = bool(ev.control.value)
            schedule_save(now=True)

        body = ft.Column([
            size_label,
            ft.Row([ft.IconButton(icon=ic("TEXT_DECREASE"), on_click=lambda ev: bump(-1)),
                    slider,
                    ft.IconButton(icon=ic("TEXT_INCREASE"), on_click=lambda ev: bump(1))]),
            ft.Switch(label="الوضع الداكن (اسود)", value=S["dark"], on_change=on_theme),
            ft.Switch(label="اغلاق الاقواس والتنصيص تلقائيا", value=S["ac"], on_change=on_ac),
            ft.Switch(label="حفظ تلقائي في الملف المفتوح", value=S["autofile"], on_change=on_af),
            ft.TextButton(content="مدير المكتبات",
                          on_click=lambda ev: (page.pop_dialog(), show_libs())),
        ], tight=True, scroll=ft.ScrollMode.AUTO)
        dialog("الاعدادات", body, height=lv_height(0.6))

    def show_examples(e=None):
        import examples_data
        cats = examples_data.categories()
        total = sum(len(v) for v in cats.values())
        search = ft.TextField(hint_text="ابحث عن مثال...", dense=True, text_size=14)
        lv = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        def pick(title, code):
            def h(ev):
                page.pop_dialog()
                new_tab(name=title[:24], code=code)
            return h

        def fill(q=""):
            q = q.strip().lower()
            ctrls = []
            for cat, items in cats.items():
                rows = [(t, c) for t, c in items if not q or q in t.lower() or q in c.lower()]
                if not rows:
                    continue
                ctrls.append(ft.Container(
                    content=ft.Text(f"{cat} ({len(rows)})", weight=ft.FontWeight.BOLD,
                                    color=C["ok"]),
                    padding=ft.Padding.symmetric(vertical=6, horizontal=0)))
                for t, c in rows:
                    ctrls.append(ft.ListTile(title=ft.Text(t, size=14), dense=True,
                                             on_click=pick(t, c)))
            lv.controls = ctrls or [ft.Text("لا توجد نتائج")]

        def on_search(ev):
            fill(search.value or "")
            page.update()

        search.on_change = on_search
        fill()
        dialog(f"امثلة وادوات جاهزة ({total})",
               ft.Column([search, lv], expand=True, spacing=4), height=lv_height(0.72))

    def show_keywords(e=None):
        import keyword
        ctrls = [ft.Text("الكلمات المحجوزة", weight=ft.FontWeight.BOLD, color=C["ok"])]
        for w in keyword.kwlist:
            ctrls.append(ft.ListTile(title=ft.Text(w, font_family=MONO),
                                     subtitle=ft.Text(core.KW_EXPLAIN.get(w, "كلمة محجوزة في بايثون."),
                                                      size=12), dense=True))
        ctrls.append(ft.Text("الدوال المدمجة", weight=ft.FontWeight.BOLD, color=C["ok"]))
        for w, t in core.BUILTIN_EXPLAIN.items():
            ctrls.append(ft.ListTile(title=ft.Text(w + "()", font_family=MONO),
                                     subtitle=ft.Text(t, size=12), dense=True))
        ctrls.append(ft.Text("دوال النصوص والقوائم والقواميس", weight=ft.FontWeight.BOLD,
                             color=C["ok"]))
        for w, t in core.METHOD_EXPLAIN.items():
            ctrls.append(ft.ListTile(title=ft.Text("." + w + "()", font_family=MONO),
                                     subtitle=ft.Text(t, size=12), dense=True))
        dialog("دليل بايثون", ft.Column(ctrls, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True), height=lv_height(0.72))

    def show_modules(e=None):
        rows = [ft.ListTile(title=ft.Text(m, font_family=MONO), subtitle=ft.Text(t, size=12),
                            dense=True) for m, t in sorted(core.MODULES.items())]
        dialog("دليل المكتبات (Modules)", ft.Column(rows, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True), height=lv_height(0.72))

    def show_explain(e=None):
        code = W["editor"].value or ""
        res = core.explain_code(code)
        rows = core.explain_lines(code)
        ctrls = [ft.Text(f"عدد الاسطر: {res['lines']}", size=12, color=C["gutter"])]
        diags = core.diagnose(code)
        ctrls.append(ft.Text("فحص الكود", weight=ft.FontWeight.BOLD, color=C["ok"]))
        if not diags:
            ctrls.append(ft.Text("لم أجد اخطاء كتابة او اسماء غير معرّفة.", size=13,
                                 color=C["ok"]))
        for ln, kind, reason, hint in diags:
            ctrls.append(ft.Container(
                content=ft.Column([
                    ft.Text(f"السطر {ln}: {reason}", size=13,
                            color=C["err"] if kind == "error" else C["hint"]),
                    ft.Text("الحل: " + hint, size=12, color=C["fg"])], spacing=2),
                padding=ft.Padding.symmetric(vertical=5, horizontal=2)))
        ctrls.append(ft.Text("الشرح", weight=ft.FontWeight.BOLD, color=C["ok"]))
        if not rows:
            ctrls.append(ft.Text("لا يوجد كود لشرحه. اكتب كودا وجرّب مرة اخرى."))
        for no, src, text in rows:
            ctrls.append(ft.Container(
                content=ft.Column([
                    ft.Row([ft.Container(content=ft.Text(str(no), size=12, color=C["fg"]),
                                         bgcolor=C["sym"], padding=ft.Padding.symmetric(
                                             vertical=2, horizontal=7),
                                         border_radius=ft.BorderRadius.all(4)),
                            ft.Text(src, size=13, font_family=MONO, color=C["ok"], expand=True,
                                    selectable=True)], spacing=8),
                    ft.Text(text, size=13, color=C["fg"])], spacing=3),
                padding=ft.Padding.symmetric(vertical=7, horizontal=2),
                border=ft.Border(bottom=ft.BorderSide(1, C["line"]))))
        dialog("شرح الكود سطرا بسطر",
               ft.Column(ctrls, spacing=0, scroll=ft.ScrollMode.AUTO, expand=True),
               height=lv_height(0.78))

    def show_files(e=None):
        d = files_dir()
        lv = ft.Column(spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)

        def refresh():
            names = sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n)))
            rows = []
            for n in names:
                p = os.path.join(d, n)
                rows.append(ft.ListTile(
                    title=ft.Text(n, size=14), dense=True,
                    on_click=lambda ev, p=p: (page.pop_dialog(), open_path(p)),
                    trailing=ft.IconButton(icon=ic("DELETE"), icon_size=20,
                                           on_click=lambda ev, p=p: delete(p))))
            lv.controls = rows or [ft.Text("لا توجد ملفات محفوظة بعد")]

        def delete(p):
            try:
                os.remove(p)
                for t in S["tabs"]:
                    if t.get("path") == p:
                        t["path"], t["saved"] = "", ""
            except Exception as ex:
                notify(str(ex))
            refresh()
            render_tabs()
            page.update()

        refresh()
        def pick_device(ev):
            page.pop_dialog()
            page.run_task(open_picker)

        dialog("ملفاتي", ft.Column([
            ft.Button(content="فتح ملف من الجهاز", icon=ic("FOLDER_OPEN"), on_click=pick_device),
            lv], expand=True, spacing=6), height=lv_height(0.6))

    def show_libs(e=None):
        import importlib
        import pkgs
        site = pkgs.site_dir(BASE)
        name_f = ft.TextField(hint_text="اسم المكتبة مثل requests", dense=True, expand=True,
                              text_size=14)
        log_col = ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO, height=130)
        inst_col = ft.Column([], spacing=0)
        busy = {"v": False}
        btn = ft.Button(content="تثبيت")

        def log(msg):
            def go():
                log_col.controls.append(ft.Text(msg, size=12, selectable=True))
                page.update()
            on_loop(go)

        def refresh_installed():
            rows = []
            for n, v in pkgs.list_installed(site):
                rows.append(ft.Row([
                    ft.Text(f"{n}  {v}", expand=True, size=13),
                    ft.IconButton(icon=ic("DELETE"), icon_size=18,
                                  on_click=lambda ev, n=n: remove(n))]))
            inst_col.controls = rows or [ft.Text("لا توجد مكتبات مثبتة", size=12,
                                                 color=C["gutter"])]

        def remove(n):
            pkgs.uninstall(site, n)
            importlib.invalidate_caches()
            refresh_installed()
            page.update()

        def do_install(ev):
            n = (name_f.value or "").strip()
            if not n or busy["v"]:
                return
            busy["v"] = True
            btn.disabled = True
            page.update()

            def work():
                try:
                    ok = pkgs.install(n, site, log)
                    pkgs.activate(site)
                    importlib.invalidate_caches()
                    log(("تم بنجاح. يمكنك الآن: import " + n.replace("-", "_")) if ok
                        else "لم يكتمل التثبيت")
                finally:
                    def fin():
                        busy["v"] = False
                        btn.disabled = False
                        refresh_installed()
                        page.update()
                    on_loop(fin)

            threading.Thread(target=work, daemon=True).start()

        btn.on_click = do_install

        def chip(n):
            def pick(ev):
                name_f.value = n
                page.update()
            return ft.Container(content=ft.Text(n, size=12, font_family=MONO),
                                padding=ft.Padding.symmetric(vertical=6, horizontal=10),
                                border=ft.Border.all(1, C["gutter"]),
                                border_radius=ft.BorderRadius.all(14), on_click=pick)

        refresh_installed()
        body = ft.Column([
            ft.Text("يحمّل المكتبات من الانترنت (PyPI). يعمل مع المكتبات النقية بلغة بايثون فقط، "
                    "اما المكتبات المبنية بلغة C مثل numpy و pandas فلا يمكن تثبيتها هنا.",
                    size=12, color=C["gutter"]),
            ft.Row([name_f, btn]),
            ft.Row([chip(x) for x in ["requests", "colorama", "tabulate", "pyfiglet",
                                      "arabic-reshaper", "python-dateutil", "emoji"]],
                   wrap=True, spacing=6, run_spacing=6),
            ft.Text("السجل:", size=12), log_col,
            ft.Text("المثبتة:", weight=ft.FontWeight.BOLD), inst_col,
        ], scroll=ft.ScrollMode.AUTO, spacing=8)
        dialog("مدير المكتبات", body, height=lv_height(0.75))

    def show_menu(e=None):
        def item(icon, text, fn):
            def h(ev):
                page.pop_dialog()
                res = fn()
                if asyncio.iscoroutine(res):
                    page.run_task(lambda: res)
            return ft.ListTile(leading=ft.Icon(ic(icon)), title=ft.Text(text), dense=True,
                               on_click=h)

        items = [
            item("NOTE_ADD", "ملف جديد", lambda: new_tab()),
            item("FOLDER", "ملفاتي (فتح)", show_files),
            item("SAVE", "حفظ", save_current),
            item("LIGHTBULB", "امثلة وادوات جاهزة", show_examples),
            item("KEY", "دليل بايثون (كلمات ودوال)", show_keywords),
            item("MENU_BOOK", "دليل المكتبات", show_modules),
            item("EXTENSION", "مدير المكتبات", show_libs),
            item("SETTINGS", "الاعدادات والخط", show_settings),
        ]
        page.show_dialog(ft.AlertDialog(
            content=ft.Container(content=ft.Column(items, tight=True, scroll=ft.ScrollMode.AUTO,
                                                   spacing=0),
                                 width=dlg_width()),
            actions=[ft.TextButton(content="اغلاق", on_click=lambda ev: page.pop_dialog())]))

    # ------------------------------------------------------- بناء الشاشات
    def show_screen(ctrl):
        page.controls.clear()
        page.controls.append(ft.SafeArea(content=ctrl, expand=True))
        page.update()

    def sym_button(sym):
        label = "Tab" if sym == "TAB" else sym
        return ft.Container(
            content=ft.Text(label, size=16, font_family=MONO, color=C["fg"]),
            padding=ft.Padding.symmetric(vertical=9, horizontal=14),
            margin=ft.Margin.all(2), bgcolor=C["sym"], border_radius=ft.BorderRadius.all(6),
            on_click=lambda e, s=sym: on_sym(s))

    def build_editor_screen():
        S["screen"] = "editor"
        page.theme_mode = ft.ThemeMode.DARK if S["dark"] else ft.ThemeMode.LIGHT
        page.bgcolor = C["bg"]
        S["last"] = cur()["code"]
        W.pop("out", None)
        W.pop("run_btn", None)

        W["editor"] = make_editor()
        W["tabs"] = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=4)
        render_tabs()

        appbar = ft.Container(
            content=ft.Row([
                ft.IconButton(icon=ic("PLAY_ARROW"), icon_color=C["ok"], icon_size=30,
                              on_click=run_clicked, tooltip="تشغيل"),
                ft.Container(expand=True),
                ft.IconButton(icon=ic("HELP_OUTLINE"), icon_color=C["fg"], on_click=show_explain,
                              tooltip="شرح الكود"),
                ft.IconButton(icon=ic("MORE_VERT"), icon_color=C["fg"], on_click=show_menu),
            ], spacing=0),
            bgcolor=C["bar"], padding=ft.Padding.symmetric(vertical=2, horizontal=6))

        tabs_box = ft.Container(content=W["tabs"], bgcolor=C["bar"],
                                padding=ft.Padding.symmetric(vertical=2, horizontal=6))
        sym_bar = ft.Container(
            content=ft.Row([sym_button(s) for s in SYMBOLS], scroll=ft.ScrollMode.AUTO, spacing=0),
            bgcolor=C["bar"], padding=ft.Padding.symmetric(vertical=2, horizontal=0))

        body = ft.Column([appbar, tabs_box,
                          ft.Container(content=W["editor"], expand=True, bgcolor=C["bg"]),
                          sym_bar], spacing=0, expand=True)
        show_screen(body)

    build_editor_screen()


ft.run(main)
