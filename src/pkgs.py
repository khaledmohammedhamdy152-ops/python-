"""مدير مكتبات بسيط: يحمّل مكتبات بايثون النقية (pure python wheels) من PyPI.

لا يدعم المكتبات المبنية بلغة C مثل numpy و pandas لأنها تحتاج بناء خاص لكل جهاز.
"""
import hashlib
import io
import json
import os
import re
import sys
import zipfile


def site_dir(base):
    d = os.path.join(base, "site-packages")
    os.makedirs(d, exist_ok=True)
    return d


def activate(d):
    if os.path.isdir(d) and d not in sys.path:
        sys.path.append(d)


def norm(name):
    return re.sub(r"[-_.]+", "-", name).lower()


def _fetch_json(url):
    from urllib.request import Request, urlopen
    req = Request(url, headers={"User-Agent": "pyeditor/0.2"})
    with urlopen(req, timeout=25) as r:
        return json.load(r)


def _download(url):
    from urllib.request import Request, urlopen
    req = Request(url, headers={"User-Agent": "pyeditor/0.2"})
    with urlopen(req, timeout=60) as r:
        return r.read()


def list_installed(site):
    out = []
    try:
        for n in sorted(os.listdir(site)):
            if n.endswith(".dist-info"):
                base = n[:-len(".dist-info")]
                name, _, ver = base.rpartition("-")
                out.append((name or base, ver))
    except OSError:
        pass
    return out


def is_installed(site, name):
    n = norm(name)
    return any(norm(x[0]) == n for x in list_installed(site))


def _pick_wheel(data):
    for u in data.get("urls", []):
        if u.get("packagetype") == "bdist_wheel" and u.get("filename", "").endswith("-none-any.whl"):
            return u
    return None


def _extract(blob, site):
    root = os.path.realpath(site)
    with zipfile.ZipFile(io.BytesIO(blob)) as z:
        for m in z.infolist():
            dest = os.path.realpath(os.path.join(site, m.filename))
            if not (dest == root or dest.startswith(root + os.sep)):
                raise ValueError("ملف مشبوه داخل الحزمة: " + m.filename)
        z.extractall(site)


def install(name, site, log, fetch=None, download=None, _seen=None, _depth=0):
    """يثبت المكتبة واعتمادياتها غير المشروطة. يعيد True عند النجاح."""
    fetch = fetch or _fetch_json
    download = download or _download
    seen = _seen if _seen is not None else set()
    key = norm(name)
    if key in seen:
        return True
    seen.add(key)
    pad = "  " * _depth

    if is_installed(site, name):
        log(f"{pad}{name}: مثبتة بالفعل")
        return True
    try:
        data = fetch(f"https://pypi.org/pypi/{name}/json")
    except Exception as ex:  # noqa: BLE001
        log(f"{pad}تعذر الاتصال بـ PyPI لمكتبة {name}: {type(ex).__name__}: {ex}")
        return False

    whl = _pick_wheel(data)
    ver = data.get("info", {}).get("version", "?")
    if not whl:
        log(f"{pad}{name}: لا توجد نسخة بايثون نقية (pure python) متاحة، "
            "غالبا لأنها مكتبة مبنية بلغة C ولا يمكن تثبيتها هنا.")
        return False

    log(f"{pad}تحميل {name} {ver} ...")
    try:
        blob = download(whl["url"])
        want = (whl.get("digests") or {}).get("sha256")
        if want and hashlib.sha256(blob).hexdigest() != want:
            log(f"{pad}فشل التحقق من سلامة الملف (sha256) لمكتبة {name}")
            return False
        _extract(blob, site)
    except Exception as ex:  # noqa: BLE001
        log(f"{pad}فشل تثبيت {name}: {type(ex).__name__}: {ex}")
        return False
    log(f"{pad}تم تثبيت {name} {ver}")

    if _depth < 4:
        for line in data.get("info", {}).get("requires_dist") or []:
            req, _, marker = line.partition(";")
            if marker.strip():
                continue  # اعتماديات مشروطة (نظام/اضافات) نتخطاها
            m = re.match(r"[A-Za-z0-9][A-Za-z0-9._-]*", req.strip())
            if not m:
                continue
            dep = m.group()
            if not install(dep, site, log, fetch, download, seen, _depth + 1):
                log(f"{pad}تنبيه: تعذر تثبيت الاعتمادية {dep}")
    return True


def uninstall(site, name):
    n = norm(name)
    for d in sorted(os.listdir(site)):
        if not d.endswith(".dist-info"):
            continue
        base = d[:-len(".dist-info")]
        pkg, _, _ver = base.rpartition("-")
        if norm(pkg) != n:
            continue
        info = os.path.join(site, d)
        rec = os.path.join(info, "RECORD")
        removed = 0
        root = os.path.realpath(site)
        if os.path.isfile(rec):
            with open(rec, encoding="utf-8") as f:
                for line in f:
                    rel = line.split(",")[0].strip()
                    if not rel:
                        continue
                    p = os.path.realpath(os.path.join(site, rel))
                    if p.startswith(root + os.sep) and os.path.isfile(p):
                        os.remove(p)
                        removed += 1
        # تنظيف ملفات التخزين المؤقت والمجلدات الفارغة
        import shutil
        for dirpath, dirnames, filenames in os.walk(site, topdown=False):
            if os.path.basename(dirpath) == "__pycache__":
                shutil.rmtree(dirpath, ignore_errors=True)
            elif dirpath != site and not os.listdir(dirpath):
                os.rmdir(dirpath)
        return True
    return False
