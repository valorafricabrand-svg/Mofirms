import importlib
import pkgutil

from django import template
from django.utils.safestring import mark_safe

register = template.Library()

_CACHE = None


def _load_strings():
    global _CACHE
    if _CACHE is not None:
        return _CACHE
    import mofirms_backend.i18n_strings as pkg

    merged = {}
    for _, name, _ in pkgutil.iter_modules(pkg.__path__):
        module = importlib.import_module(f"{pkg.__name__}.{name}")
        merged.update(getattr(module, "STRINGS", {}))
    _CACHE = merged
    return merged


def current_lang(request):
    code = getattr(request, "COOKIES", {}).get("lang", "en")
    return "sw" if code == "sw" else "en"


def translate(key, lang, **kwargs):
    """Plain-Python lookup for use in forms.py/views.py, outside templates."""
    entry = _load_strings().get(key)
    text = (entry.get(lang) or entry.get("en") or key) if entry else key
    if kwargs:
        text = text.format(**kwargs)
    return text


def localize_choices(choices, lang, key_prefix):
    """Rebuild a Django choices iterable with translated labels, same values."""
    return [
        (value, translate(f"{key_prefix}.{value}", lang))
        for value, _label in choices
    ]


@register.simple_tag(takes_context=True)
def t(context, key):
    request = context.get("request")
    lang = current_lang(request) if request else "en"
    entry = _load_strings().get(key)
    if not entry:
        return key
    return mark_safe(entry.get(lang) or entry.get("en") or key)


@register.simple_tag(takes_context=True)
def choice_label(context, value, prefix):
    request = context.get("request")
    lang = current_lang(request) if request else "en"
    return mark_safe(translate(f"{prefix}.{value}", lang))


@register.simple_tag(takes_context=True)
def current_language_code(context):
    request = context.get("request")
    return current_lang(request) if request else "en"
