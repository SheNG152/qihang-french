"""Package the exact public recordings referenced by the dictionary index."""
from pathlib import Path
import hashlib
import json
import zipfile

ROOT = Path(__file__).resolve().parents[1]
AUDIO = ROOT / 'src/static/lexicon/audio'
DELIVERY = ROOT / '交付/2.2.0'

def sha(path):
    with path.open('rb') as stream:
        return hashlib.file_digest(stream, 'sha256').hexdigest()

def main():
    index = json.loads((AUDIO / 'index.json').read_text(encoding='utf-8'))
    files = []
    for name in sorted({clip['file'] for clip in index['entries'].values()}):
        path = AUDIO / name
        digest = sha(path)
        if name != digest + '.mp3':
            raise ValueError('Invalid recording: ' + name)
        files.append({'name': name, 'size': path.stat().st_size, 'sha256': digest})
    DELIVERY.mkdir(parents=True, exist_ok=True)
    archive = DELIVERY / 'QihangFrench-ExtraAudio-v1.zip'
    with zipfile.ZipFile(archive, 'w', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as target:
        resources = [(AUDIO / entry['name'], 'audio/' + entry['name']) for entry in files]
        resources.append((AUDIO / 'index.json', 'audio/index.json'))
        resources += [(path, 'licenses/' + path.name) for path in (ROOT / 'src/static/lexicon').iterdir()
                      if path.suffix in ('.txt', '.md', '.html')]
        for path, name in resources:
            info = zipfile.ZipInfo(name, (2026, 1, 1, 0, 0, 0))
            info.compress_type = zipfile.ZIP_DEFLATED
            target.writestr(info, path.read_bytes(), compresslevel=6)
    manifest = {
        'id': 'extra-audio-v1', 'revision': sha(AUDIO / 'index.json'), 'label': '非课内语音包',
        'filename': archive.name, 'size': archive.stat().st_size,
        'expandedSize': sum(entry['size'] for entry in files), 'sha256': sha(archive),
        'sources': [{'id': 'github', 'name': 'GitHub',
                     'url': 'https://github.com/zyh307/qihang-french/releases/download/v2.2.0/' + archive.name}],
        'files': files,
    }
    (ROOT / 'native/extra-audio-manifest.json').write_text(
        json.dumps(manifest, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    public = {key: value for key, value in manifest.items() if key != 'files'}
    (ROOT / 'src/static/lexicon/voice-pack.json').write_text(
        json.dumps(public, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    print(json.dumps({'clips': len(index['entries']), 'files': len(files), 'size': manifest['size'],
                      'sha256': manifest['sha256']}, ensure_ascii=False))

if __name__ == '__main__':
    main()
