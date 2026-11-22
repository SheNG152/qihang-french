"""Start an isolated daily speaking preview with a local French model."""
import argparse
import asyncio
import os
from pathlib import Path
import secrets
import sys
from tempfile import TemporaryDirectory
import webbrowser

from aiohttp import web

ROOT = Path(__file__).resolve().parents[1]
USER_PREVIEW = ROOT / ".local/daily-preview"
sys.path.insert(0, str(ROOT))

from french_asr import FrenchEngine
from fluency_session import DEMO_PACK
from slot_session import DEMO_PACK as SLOT_PACK
from server import make_app
from speech_server import make_speech_app
from store import atomic_json


def installed_runtime(runtime_dir):
    sys.path.append(str(runtime_dir / ".whisper_deps"))
    bins = list((runtime_dir / ".gpu_deps/nvidia").glob("*/bin"))
    os.environ["PATH"] = os.pathsep.join([*map(str, bins), os.environ.get("PATH", "")])
    settings = {"model_path": runtime_dir / ".models/whisper-large-v3-french/ctranslate2",
                "alternate_model_path": runtime_dir / ".models/faster-whisper-large-v3-turbo"}
    engine = FrenchEngine(settings)
    if hasattr(os, "add_dll_directory"):
        engine.dll_handles.extend(os.add_dll_directory(str(path)) for path in bins)
    return engine


async def serve(args, data):
    if not (ROOT / ".desktop/desktop.html").is_file():
        raise RuntimeError("缺少桌面页面，请在项目目录执行 node scripts/build-oral.mjs")
    engine = installed_runtime(args.runtime_dir)
    if not engine.state["available"]:
        raise RuntimeError("未找到已安装的本机法语模型或依赖")
    if not args.disable_a and not DEMO_PACK.is_file():
        raise RuntimeError("缺少接拍串说课包，请运行 scripts/prepare_fluency_demo.py")
    if not args.disable_b and not SLOT_PACK.is_file():
        raise RuntimeError("缺少看提示换一格课包，请运行 scripts/prepare_slot_demo.py")
    if not args.disable_a or not args.disable_b:
        print("正在预热本机法语模型…", flush=True)
        await engine.warmup()
        sample = DEMO_PACK.parent / "s13-full.wav" if not args.disable_a else SLOT_PACK.parent / "slot-muscu.wav"
        await engine.transcribe(sample.read_bytes(), word_evidence=True)
        if not args.disable_b and (engine.alternate_path / "model.bin").is_file():
            try:
                await engine.transcribe_alternate_wav((SLOT_PACK.parent / "slot-muscu.wav").read_bytes())
            except (ValueError, RuntimeError) as exc:
                print(f"B 备用识别预热未完成：{exc}", flush=True)
    atomic_json(data / "daily-practice.json", {
        "fluency": {"enabled": not args.disable_a},
        "slot": {"enabled": not args.disable_b},
    })
    token = secrets.token_urlsafe(40)
    worker = web.AppRunner(make_speech_app(data, args.speech_port, engine, token), access_log=None)
    await worker.setup()
    try:
        await web.TCPSite(worker, "127.0.0.1", args.speech_port).start()
        app = make_app(data, args.port, cookie_name=f"oral_daily_preview_{args.port}",
                       game_private_assets=ROOT.parent / "assets-private" if args.game_private_assets else None)
        app["french_asr"].endpoint = f"http://127.0.0.1:{args.speech_port}"
        app["french_asr"].token = token
        runner = web.AppRunner(app, access_log=None)
        await runner.setup()
        try:
            await web.TCPSite(runner, "127.0.0.1", args.port).start()
            url = f"http://127.0.0.1:{args.port}/?desktop=1&daily=1"
            print(f"日常口语试玩已就绪  {url}", flush=True)
            print(f"独立数据目录  {data}", flush=True)
            if not args.no_browser:
                webbrowser.open(url)
            await asyncio.Event().wait()
        finally:
            await runner.cleanup()
    finally:
        await worker.cleanup()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--runtime-dir", type=Path, default=ROOT)
    parser.add_argument("--data-dir", type=Path, default=USER_PREVIEW)
    parser.add_argument("--port", type=int, default=18983)
    parser.add_argument("--speech-port", type=int, default=18984)
    parser.add_argument("--disable-a", action="store_true")
    parser.add_argument("--disable-b", action="store_true")
    parser.add_argument("--no-browser", action="store_true")
    parser.add_argument("--game-private-assets", action="store_true", help="仅在本机读取可用的游戏素材")
    parser.add_argument("--temporary-data", action="store_true")
    args = parser.parse_args()
    try:
        if args.temporary_data:
            scratch = ROOT / ".local/daily-tests"
            scratch.mkdir(parents=True, exist_ok=True)
            with TemporaryDirectory(prefix="test-", dir=scratch) as data:
                asyncio.run(serve(args, Path(data)))
        else:
            asyncio.run(serve(args, args.data_dir))
    except KeyboardInterrupt:
        pass
    except (RuntimeError, OSError) as exc:
        parser.exit(1, f"试玩启动失败：{exc}\n")


if __name__ == "__main__":
    main()
