"""مكتبة الأمثلة والأدوات. تُحمَّل عند الحاجة فقط حتى لا تبطئ بدء التطبيق."""
from ex_basics import ITEMS as _B
from ex_tools import ITEMS as _T
from ex_games import ITEMS as _G
from ex_more import ITEMS as _M

# كل عنصر: (التصنيف, العنوان, الكود, مدخلات_اختبار)
ALL = list(_B) + list(_T) + list(_G) + list(_M)

ORDER = ["أساسيات", "أدوات", "ألعاب", "خوارزميات"]


def categories():
    out = {}
    for cat, title, code, _inputs in ALL:
        out.setdefault(cat, []).append((title, code))
    return {c: out[c] for c in ORDER if c in out}
