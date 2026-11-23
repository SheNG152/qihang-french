"""Start the local preview's own daily-practice service on first use."""
import argparse
import ctypes
from http.cookiejar import CookieJar
import json
import msvcrt
from pathlib import Path
import socket
import subprocess
import sys
import time
import urllib.request
import webbrowser

HOME = Path(__file__).resolve().parent
HTTP = urllib.request.build_opener(urllib.request.ProxyHandler({}),
                                   urllib.request.HTTPCookieProcessor(CookieJar()))


def health(port):
    try:
        with HTTP.open(f'http://127.0.0.1:{port}/api/health', timeout=1) as request:
            value = json.load(request)
        return value.get('pid') if value.get('local_only') is True else None
    except (OSError, ValueError):
        return None


def read_pid(path):
    try:
        return json.loads(path.read_text(encoding='utf-8'))['pid']
    except (OSError, ValueError, KeyError):
        return None


def wait_for_lock(lock):
    for _ in range(350):
        try:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            return
        except OSError:
            time.sleep(.4)
    raise RuntimeError('日常口语仍在准备，请稍后再试。')


def run(options):
    port, speech_port = options.port, options.speech_port
    if port == speech_port or not all(1024 <= value <= 65535 for value in (port, speech_port)):
        raise RuntimeError('日常口语端口配置无效。')
    data = options.data_dir.resolve()
    data.mkdir(parents=True, exist_ok=True)
    marker = data / 'preview-runtime.json'
    settings = json.loads((HOME / 'local-runtime.json').read_text(encoding='utf-8'))
    with (data / 'startup-lock').open('a+b') as lock:
        if not lock.tell():
            lock.write(b'0')
            lock.flush()
        wait_for_lock(lock)
        try:
            active = health(port)
            if active is not None and active != read_pid(marker):
                raise RuntimeError(f'端口 {port} 已被其他日常口语服务占用。')
            if active is None:
                with socket.socket() as sock:
                    if sock.connect_ex(('127.0.0.1', port)) == 0:
                        raise RuntimeError(f'端口 {port} 已被占用。')
                oral = HOME / 'oral-assistant'
                args = [settings['python'], '-X', 'utf8', str(oral / 'scripts/preview_daily_practice.py'),
                        '--runtime-dir', settings['modelRuntime'], '--data-dir', str(data),
                        '--port', str(port), '--speech-port', str(speech_port), '--no-browser']
                private_assets = HOME / (settings.get('gamePrivateAssets') or 'assets-private')
                if private_assets.is_dir():
                    args.extend(('--game-private-assets-dir', str(private_assets.resolve())))
                log_path = data / '启动日志.txt'
                with log_path.open('ab') as log:
                    child = subprocess.Popen(args, cwd=oral, stdout=log, stderr=subprocess.STDOUT,
                                             creationflags=subprocess.CREATE_NO_WINDOW)
                for _ in range(300):
                    if child.poll() is not None:
                        raise RuntimeError(f'日常口语启动失败。启动日志在：{log_path}')
                    active = health(port)
                    if active:
                        marker.write_text(json.dumps({'pid':active}), encoding='utf-8')
                        break
                    time.sleep(.4)
                else:
                    child.terminate()
                    raise RuntimeError(f'本机模型预热超时。启动日志在：{log_path}')
            address = f'http://127.0.0.1:{port}/?desktop=1&daily=1'
            if not options.no_browser and not webbrowser.open(address):
                raise RuntimeError(f'无法打开默认浏览器。请在浏览器中打开 {address}')
        finally:
            lock.seek(0)
            msvcrt.locking(lock.fileno(), msvcrt.LK_UNLCK, 1)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('data_dir', type=Path)
    parser.add_argument('--port', type=int, default=8127)
    parser.add_argument('--speech-port', type=int, default=18980)
    parser.add_argument('--no-browser', action='store_true')
    options = parser.parse_args()
    try:
        run(options)
    except Exception as error:
        if options.no_browser:
            print(str(error), file=sys.stderr)
            raise SystemExit(1)
        ctypes.windll.user32.MessageBoxW(None, str(error), '启航法语 · 日常口语', 0x10)
        raise SystemExit(1)
