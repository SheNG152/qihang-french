import json
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch
import wave

from daily_content import BUILTIN, daily_packs, select_lesson
from daily_practice_config import load_settings
from fluency_session import DEMO_PACK as CHAINS
from lecture import MEDIA, catalog
from practice_records import Mode
from scripts.validate_daily_practice import validate
from slot_session import DEMO_PACK as FRAMES


class StarterSpeakingTest(TestCase):
    def test_shipped_reading_tracks_and_sections(self):
        lessons = [p for p in catalog(MEDIA, playable=True).values() if p['id'].startswith('studio-')]
        self.assertEqual([p['unit'] for p in lessons], list(range(1, 9)))
        for lesson in lessons:
            with self.subTest(lesson=lesson['id']):
                self.assertEqual(len(lesson['sentences']), 4)
                self.assertIn('原创', lesson['source'])
                with wave.open(str(BUILTIN / 'lecture' / f"{lesson['piste']:03d}.wav"), 'rb') as audio:
                    self.assertEqual(audio.getframerate(), 16000)
                    self.assertTrue(all(0 <= s['start'] < s['end'] <= audio.getnframes() / 16000
                                        for s in lesson['sentences']))

    def test_all_rhythm_lessons_and_the_approved_slot_contrast(self):
        chains = daily_packs(CHAINS, CHAINS)
        for unit in range(1, 9):
            path, _ = select_lesson(chains, f'studio-u{unit:02d}')
            self.assertEqual(validate(path, 'formal'), 6)
        path, lesson = select_lesson(daily_packs(FRAMES, FRAMES), 'studio-u05')
        self.assertEqual(validate(path, 'formal'), 3)
        for frame in lesson['frames']:
            self.assertEqual({c['form'] for c in frame['candidates']}, {'du sport', 'de la muscu'})
            self.assertEqual(len(frame['prompts']), 4)

    def test_explicit_switches_win_over_shipped_defaults(self):
        with TemporaryDirectory() as scratch:
            path = Path(scratch) / 'daily-practice.json'
            path.write_text(json.dumps({'slot': {'enabled':False}}), encoding='utf-8')
            settings = load_settings(path.parent, {Mode.FLUENCY, Mode.SLOT})
            self.assertTrue(settings[Mode.FLUENCY].enabled)
            self.assertFalse(settings[Mode.SLOT].enabled)

    def test_first_lesson_adaptations_have_distinct_exercise_references(self):
        path, lesson = select_lesson(daily_packs(CHAINS, CHAINS),'inspire1-u01-l01-oralise')
        self.assertEqual(validate(path, 'formal'), 4)
        mappings = json.loads((BUILTIN/'inspire1-exercise-mapping.json').read_text(encoding='utf-8'))
        self.assertEqual({row['exercise'] for row in mappings},{f'L01-ACT{number:02d}' for number in range(1,5)})
        self.assertEqual({row['item'] for row in mappings},
                         {f'{lesson["lesson_id"]}/{chain["id"]}' for chain in lesson['chains']})
        self.assertTrue(all(chain['cue'] and 'PDF 第' in chain['source'] for chain in lesson['chains']))

    def test_private_lesson_discovery_cannot_shadow_another_lesson(self):
        with TemporaryDirectory() as scratch:
            root = Path(scratch)
            primary = root / 'media/demo/chains.json'
            extra = root / 'media/local/chains.json'
            shipped = root / 'builtin/daily/shipped/chains.json'
            for path, key in [(primary, 'demo'), (extra, 'private'), (shipped, 'shipped')]:
                path.parent.mkdir(parents=True)
                path.write_text(json.dumps({'lesson_id':key}), encoding='utf-8')
            with patch('daily_content.BUILTIN', root / 'builtin'):
                self.assertEqual(list(daily_packs(primary, primary)), ['demo','private','shipped'])
                extra.write_text(json.dumps({'lesson_id':'shipped'}), encoding='utf-8')
                with self.assertRaisesRegex(ValueError, '课次编号重复：shipped'):
                    daily_packs(primary, primary)
