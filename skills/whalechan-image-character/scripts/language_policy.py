"""Task language contracts and offline locale packs; language inference belongs to the agent."""
import copy
import json
import re
from pathlib import Path
from string import Formatter

ROOT = Path(__file__).resolve().parents[1]
FIELDS = {'language', 'language_overrides', 'language_resolution', 'localizations', 'run_title'}
SCOPES = {'communication', 'visible_text', 'interface', 'prompt', 'titles'}
ALIASES = {'zh': 'zh-Hans', 'zh-CN': 'zh-Hans', 'zh-SG': 'zh-Hans', 'zh-TW': 'zh-Hant', 'zh-HK': 'zh-Hant'}


def tag(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z]{2,8}(?:-[a-zA-Z0-9]{1,8})*', value):
        raise ValueError('Use a BCP-47 language tag')
    parts = value.split('-')
    value = '-'.join([parts[0].lower()] + [p.title() if len(p) == 4 else p.upper() if len(p) == 2 else p.lower() for p in parts[1:]])
    return ALIASES.get(value, value)


def effective(value, scope):
    return tag(value.get('language_overrides', {}).get(scope, value['language']))


def placeholders(value):
    return {field for _, field, _, _ in Formatter().parse(value) if field is not None}


def check_dictionary(actual, expected, path='locale'):
    if isinstance(expected, dict):
        if not isinstance(actual, dict) or set(actual) != set(expected):
            raise ValueError(f'{path}: missing or unexpected translation keys')
        for key in expected:
            check_dictionary(actual[key], expected[key], f'{path}.{key}')
    elif not isinstance(actual, str) or not actual.strip() or placeholders(actual) != placeholders(expected):
        raise ValueError(f'{path}: empty translation or mismatched placeholders')


def locale(value, language, section):
    language = tag(language)
    baseline = json.loads((ROOT / 'assets/locales/en.json').read_text())
    path = ROOT / 'assets/locales' / f'{language}.json'
    bundled = json.loads(path.read_text()) if path.is_file() else {}
    supplied = value.get('localizations', {}).get(language, {})
    result = supplied.get(section, bundled.get(section))
    if result is None:
        raise ValueError(f'Missing {language}.{section}; author the complete locale before continuing')
    check_dictionary(result, baseline[section], f'{language}.{section}')
    return copy.deepcopy(result)


def contract(value):
    """Only new schemas call this; legacy approval hashes remain unchanged."""
    language = tag(value.get('language'))
    if language != value['language']:
        raise ValueError('Store the normalized language tag')
    overrides = value.get('language_overrides', {})
    if not isinstance(overrides, dict) or set(overrides) - SCOPES:
        raise ValueError('Unknown language override scope')
    for scope, code in overrides.items():
        if tag(code) != code:
            raise ValueError(f'Normalize language_overrides.{scope}')
    evidence = value.get('language_resolution')
    if not isinstance(evidence, dict) or evidence.get('source') not in {'explicit', 'current-session', 'recent-session', 'user-answer'} or not evidence.get('reason'):
        raise ValueError('Record actual language resolution source and reason')
    if not isinstance(value.get('run_title'), str) or not value['run_title'].strip():
        raise ValueError('run_title is required for new tasks')
    return {k: copy.deepcopy(value[k]) for k in FIELDS if k in value}


def validate(value, comic=False, images=True):
    result = contract(value)
    if images:
        for image in value.get('images', []):
            if not isinstance(image.get('title'), str) or not image['title'].strip():
                raise ValueError('Every new image needs a visible title')
            text = image.get('text')
            if text and effective(value, 'visible_text') not in [tag(x) for x in text['languages']] and text['content'] not in value['language_resolution'].get('preserved_text', []):
                raise ValueError('text.languages must include the resolved visible-text language')
    if comic and tag(value['input']['language']) != effective(value, 'visible_text'):
        raise ValueError('input.language differs from the resolved visible-text language')
    return result


def gallery_locales(assignments, extra=None):
    """Merge only UI dictionaries; never translate saved task content."""
    merged = {}
    languages = ['zh-Hans', 'en']
    for value in assignments:
        for code, pack in value.get('localizations', {}).items():
            code = tag(code)
            if 'gallery' in pack:
                if code in merged and any(merged[code].get(k) != pack.get(k) for k in ('gallery', 'name', 'direction')):
                    raise ValueError(f'Conflicting gallery locale: {code}')
                merged[code] = pack
        if value.get('language'):
            used = [value['language'], *value.get('language_overrides', {}).values()]
            if value.get('input', {}).get('language'):
                used.append(value['input']['language'])
            for image in value.get('images', []):
                used.extend((image.get('text') or {}).get('languages', []))
            for code in used:
                if tag(code) not in languages:
                    languages.append(tag(code))
    for code, pack in (extra or {}).items():
        merged[tag(code)] = pack
    result, names, directions = {}, {}, {}
    for code in languages:
        result[code] = locale({'localizations': merged}, code, 'gallery')
        path = ROOT / 'assets/locales' / f'{code}.json'
        metadata = merged.get(code) or (json.loads(path.read_text()) if path.is_file() else {})
        if not metadata.get('name') or metadata.get('direction') not in {'ltr', 'rtl'}:
            raise ValueError(f'{code}: locale requires a native name and ltr/rtl direction')
        names[code], directions[code] = metadata['name'], metadata['direction']
    return result, names, directions


def overrides_text(value, words):
    return "; ".join(words["scopes"][scope] + ": " + code for scope, code in value.get("language_overrides", {}).items()) or words["none"]
