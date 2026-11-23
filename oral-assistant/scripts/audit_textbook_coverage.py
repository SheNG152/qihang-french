"""Compare a reviewed textbook exercise index with an explicit practice mapping."""
import argparse
from collections import Counter
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from daily_content import daily_packs
from fluency_session import DEMO_PACK as CHAINS
from lecture import MEDIA, catalog
from slot_session import DEMO_PACK as FRAMES


def practice_items():
    packs = catalog(MEDIA, playable=True)
    chains = daily_packs(CHAINS, CHAINS)
    frames = daily_packs(FRAMES, FRAMES)
    return {
        'lecture': {f'{pack}/{row["id"]}' for pack, lesson in packs.items()
                    for row in lesson['sentences']},
        'fluency': {f'{pack}/{row["id"]}' for pack, (_, lesson) in chains.items()
                    for row in lesson['chains']},
        'slot': {f'{pack}/{frame["id"]}/{row["id"]}' for pack, (_, lesson) in frames.items()
                 for frame in lesson['frames'] for row in frame['prompts']},
    }


def audit(source, mappings, items):
    rows = source['exercises']
    if type(source['complete']) is not bool or not rows:
        raise ValueError('题源索引需要标明是否为完整清单，并且至少包含一道题。')
    if any(not isinstance(row['id'], str) or not row['id'].strip() for row in rows):
        raise ValueError('题源 ID 必须是非空字符串。')
    counts = Counter(row['id'] for row in rows)
    source_duplicates = sorted(key for key, count in counts.items() if count > 1)
    bad_mappings, mapped = [], set()
    mapping_counts = Counter((row['exercise'], row['mode'], row['item']) for row in mappings)
    for (exercise, mode, item), count in mapping_counts.items():
        if exercise not in counts or item not in items.get(mode, set()) or count > 1:
            bad_mappings.append({'exercise':exercise, 'mode':mode, 'item':item, 'count':count})
        else:
            mapped.add(exercise)
    missing = [row for row in rows if row['id'] not in mapped]
    return {
        'edition': source['edition'],
        'source_index_complete': source['complete'],
        'source_index_count': len(counts),
        'practice_items': {mode:len(keys) for mode, keys in items.items()},
        'mapped_count': len(mapped),
        'missing': missing,
        'source_duplicates': source_duplicates,
        'invalid_or_duplicate_mappings': bad_mappings,
        'complete_coverage': source['complete'] and not (missing or source_duplicates or bad_mappings),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('source_index', type=Path)
    parser.add_argument('mapping', type=Path)
    args = parser.parse_args()
    source, mapping = [json.loads(path.read_text(encoding='utf-8-sig'))
                       for path in (args.source_index, args.mapping)]
    result = audit(source, mapping, practice_items())
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result['complete_coverage'] else 1


if __name__ == '__main__':
    raise SystemExit(main())
