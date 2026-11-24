#!/usr/bin/python3
"""Dashboard OSHL: tela cheia com menu de esferas e capsulas (mouse, teclado e controle).
Variaveis de teste: OSHL_ORBITAL (pasta dos assets), OSHL_FONT (arquivo .ttf),
OSHL_PREVIEW=arquivo.png (salva uma imagem e sai), OSHL_THEME (forca o tema)."""
import json
import os
import subprocess
import sys
import threading
import time

from PySide6.QtCore import Property, QObject, QTimer, QUrl, Signal, Slot, qInstallMessageHandler
from PySide6.QtGui import QFontDatabase, QGuiApplication
from PySide6.QtQml import QQmlApplicationEngine

HERE = os.path.dirname(os.path.abspath(__file__))
ASSETS = os.environ.get("OSHL_ORBITAL", "/usr/share/oshl/orbital")
THEMES = os.environ.get("OSHL_THEMES", "/usr/share/oshl/themes.json")
FONT = os.environ.get("OSHL_FONT", "/usr/share/fonts/oshl/Orbitron.ttf")
CONF = os.path.join(os.environ.get("XDG_CONFIG_HOME") or os.path.expanduser("~/.config"), "oshl")
# Papeis de parede: os do sistema + a pasta do usuario (pacote WALLPAPERS-OSHL ou copiados a mao)
USER_WALL = os.environ.get("OSHL_WALLPAPERS") or os.path.join(
    os.environ.get("XDG_DATA_HOME") or os.path.expanduser("~/.local/share"), "oshl", "wallpapers")
IMG_EXT = (".jpg", ".jpeg", ".png", ".webp")


def list_wallpapers():
    found = [os.path.join(ASSETS, n) for n in ("bg.jpg", "bg-malha.jpg") if os.path.exists(os.path.join(ASSETS, n))]
    if os.path.isdir(USER_WALL):
        found += sorted(os.path.join(USER_WALL, n) for n in os.listdir(USER_WALL) if n.lower().endswith(IMG_EXT))
    return found


def load_palette():
    key = os.environ.get("OSHL_THEME")
    if not key:
        try:
            key = open(os.path.join(CONF, "theme"), encoding="utf-8").read().strip()
        except OSError:
            key = "orbital"
    try:
        themes = json.load(open(THEMES, encoding="utf-8"))
    except (OSError, ValueError):
        themes = {}
    t = themes.get(key) or themes.get("orbital") or {
        "accent": "#9be22d", "bright": "#efff9a", "dim": "#1f4d0c", "bg": "#020c03", "bg2": "#071a06"}
    pal = {k: t.get(k, "#9be22d") for k in ("accent", "bright", "dim", "bg", "bg2")}
    pal["key"] = key
    pal["tint"] = key not in ("orbital", "matrix")
    return pal


class Backend(QObject):
    padUp = Signal()
    padDown = Signal()
    padLeft = Signal()
    padRight = Signal()
    padA = Signal()
    padB = Signal()
    padY = Signal()
    wallpaperChanged = Signal()

    def __init__(self, app):
        super().__init__()
        self._app = app
        self._pal = load_palette()
        self._menus = json.load(open(os.path.join(HERE, "menus.json"), encoding="utf-8"))
        self._walls = list_wallpapers()
        try:
            saved = open(os.path.join(CONF, "dashboard-wallpaper"), encoding="utf-8").read().strip()
        except OSError:
            saved = ""
        self._wall = saved if saved in self._walls else (self._walls[0] if self._walls else "")
        self._font = "Sans Serif"
        if os.path.exists(FONT):
            fid = QFontDatabase.addApplicationFont(FONT)
            fams = QFontDatabase.applicationFontFamilies(fid) if fid >= 0 else []
            if fams:
                self._font = fams[0]

    def _get_pal(self):
        return self._pal

    def _get_menus(self):
        return self._menus

    def _get_font(self):
        return self._font

    def _get_test(self):
        return bool(os.environ.get("OSHL_TESTE"))

    testMode = Property(bool, _get_test, constant=True)

    def _get_janela(self):
        return bool(os.environ.get("OSHL_JANELA")) or "--janela" in sys.argv

    windowMode = Property(bool, _get_janela, constant=True)

    def _get_wall(self):
        return QUrl.fromLocalFile(self._wall).toString() if self._wall else ""

    wallpaper = Property(str, _get_wall, notify=wallpaperChanged)

    def _get_wall_info(self):
        n = len(self._walls)
        i = self._walls.index(self._wall) + 1 if self._wall in self._walls else 0
        return f"{i}/{n}"

    wallpaperInfo = Property(str, _get_wall_info, notify=wallpaperChanged)

    @Slot()
    def nextWallpaper(self):
        self._walls = list_wallpapers() or self._walls
        if not self._walls:
            return
        i = self._walls.index(self._wall) if self._wall in self._walls else -1
        self._wall = self._walls[(i + 1) % len(self._walls)]
        try:
            os.makedirs(CONF, exist_ok=True)
            open(os.path.join(CONF, "dashboard-wallpaper"), "w", encoding="utf-8").write(self._wall)
        except OSError:
            pass
        self.wallpaperChanged.emit()
    palette = Property("QVariant", _get_pal, constant=True)
    menus = Property("QVariant", _get_menus, constant=True)
    fontFamily = Property(str, _get_font, constant=True)

    @Slot(str, result=str)
    def asset(self, name):
        return QUrl.fromLocalFile(os.path.join(ASSETS, name)).toString()

    @Slot(str)
    def launch(self, cmd):
        subprocess.Popen(["sh", "-c", cmd], start_new_session=True,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

    @Slot(str)
    def sound(self, name):
        wav = os.path.join(ASSETS, name + ".wav")
        if os.path.exists(wav) and os.name == "nt":          # teste no Windows
            import winsound
            winsound.PlaySound(wav, winsound.SND_FILENAME | winsound.SND_ASYNC | winsound.SND_NODEFAULT)
            return
        if os.path.exists(wav):
            for player in ("pw-play", "paplay", "aplay"):
                try:
                    subprocess.Popen([player, wav], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    return
                except OSError:
                    continue

    @Slot()
    def quit(self):
        self._app.quit()


def gamepad_loop(backend):
    """Le controles (Xbox/PlayStation/genericos) via evdev e emite sinais para a interface."""
    try:
        import evdev
        from evdev import ecodes as E
    except ImportError:
        return
    import selectors
    sel = selectors.DefaultSelector()
    devs, last_scan, stick = {}, 0.0, {}
    keymap = {E.BTN_SOUTH: backend.padA, E.BTN_EAST: backend.padB,
              E.BTN_NORTH: backend.padY, E.BTN_WEST: backend.padY,
              E.BTN_DPAD_UP: backend.padUp, E.BTN_DPAD_DOWN: backend.padDown,
              E.BTN_DPAD_LEFT: backend.padLeft, E.BTN_DPAD_RIGHT: backend.padRight}
    while True:
        if time.time() - last_scan > 3:
            last_scan = time.time()
            for path in evdev.list_devices():
                if path in devs:
                    continue
                try:
                    d = evdev.InputDevice(path)
                    if E.BTN_SOUTH in d.capabilities().get(E.EV_KEY, []):
                        devs[path] = d
                        sel.register(d, selectors.EVENT_READ)
                except OSError:
                    continue
        if not devs:
            time.sleep(1)
            continue
        for key, _ in sel.select(timeout=1):
            d = key.fileobj
            try:
                for ev in d.read():
                    if ev.type == E.EV_KEY and ev.value == 1 and ev.code in keymap:
                        keymap[ev.code].emit()
                    elif ev.type == E.EV_ABS and ev.code in (E.ABS_HAT0X, E.ABS_HAT0Y):
                        if ev.value:
                            {(E.ABS_HAT0Y, -1): backend.padUp, (E.ABS_HAT0Y, 1): backend.padDown,
                             (E.ABS_HAT0X, -1): backend.padLeft, (E.ABS_HAT0X, 1): backend.padRight}[(ev.code, ev.value)].emit()
                    elif ev.type == E.EV_ABS and ev.code in (E.ABS_X, E.ABS_Y):
                        info = d.absinfo(ev.code)
                        span = (info.max - info.min) / 2 or 1
                        v = (ev.value - (info.max + info.min) / 2) / span
                        state = -1 if v < -0.6 else (1 if v > 0.6 else 0)
                        k = (d.path, ev.code)
                        if state and stick.get(k) != state:
                            {(E.ABS_Y, -1): backend.padUp, (E.ABS_Y, 1): backend.padDown,
                             (E.ABS_X, -1): backend.padLeft, (E.ABS_X, 1): backend.padRight}[(ev.code, state)].emit()
                        stick[k] = state
            except OSError:
                sel.unregister(d)
                devs.pop(d.path, None)


def main():
    qInstallMessageHandler(lambda mode, ctx, msg: print(msg, file=sys.stderr, flush=True))
    app = QGuiApplication(sys.argv)
    app.setApplicationName("oshl-dashboard")
    app.setDesktopFileName("oshl-dashboard")
    backend = Backend(app)
    engine = QQmlApplicationEngine()
    engine.rootContext().setContextProperty("backend", backend)
    engine.rootContext().setContextProperty("previewMode", bool(os.environ.get("OSHL_PREVIEW")))
    engine.rootContext().setContextProperty("previewPath", os.environ.get("OSHL_PREVIEW", ""))
    engine.load(QUrl.fromLocalFile(os.path.join(HERE, "Dashboard.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    threading.Thread(target=gamepad_loop, args=(backend,), daemon=True).start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
