import json
import os
import sys
import threading
import time

import flet as ft

import core

AR = core.AR
MONO = "monospace"
HEADER_H = 44

BASE = os.environ.get("FLET_APP_STORAGE_DATA") or os.path.join(os.path.expanduser("~"), ".pyeditor")
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


def setp(obj, **kw):
    for k, v in kw.items():
        try:
            setattr(obj, k, v)
        except Exception:
            pass
    return obj


def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def main(page: ft.Page):
    page.title = "محرر بايثون"
    page.padding = 0
    page.spacing = 0

    # ------------------------------------------------------------ التخزين
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

    def files_dir():
        d = os.path.join(BASE, "files")
        os.makedirs(d, exist_ok=True)
        return d

    S = {
        "dark": bool(sget("dark", True)),
        "fs": float(sget("fs", 16)),
        "hl": bool(sget("hl", True)),
        "ac": bool(sget("ac", True)),
        "autofile": bool(sget("autofile", True)),
        "charw": float(sget("charw", 0.6)),
        "out_h": float(sget("out_h", 220)),
        "prev_h": 220.0,
        "out_show": True,
        "tabs": [],
        "active": 0,
        "last": "",
        "sel": None,
        "cursor": None,
        "timer": None,
        "thread": None,
        "tid": None,
        "wait": None,
        "answer": "",
        "stopped": False,
        "out": [],
        "last_ui": 0.0,
    }

    try:
        raw = sget("tabs", None)
        data = json.loads(raw) if raw else None
    except Exception:
        data = None
    if data and data.get("tabs"):
        S["tabs"] = data["tabs"]
        S["active"] = clamp(int(data.get("active", 0)), 0, len(S["tabs"]) - 1)
    else:
        S["tabs"] = [{"name": "new", "path": "", "code": sget("code", DEFAULT_CODE), "saved": ""}]

    HAS_SEL = hasattr(ft, "TextSelection")

    C = {}

    def palette():
        if S["dark"]:
            return dict(bg="#000000", fg="#E6E6E6", bar="#111111", gutter="#707070",
                        panel="#0C0C0C", err="#FF6B6B", ok="#7EE787", hint="#E3B341",
                        line="#2A2A2A", tab="#161616", tabsel="#2A2A2A", sym="#1E1E1E",
                        keyword="#FF79C6", builtin="#8BE9FD", string="#F1FA8C",
                        number="#BD93F9", comment="#6C7A96", defname="#50FA7B",
                        call="#C8E6C9", self="#FFB86C", decorator="#FFB86C")
        return dict(bg="#FFFFFF", fg="#1A1A1A", bar="#EEEEEE", gutter="#8A8A8A",
                    panel="#F5F5F5", err="#C62828", ok="#2E7D32", hint="#B26A00",
                    line="#D0D0D0", tab="#E6E6E6", tabsel="#FFFFFF", sym="#E2E2E2",
                    keyword="#D73A49", builtin="#005CC5", string="#0B6E2E",
                    number="#6F42C1", comment="#6A737D", defname="#6F42C1",
                    call="#22863A", self="#E36209", decorator="#E36209")

    C.update(palette())

    # ------------------------------------------------------------ المكونات
    editor = ft.TextField()
    hl_text = ft.Text("")
    gutter = ft.Text("")
    out_list = ft.ListView(expand=True, auto_scroll=True, spacing=2, padding=10)
    run_btn = ft.IconButton(ic("PLAY_ARROW"))
    out_panel = ft.Container()
    tabs_row = ft.Row(scroll=ft.ScrollMode.AUTO, spacing=4)
    file_picker = ft.FilePicker()
    page.overlay.append(file_picker)

    def notify(msg):
        try:
            page.open(ft.SnackBar(ft.Text(msg)))
        except Exception:
            pass

    def cur():
        return S["tabs"][S["active"]]

    # ------------------------------------------------- التلوين وارقام الاسطر
    def spans_for(text):
        if not S["hl"] or len(text) > core.MAX_HIGHLIGHT:
            return [ft.TextSpan(text)]
        spans = []
        for kind, s, e in core.tokenize(text):
            seg = text[s:e]
            if kind == "plain":
                spans.append(ft.TextSpan(seg))
            else:
                spans.append(ft.TextSpan(seg, style=ft.TextStyle(color=C[kind])))
        return spans

    def refresh_view(update=True):
        text = editor.value or ""
        hl_text.spans = spans_for(text)
        w = (page.width or 400) - 36 - 8 - 16
        cpl = max(8, int(w / (S["fs"] * S["charw"])))
        gutter.value = core.gutter_text(text, cpl)
        if update:
            try:
                hl_text.update()
                gutter.update()
            except Exception:
                pass

    def apply_font():
        style = ft.TextStyle(font_family=MONO, size=S["fs"], height=1.4)
        setp(editor, text_style=style, text_size=S["fs"])
        setp(hl_text, size=S["fs"], font_family=MONO, style=ft.TextStyle(height=1.4),
             color=C["fg"])
        setp(gutter, size=S["fs"], font_family=MONO, text_align=ft.TextAlign.RIGHT,
             style=ft.TextStyle(height=1.4), color=C["gutter"])
        setp(editor, min_lines=max(8, int(((page.height or 700) * 0.5) / (S["fs"] * 1.4))))
        setp(editor, color=ft.Colors.TRANSPARENT if S["hl"] else C["fg"])
        setp(hl_text, visible=S["hl"])

    # ----------------------------------------------------------- الحفظ
    def persist(_=None):
        try:
            t = cur()
            if S["autofile"] and t.get("path"):
                try:
                    with open(t["path"], "w", encoding="utf-8") as f:
                        f.write(t["code"])
                    t["saved"] = t["code"]
                except Exception:
                    pass
            sset("tabs", json.dumps({"tabs": S["tabs"], "active": S["active"]},
                                    ensure_ascii=False))
        except Exception:
            pass

    def schedule_save(now=False):
        old = S.get("timer")
        if old:
            old.cancel()
        if now:
            persist()
            return
        tm = threading.Timer(0.8, persist)
        tm.daemon = True
        S["timer"] = tm
        tm.start()

    def make_sel(a, b):
        try:
            return ft.TextSelection(base_offset=a, extent_offset=b)
        except TypeError:
            return ft.TextSelection(start=a, end=b)

    def apply_sel(pos):
        S["sel"] = (pos, pos)
        S["cursor"] = pos
        if HAS_SEL:
            try:
                editor.selection = make_sel(pos, pos)
            except Exception:
                pass

    def set_editor_text(text, pos=None, update=True):
        editor.value = text
        S["last"] = text
        cur()["code"] = text
        if pos is not None:
            apply_sel(pos)
        else:
            S["sel"] = None
            S["cursor"] = None
        refresh_view(update=False)
        if update:
            try:
                editor.update()
                hl_text.update()
                gutter.update()
            except Exception:
                pass

    def on_change(e):
        new = editor.value or ""
        old = S["last"]
        if S["ac"] and HAS_SEL:
            res = core.auto_edit(old, new, S["cursor"])
            if res:
                new, pos = res
                editor.value = new
                apply_sel(pos)
                try:
                    editor.update()
                except Exception:
                    pass
        newline_changed = new.count("\n") != old.count("\n")
        S["last"] = new
        cur()["code"] = new
        refresh_view()
        schedule_save(now=newline_changed)

    def on_sel(e):
        try:
            sel = getattr(e, "selection", None)
            if sel is not None:
                a = getattr(sel, "base_offset", None)
                b = getattr(sel, "extent_offset", None)
                if a is None:
                    a = getattr(sel, "start", None)
                    b = getattr(sel, "end", None)
            else:
                a = getattr(e, "start", None)
                b = getattr(e, "end", None)
            if a is not None and b is not None:
                S["sel"] = (int(a), int(b))
                S["cursor"] = int(b)
        except Exception:
            pass

    def on_sym(sym):
        text = editor.value or ""
        a, b = S["sel"] if S["sel"] else (len(text), len(text))
        a, b = clamp(a, 0, len(text)), clamp(b, 0, len(text))
        new, pos = core.insert_symbol(text, min(a, b), max(a, b), sym)
        set_editor_text(new, pos)
        schedule_save()
        try:
            editor.focus()
        except Exception:
            pass

    # ------------------------------------------------------------ التبويبات
    def tab_title(t):
        name = os.path.basename(t["name"]) if t.get("path") else t["name"]
        mark = "•" if t.get("path") and t["code"] != t.get("saved") else ""
        return name + mark

    def render_tabs(update=True):
        items = []
        for i, t in enumerate(S["tabs"]):
            sel = i == S["active"]
            label = ft.Text(tab_title(t), size=13, color=C["fg"])
            close = ft.Container(ft.Icon(ic("CLOSE"), size=14, color=C["gutter"]),
                                 padding=4, on_click=lambda e, i=i: close_tab(i))
            items.append(ft.Container(
                ft.Row([label, close], spacing=2, tight=True),
                bgcolor=C["tabsel"] if sel else C["tab"],
                padding=ft.padding.only(left=10, right=2, top=4, bottom=4),
                border_radius=ft.border_radius.only(top_left=8, top_right=8),
                on_click=lambda e, i=i: switch_tab(i)))
        items.append(ft.Container(ft.Icon(ic("ADD"), size=20, color=C["fg"]),
                                  padding=6, on_click=lambda e: new_tab()))
        tabs_row.controls = items
        if update:
            try:
                tabs_row.update()
            except Exception:
                pass

    def switch_tab(i):
        if i == S["active"] or not (0 <= i < len(S["tabs"])):
            return
        S["active"] = i
        set_editor_text(cur()["code"])
        render_tabs()
        schedule_save(now=True)

    def new_tab(name=None, code="", path=""):
        names = [t["name"] for t in S["tabs"]]
        name = name or core.unique_name(names, "new")
        if name in names and not path:
            name = core.unique_name(names, name)
        S["tabs"].append({"name": name, "path": path, "code": code, "saved": code if path else ""})
        S["active"] = len(S["tabs"]) - 1
        set_editor_text(code)
        render_tabs()
        schedule_save(now=True)
        try:
            editor.focus()
        except Exception:
            pass

    def really_close(i):
        S["tabs"].pop(i)
        if not S["tabs"]:
            S["tabs"].append({"name": "new", "path": "", "code": "", "saved": ""})
        S["active"] = clamp(S["active"] if S["active"] < i else S["active"] - (1 if S["active"] >= i else 0),
                            0, len(S["tabs"]) - 1)
        set_editor_text(cur()["code"])
        render_tabs()
        schedule_save(now=True)

    def close_tab(i):
        t = S["tabs"][i]
        unsaved = (t["code"].strip() != "" and
                   (not t.get("path") or t["code"] != t.get("saved")))
        if not unsaved:
            really_close(i)
            return

        def yes(e):
            page.close(dlg)
            really_close(i)

        def no(e):
            page.close(dlg)

        dlg = ft.AlertDialog(
            title=ft.Text("اغلاق التبويب؟"),
            content=ft.Text(f"الملف «{t['name']}» لم يُحفظ في ملف. سيُفقد محتواه عند الاغلاق."),
            actions=[ft.TextButton("الغاء", on_click=no), ft.TextButton("اغلاق بدون حفظ", on_click=yes)])
        page.open(dlg)

    # ------------------------------------------------------------ الملفات
    def write_file(path, text):
        with open(path, "w", encoding="utf-8") as f:
            f.write(text)

    def save_current(e=None):
        t = cur()
        t["code"] = editor.value or ""
        if t.get("path"):
            try:
                write_file(t["path"], t["code"])
                t["saved"] = t["code"]
                render_tabs()
                schedule_save(now=True)
                notify("تم الحفظ: " + os.path.basename(t["path"]))
            except Exception as ex:
                notify("تعذر الحفظ: " + str(ex))
        else:
            save_as(None)

    def save_as(e=None):
        t = cur()
        default = core.safe_filename(t["name"] if t["name"] != "new" else "new")
        field = ft.TextField(value=default, dense=True, autofocus=True, text_size=15)

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
                t["code"] = editor.value or ""
                write_file(path, t["code"])
                t["path"] = path
                t["name"] = fname
                t["saved"] = t["code"]
                page.close(dlg)
                render_tabs()
                schedule_save(now=True)
                notify("تم الحفظ باسم " + fname)
            except Exception as ex:
                notify("تعذر الحفظ: " + str(ex))

        field.on_submit = do_save
        dlg = ft.AlertDialog(
            title=ft.Text("حفظ الملف"),
            content=ft.Column([ft.Text("اسم الملف:"), field], tight=True),
            actions=[ft.TextButton("الغاء", on_click=lambda ev: page.close(dlg)),
                     ft.TextButton("حفظ", on_click=do_save)])
        page.open(dlg)

    def on_pick(e):
        if not e.files:
            return
        f = e.files[0]
        path = f.path
        try:
            with open(path, "r", encoding="utf-8") as fh:
                code = fh.read()
        except Exception as ex:
            notify("تعذر فتح الملف: " + str(ex))
            return
        new_tab(name=f.name, code=code, path=path)

    file_picker.on_result = on_pick

    def open_picker(e=None):
        file_picker.pick_files(allow_multiple=False)

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

    # ---------------------------------------------------------- المخرجات
    def out_control(text, kind):
        rtl = bool(AR.search(text))
        color = {"err": C["err"], "ok": C["ok"], "hint": C["hint"],
                 "dim": C["gutter"]}.get(kind, C["fg"])
        return ft.Container(
            content=ft.Text(text, selectable=True, color=color, size=S["fs"], font_family=MONO,
                            text_align=ft.TextAlign.RIGHT if rtl else ft.TextAlign.LEFT),
            alignment=ft.alignment.center_right if rtl else ft.alignment.center_left)

    def ui_flush(force=False):
        now = time.time()
        if force or now - S["last_ui"] > 0.05:
            S["last_ui"] = now
            try:
                out_list.update()
            except Exception:
                pass

    def add_line(text, kind="out"):
        S["out"].append((text, kind))
        out_list.controls.append(out_control(text, kind))
        if len(S["out"]) > 1500:
            del S["out"][:200]
            del out_list.controls[:200]
        ui_flush()

    def clear_out(e=None):
        S["out"].clear()
        out_list.controls.clear()
        ui_flush(True)

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
            ui_flush(True)

    writer = Out()

    def max_out_h():
        return max(HEADER_H + 40, (page.height or 700) - 230)

    def set_out_h(h, persist_it=True):
        S["out_h"] = clamp(h, HEADER_H, max_out_h())
        out_panel.height = S["out_h"]
        if persist_it:
            sset("out_h", S["out_h"])

    def apply_out(update=True):
        out_panel.visible = S["out_show"]
        out_panel.height = clamp(S["out_h"], HEADER_H, max_out_h())
        if update:
            try:
                out_panel.update()
            except Exception:
                pass

    def toggle_collapse(e=None):
        if S["out_h"] > HEADER_H + 10:
            S["prev_h"] = S["out_h"]
            set_out_h(HEADER_H)
        else:
            set_out_h(S["prev_h"] or 220)
        apply_out()

    def maximize_out(e=None):
        S["prev_h"] = S["out_h"] if S["out_h"] > HEADER_H + 10 else 220
        set_out_h(max_out_h())
        apply_out()

    def toggle_out(e=None):
        S["out_show"] = not S["out_show"]
        apply_out()

    def ensure_out_visible():
        changed = False
        if not S["out_show"]:
            S["out_show"] = True
            changed = True
        if S["out_h"] < 150:
            set_out_h(180, persist_it=False)
            changed = True
        if changed:
            apply_out()

    def on_drag(e):
        dy = getattr(e, "delta_y", None)
        if dy is None:
            dy = getattr(e, "local_delta_y", 0) or 0
        set_out_h(S["out_h"] - dy, persist_it=False)
        try:
            out_panel.update()
        except Exception:
            pass

    def on_drag_end(e):
        sset("out_h", S["out_h"])

    # ------------------------------------------------------------- input
    def my_input(prompt=""):
        text = writer.buf + str(prompt)
        writer.buf = ""
        rtl = bool(AR.search(text))
        ev = threading.Event()
        S["wait"] = ev
        field = ft.TextField(value="", autofocus=True, expand=True)
        setp(field, border=ft.InputBorder.NONE, dense=True, content_padding=0,
             color=C["fg"], cursor_color=C["ok"], text_size=S["fs"],
             text_style=ft.TextStyle(font_family=MONO, size=S["fs"]),
             text_align=ft.TextAlign.RIGHT if rtl else ft.TextAlign.LEFT)
        label = ft.Text(text, color=C["fg"], size=S["fs"], font_family=MONO)

        def submit(e):
            S["answer"] = field.value or ""
            ev.set()

        field.on_submit = submit
        row = ft.Row([field, label] if rtl else [label, field], spacing=6,
                     vertical_alignment=ft.CrossAxisAlignment.CENTER)
        out_list.controls.append(row)
        ui_flush(True)
        try:
            field.focus()
        except Exception:
            pass
        ev.wait()
        S["wait"] = None
        try:
            out_list.controls.remove(row)
        except ValueError:
            pass
        shown = text + S["answer"]
        S["out"].append((shown, "out"))
        out_list.controls.append(out_control(shown, "out"))
        ui_flush(True)
        if S["stopped"]:
            raise KeyboardInterrupt()
        return S["answer"]

    # ---------------------------------------------------------- التشغيل
    def show_error(ex, code):
        info = core.explain_error(ex, code)
        head = f"خطأ ({info['name']})"
        if info["line"]:
            head += f" في السطر {info['line']}"
        add_line(head, "err")
        if info["src"]:
            add_line("   " + info["src"], "dim")
        add_line("السبب: " + info["reason"], "err")
        if info["hint"]:
            add_line("الحل المقترح: " + info["hint"], "hint")
        if info["detail"]:
            add_line("التفاصيل: " + info["detail"], "dim")

    def set_running(flag):
        run_btn.icon = ic("STOP_CIRCLE") if flag else ic("PLAY_ARROW")
        run_btn.icon_color = C["err"] if flag else C["ok"]
        run_btn.tooltip = "ايقاف" if flag else "تشغيل"
        try:
            run_btn.update()
        except Exception:
            pass

    def run_clicked(e=None):
        th = S["thread"]
        if th and th.is_alive():
            stop()
            return
        ensure_out_visible()
        clear_out()
        code = editor.value or ""
        cur()["code"] = code
        schedule_save(now=True)
        try:
            compiled = compile(code, "main.py", "exec")
        except SyntaxError as ex:
            show_error(ex, code)
            ui_flush(True)
            return
        S["stopped"] = False

        def target():
            S["tid"] = threading.get_ident()
            old = (sys.stdout, sys.stderr)
            sys.stdout = sys.stderr = writer
            try:
                exec(compiled, {"__name__": "__main__", "__file__": "main.py", "input": my_input})
            except SystemExit:
                pass
            except KeyboardInterrupt:
                writer.done()
                add_line("تم ايقاف البرنامج", "err")
            except BaseException as ex:  # noqa: BLE001
                writer.done()
                show_error(ex, code)
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
            import ctypes
            ctypes.pythonapi.PyThreadState_SetAsyncExc(ctypes.c_ulong(tid),
                                                       ctypes.py_object(KeyboardInterrupt))

    # ----------------------------------------------------------- النوافذ
    def dlg_width():
        return min(380, (page.width or 400) - 40)

    def dialog(title, content, height=None, extra_actions=None):
        acts = list(extra_actions or [])
        acts.append(ft.TextButton("اغلاق", on_click=lambda e: page.close(dlg)))
        dlg = ft.AlertDialog(title=ft.Text(title),
                             content=ft.Container(content=content, width=dlg_width(), height=height),
                             actions=acts)
        page.open(dlg)
        return dlg

    def lv_height(frac=0.6):
        return int((page.height or 700) * frac)

    # --- الاعدادات
    def show_settings(e=None):
        size_label = ft.Text(f"حجم الخط: {int(S['fs'])}")
        char_label = ft.Text(f"معايرة ارقام الاسطر: {S['charw']:.2f}")

        def set_size(v):
            S["fs"] = clamp(float(v), 10, 32)
            sset("fs", S["fs"])
            size_label.value = f"حجم الخط: {int(S['fs'])}"
            apply_font()
            refresh_view(update=False)
            render_out_all()
            page.update()

        def on_size(ev):
            set_size(ev.control.value)

        slider = ft.Slider(min=10, max=32, divisions=22, value=S["fs"], on_change=on_size, expand=True)

        def bump(d):
            set_size(S["fs"] + d)
            slider.value = S["fs"]
            slider.update()

        def on_theme(ev):
            S["dark"] = bool(ev.control.value)
            sset("dark", S["dark"])
            page.close(dlg)
            build()

        def on_hl(ev):
            S["hl"] = bool(ev.control.value)
            sset("hl", S["hl"])
            apply_font()
            refresh_view(update=False)
            page.update()

        def on_ac(ev):
            S["ac"] = bool(ev.control.value)
            sset("ac", S["ac"])

        def on_af(ev):
            S["autofile"] = bool(ev.control.value)
            sset("autofile", S["autofile"])

        def on_charw(ev):
            S["charw"] = round(float(ev.control.value), 2)
            sset("charw", S["charw"])
            char_label.value = f"معايرة ارقام الاسطر: {S['charw']:.2f}"
            refresh_view()
            char_label.update()

        body = ft.Column([
            size_label,
            ft.Row([ft.IconButton(ic("TEXT_DECREASE"), on_click=lambda ev: bump(-1)), slider,
                    ft.IconButton(ic("TEXT_INCREASE"), on_click=lambda ev: bump(1))]),
            ft.Switch(label="الوضع الداكن (اسود)", value=S["dark"], on_change=on_theme),
            ft.Switch(label="تلوين الكود", value=S["hl"], on_change=on_hl),
            ft.Switch(label="اغلاق الاقواس والتنصيص تلقائيا", value=S["ac"], on_change=on_ac),
            ft.Switch(label="حفظ تلقائي في الملف المفتوح", value=S["autofile"], on_change=on_af),
            char_label,
            ft.Slider(min=0.5, max=0.7, divisions=20, value=S["charw"], on_change=on_charw),
            ft.Text("لو ارقام الاسطر لا تطابق السطور الطويلة غيّر المعايرة. ولو التلوين غير منطبق "
                    "على الكتابة اغلق خيار تلوين الكود.", size=12, color=C["gutter"]),
            ft.TextButton("مدير المكتبات", icon=ic("EXTENSION"),
                          on_click=lambda ev: (page.close(dlg), show_libs())),
        ], tight=True, scroll=ft.ScrollMode.AUTO)
        dlg = dialog("الاعدادات", body, height=lv_height(0.7))

    # --- الامثلة
    def show_examples(e=None):
        import examples_data
        cats = examples_data.categories()
        search = ft.TextField(hint_text="ابحث عن مثال...", dense=True, text_size=14,
                              prefix_icon=ic("SEARCH"))
        lv = ft.ListView(spacing=0, expand=True)

        def pick(title, code):
            def h(ev):
                page.close(dlg)
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
                    ft.Text(f"{cat} ({len(rows)})", weight=ft.FontWeight.BOLD, color=C["ok"]),
                    padding=ft.padding.only(top=10, bottom=2)))
                for t, c in rows:
                    ctrls.append(ft.ListTile(title=ft.Text(t, size=14), dense=True,
                                             on_click=pick(t, c)))
            if not ctrls:
                ctrls.append(ft.Text("لا توجد نتائج"))
            lv.controls = ctrls

        def on_search(ev):
            fill(search.value or "")
            lv.update()

        search.on_change = on_search
        fill()
        total = sum(len(v) for v in cats.values())
        body = ft.Column([search, lv], expand=True, spacing=4)
        dlg = dialog(f"امثلة وادوات جاهزة ({total})", body, height=lv_height(0.72))

    # --- الكلمات المحجوزة والدوال
    def show_keywords(e=None):
        import keyword
        ctrls = [ft.Text("الكلمات المحجوزة", weight=ft.FontWeight.BOLD, color=C["ok"])]
        for w in keyword.kwlist:
            ctrls.append(ft.ListTile(
                title=ft.Text(w, font_family=MONO, color=C["keyword"]),
                subtitle=ft.Text(core.KW_EXPLAIN.get(w, "كلمة محجوزة في بايثون."), size=12),
                dense=True))
        ctrls.append(ft.Text("الدوال المدمجة", weight=ft.FontWeight.BOLD, color=C["ok"]))
        for w, t in core.BUILTIN_EXPLAIN.items():
            ctrls.append(ft.ListTile(
                title=ft.Text(w + "()", font_family=MONO, color=C["builtin"]),
                subtitle=ft.Text(t, size=12), dense=True))
        ctrls.append(ft.Text("دوال النصوص والقوائم والقواميس", weight=ft.FontWeight.BOLD, color=C["ok"]))
        for w, t in core.METHOD_EXPLAIN.items():
            ctrls.append(ft.ListTile(
                title=ft.Text("." + w + "()", font_family=MONO, color=C["call"]),
                subtitle=ft.Text(t, size=12), dense=True))
        dialog("دليل بايثون", ft.ListView(ctrls, spacing=0), height=lv_height(0.72))

    def show_modules(e=None):
        rows = [ft.ListTile(title=ft.Text(m, font_family=MONO), subtitle=ft.Text(t, size=12), dense=True)
                for m, t in sorted(core.MODULES.items())]
        dialog("دليل المكتبات (Modules)", ft.ListView(rows, spacing=0), height=lv_height(0.72))

    # --- شرح الكود (زر المساعدة)
    def show_explain(e=None):
        code = editor.value or ""
        res = core.explain_code(code)
        ctrls = [ft.Text(f"عدد الاسطر: {res['lines']}", size=12, color=C["gutter"])]
        if res["error"] is not None:
            info = core.explain_error(res["error"], code)
            ctrls.append(ft.Text(
                f"تنبيه: في الكود خطأ كتابة (السطر {info['line']}): {info['reason']} {info['hint']}",
                color=C["err"], size=13))
        if not res["items"]:
            ctrls.append(ft.Text("لا يوجد كود لشرحه. اكتب كودا وجرّب مرة اخرى."))
        for label, text, lines in res["items"]:
            sub = text
            if lines:
                sub += "\nالسطر: " + "، ".join(str(x) for x in lines)
            ctrls.append(ft.ListTile(
                title=ft.Text(label, font_family=MONO, color=C["builtin"], size=14),
                subtitle=ft.Text(sub, size=12), dense=True))
        dialog("شرح الكود", ft.ListView(ctrls, spacing=0), height=lv_height(0.72))

    # --- ملفاتي
    def show_files(e=None):
        d = files_dir()
        lv = ft.ListView(spacing=0, expand=True)

        def refresh():
            names = sorted(n for n in os.listdir(d) if os.path.isfile(os.path.join(d, n)))
            rows = []
            for n in names:
                p = os.path.join(d, n)
                rows.append(ft.ListTile(
                    title=ft.Text(n, size=14), dense=True,
                    on_click=lambda ev, p=p: (page.close(dlg), open_path(p)),
                    trailing=ft.IconButton(ic("DELETE"), icon_size=20,
                                           on_click=lambda ev, p=p: delete(p))))
            lv.controls = rows or [ft.Text("لا توجد ملفات محفوظة بعد")]

        def delete(p):
            def yes(ev):
                try:
                    os.remove(p)
                    for t in S["tabs"]:
                        if t.get("path") == p:
                            t["path"] = ""
                            t["saved"] = ""
                except Exception as ex:
                    notify(str(ex))
                page.close(cd)
                refresh()
                lv.update()
                render_tabs()
            cd = ft.AlertDialog(
                title=ft.Text("حذف الملف؟"), content=ft.Text(os.path.basename(p)),
                actions=[ft.TextButton("الغاء", on_click=lambda ev: page.close(cd)),
                         ft.TextButton("حذف", on_click=yes)])
            page.open(cd)

        refresh()
        dlg = dialog("ملفاتي", lv, height=lv_height(0.5))

    # --- مدير المكتبات
    def show_libs(e=None):
        import importlib
        import pkgs
        site = pkgs.site_dir(BASE)
        name_f = ft.TextField(hint_text="اسم المكتبة مثل requests", dense=True, expand=True, text_size=14)
        log_col = ft.Column([], spacing=2, scroll=ft.ScrollMode.AUTO, height=130)
        inst_col = ft.Column([], spacing=0)
        busy = {"v": False}
        btn = ft.ElevatedButton("تثبيت")

        def log(msg):
            log_col.controls.append(ft.Text(msg, size=12, selectable=True))
            try:
                log_col.update()
            except Exception:
                pass

        def refresh_installed():
            rows = []
            for n, v in pkgs.list_installed(site):
                rows.append(ft.Row([
                    ft.Text(f"{n}  {v}", expand=True, size=13),
                    ft.IconButton(ic("DELETE"), icon_size=18,
                                  on_click=lambda ev, n=n: remove(n))]))
            inst_col.controls = rows or [ft.Text("لا توجد مكتبات مثبتة", size=12, color=C["gutter"])]

        def remove(n):
            pkgs.uninstall(site, n)
            importlib.invalidate_caches()
            refresh_installed()
            inst_col.update()

        def do_install(ev):
            n = (name_f.value or "").strip()
            if not n or busy["v"]:
                return
            busy["v"] = True
            btn.disabled = True
            btn.update()

            def work():
                try:
                    ok = pkgs.install(n, site, log)
                    pkgs.activate(site)
                    importlib.invalidate_caches()
                    log("تم بنجاح. يمكنك الآن: import " + n.replace("-", "_") if ok else "لم يكتمل التثبيت")
                finally:
                    busy["v"] = False
                    btn.disabled = False
                    refresh_installed()
                    try:
                        btn.update()
                        inst_col.update()
                    except Exception:
                        pass

            threading.Thread(target=work, daemon=True).start()

        btn.on_click = do_install

        def chip(n):
            return ft.Container(ft.Text(n, size=12, font_family=MONO), padding=ft.padding.symmetric(6, 10),
                                border=ft.border.all(1, C["gutter"]), border_radius=14,
                                on_click=lambda ev: (setattr(name_f, "value", n), name_f.update()))

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

    # ------------------------------------------------------- بناء الواجهة
    def render_out_all():
        out_list.controls = [out_control(t, k) for t, k in S["out"]]

    def sym_button(sym):
        label = "Tab" if sym == "TAB" else sym
        return ft.Container(ft.Text(label, size=16, font_family=MONO, color=C["fg"]),
                            padding=ft.padding.symmetric(vertical=9, horizontal=14),
                            margin=ft.margin.all(2), bgcolor=C["sym"], border_radius=6,
                            on_click=lambda e, s=sym: on_sym(s))

    def build():
        C.clear()
        C.update(palette())
        page.theme_mode = ft.ThemeMode.DARK if S["dark"] else ft.ThemeMode.LIGHT
        page.bgcolor = C["bg"]

        setp(editor, multiline=True, max_lines=None, border=ft.InputBorder.NONE,
             content_padding=0, cursor_color=C["ok"], keyboard_type=ft.KeyboardType.MULTILINE,
             autocorrect=False, enable_suggestions=False, dense=True, filled=False)
        editor.on_change = on_change
        setp(editor, on_selection_change=on_sel)
        apply_font()

        run_btn.icon = ic("PLAY_ARROW")
        run_btn.icon_color = C["ok"]
        run_btn.icon_size = 30
        run_btn.tooltip = "تشغيل"
        run_btn.on_click = run_clicked

        menu = ft.PopupMenuButton(
            icon=ic("MORE_VERT"), icon_color=C["fg"],
            items=[
                ft.PopupMenuItem(text="ملف جديد", icon=ic("NOTE_ADD"), on_click=lambda e: new_tab()),
                ft.PopupMenuItem(text="فتح ملف", icon=ic("FOLDER_OPEN"), on_click=open_picker),
                ft.PopupMenuItem(text="ملفاتي", icon=ic("FOLDER"), on_click=show_files),
                ft.PopupMenuItem(text="حفظ", icon=ic("SAVE"), on_click=save_current),
                ft.PopupMenuItem(text="حفظ باسم", icon=ic("SAVE_AS"), on_click=save_as),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(text="امثلة وادوات جاهزة", icon=ic("LIGHTBULB"), on_click=show_examples),
                ft.PopupMenuItem(text="دليل بايثون (كلمات ودوال)", icon=ic("KEY"), on_click=show_keywords),
                ft.PopupMenuItem(text="دليل المكتبات", icon=ic("MENU_BOOK"), on_click=show_modules),
                ft.PopupMenuItem(text="مدير المكتبات", icon=ic("EXTENSION"), on_click=show_libs),
                ft.PopupMenuItem(),
                ft.PopupMenuItem(text="الاعدادات والخط", icon=ic("SETTINGS"), on_click=show_settings),
            ])

        appbar = ft.Container(
            content=ft.Row([
                run_btn,
                ft.Container(expand=True),
                ft.IconButton(ic("TERMINAL"), icon_color=C["fg"], on_click=toggle_out,
                              tooltip="اظهار/اخفاء المخرجات"),
                ft.IconButton(ic("HELP_OUTLINE"), icon_color=C["fg"], on_click=show_explain,
                              tooltip="شرح الكود"),
                menu,
            ], spacing=0),
            bgcolor=C["bar"], padding=ft.padding.symmetric(horizontal=6, vertical=2))

        render_tabs(update=False)
        tabs_box = ft.Container(tabs_row, bgcolor=C["bar"], padding=ft.padding.only(left=6, top=2))

        stack = ft.Stack([ft.Container(hl_text, left=0, top=0, right=0), editor], expand=True)
        editor_area = ft.Container(
            content=ft.Column(
                [ft.Row([ft.Container(gutter, width=36, alignment=ft.alignment.top_right),
                         stack], vertical_alignment=ft.CrossAxisAlignment.START, spacing=8)],
                scroll=ft.ScrollMode.AUTO, expand=True),
            expand=True, padding=ft.padding.only(left=6, right=10, top=8, bottom=4), bgcolor=C["bg"])

        header = ft.Container(
            content=ft.Row([
                ft.Icon(ic("DRAG_HANDLE"), color=C["gutter"]),
                ft.Text("المخرجات", color=C["fg"], weight=ft.FontWeight.BOLD, expand=True),
                ft.IconButton(ic("DELETE_SWEEP"), icon_color=C["fg"], on_click=clear_out, tooltip="مسح"),
                ft.IconButton(ic("EXPAND_MORE"), icon_color=C["fg"], on_click=toggle_collapse,
                              tooltip="طي/فرد"),
                ft.IconButton(ic("EXPAND_LESS"), icon_color=C["fg"], on_click=maximize_out,
                              tooltip="تكبير"),
                ft.IconButton(ic("VISIBILITY_OFF"), icon_color=C["fg"], on_click=toggle_out,
                              tooltip="اخفاء"),
            ], spacing=0),
            bgcolor=C["bar"], height=HEADER_H, padding=ft.padding.only(left=10))
        drag = ft.GestureDetector(content=header, on_vertical_drag_update=on_drag,
                                  on_vertical_drag_end=on_drag_end)
        setp(drag, drag_interval=10)

        out_panel.content = ft.Column([drag, out_list], spacing=0)
        out_panel.bgcolor = C["panel"]
        out_panel.border = ft.border.only(top=ft.BorderSide(1, C["line"]))
        render_out_all()
        apply_out(update=False)

        sym_bar = ft.Container(
            ft.Row([sym_button(s) for s in SYMBOLS], scroll=ft.ScrollMode.AUTO, spacing=0),
            bgcolor=C["bar"], padding=ft.padding.symmetric(vertical=2))

        page.controls.clear()
        page.add(ft.SafeArea(
            ft.Column([appbar, tabs_box, editor_area, out_panel, sym_bar], spacing=0, expand=True),
            expand=True))
        set_editor_text(cur()["code"], update=False)
        page.update()

    def on_resize(e):
        apply_font()
        refresh_view(update=False)
        apply_out(update=False)
        try:
            page.update()
        except Exception:
            pass

    page.on_resize = on_resize
    build()


ft.app(target=main)
