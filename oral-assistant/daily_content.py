"""Discover shipped speaking lessons and optional locally installed packs."""
import json
import re
from pathlib import Path

from aiohttp import web

ROOT = Path(__file__).parent
BUILTIN = ROOT / 'content/starter-speaking'


def daily_packs(primary, default_path):
    paths = [primary]
    if primary == default_path:
        paths.extend(path for path in sorted(primary.parent.parent.glob(f'*/{primary.name}'))
                     if path != primary)
        paths.extend(sorted((BUILTIN / 'daily').glob(f'*/{default_path.name}')))
    lessons = {}
    for path in paths:
        if path.is_file():
            lesson = json.loads(path.read_text(encoding='utf-8'))
            key = lesson['lesson_id']
            if key in lessons:
                raise ValueError(f'日常口语课次编号重复：{key}')
            lessons[key] = (path, lesson)
    return lessons


def select_lesson(lessons, lesson_id=None):
    if not lessons:
        raise web.HTTPNotFound(text='没有安装可用的日常口语课包')
    if lesson_id is None:
        return next(iter(lessons.values()))
    if lesson_id not in lessons:
        raise ValueError('找不到这节日常口语课')
    return lessons[lesson_id]


def lesson_choices(lessons):
    def choice(key, lesson):
        textbook = re.fullmatch(r'inspire1-u(\d+)-l(\d+)(-oralise)?', key)
        thematic = re.fullmatch(r'studio-u(\d+)', key)
        unit = int((textbook or thematic)[1]) if textbook or thematic else None
        number = int(textbook[2]) if textbook else None
        group = ('adapted' if textbook[3] else 'textbook') if textbook else ('theme' if thematic else 'local')
        count = (len(lesson['chains']) if 'chains' in lesson else
                 sum(len(frame['prompts']) for frame in lesson.get('frames', [])))
        return {'id':key, 'label':lesson.get('label', key), 'title':lesson.get('title', {'zh':key}),
                'group':group, 'unit':unit, 'number':number, 'count':count}

    groups = ('textbook', 'adapted', 'theme', 'local')
    choices = (choice(key, lesson) for key, (_, lesson) in lessons.items())
    return sorted(choices, key=lambda row: (groups.index(row['group']), row['unit'] or 0,
                                            row['number'] or 0, row['id']))
