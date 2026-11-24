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
USER_SONS = os.environ.get("OSHL_SONS") or os.path.expanduser("~/.local/share/oshl/sons")
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
    statsChanged = Signal()

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
        self._stats = {"cpu": 0, "gpu": 0, "ram": 0, "disk": 0, "temp": 0, "cpuTemp": 0, "gpuTemp": 0,
                       "vramUsed": 0, "vramTotal": 0, "rx": 0, "tx": 0, "gpuName": "", "real": False}
        self._sim = 0.0
        self._timer = QTimer()
        self._timer.timeout.connect(self._update_stats)
        self._timer.start(1500)
        self._update_stats()
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

    def _update_stats(self):
        """Dados reais (oshl-hud-stats, no OSHL) ou simulados (teste no Windows)."""
        exe = "/usr/libexec/oshl-hud-stats"
        if os.path.exists(exe):
            try:
                d = json.loads(subprocess.run([exe], capture_output=True, text=True, timeout=3).stdout)
                g = d.get("gpu") or {}
                self._stats = {"cpu": d["cpu"]["total"], "gpu": g.get("util", 0), "ram": d["mem"]["pct"],
                               "disk": d["disk"]["pct"], "temp": d["cpu"].get("temp") or g.get("temp") or 0,
                               "cpuTemp": d["cpu"].get("temp") or 0, "gpuTemp": g.get("temp", 0),
                               "vramUsed": g.get("memUsed", 0), "vramTotal": g.get("memTotal", 0),
                               "rx": d["net"]["rx"], "tx": d["net"]["tx"], "gpuName": g.get("name", ""), "real": True}
                self.statsChanged.emit()
                return
            except (OSError, ValueError, KeyError, subprocess.SubprocessError):
                pass
        import math
        self._sim += 1
        s = self._sim
        self._stats = {"cpu": 35 + 25 * math.sin(s / 3), "gpu": 55 + 30 * math.sin(s / 5 + 1), "ram": 48 + 4 * math.sin(s / 7),
                       "disk": 71, "temp": 58 + 6 * math.sin(s / 4), "rx": 12.4e6 * (1 + math.sin(s / 2)) / 2,
                       "tx": 1.3e6 * (1 + math.cos(s / 3)) / 2, "gpuName": "RTX 30", "real": False,
                       "cpuTemp": 52 + 6 * math.sin(s / 4), "gpuTemp": 61 + 5 * math.sin(s / 6),
                       "vramUsed": 5300 + 400 * math.sin(s / 5), "vramTotal": 10240}
        self.statsChanged.emit()

    def _get_stats(self):
        return self._stats

    stats = Property("QVariant", _get_stats, notify=statsChanged)

    widgetsChanged = Signal()

    def _wfile(self):
        return os.path.join(CONF, "dashboard-widgets.json")

    def _get_widgets(self):
        try:
            return json.load(open(self._wfile(), encoding="utf-8"))
        except (OSError, ValueError):
            return {}

    widgets = Property("QVariant", _get_widgets, notify=widgetsChanged)

    @Slot(str, bool)
    def setWidget(self, name, on):
        w = self._get_widgets()
        w[name] = on
        os.makedirs(CONF, exist_ok=True)
        json.dump(w, open(self._wfile(), "w", encoding="utf-8"))
        self.widgetsChanged.emit()

    @Slot()
    def showAllWidgets(self):
        try:
            os.remove(self._wfile())
        except OSError:
            pass
        self.widgetsChanged.emit()

    def _get_pivots(self):
        try:
            return json.load(open(os.path.join(ASSETS, "widgets", "pivots.json"), encoding="utf-8"))
        except (OSError, ValueError):
            return {"hand-hour": {"pivot_x": 0.5, "pivot_y": 0.70}, "hand-min": {"pivot_x": 0.5, "pivot_y": 0.688}}

    pivots = Property("QVariant", _get_pivots, constant=True)

    menuStyleChanged = Signal()

    def _get_menu_style(self):
        try:
            v = open(os.path.join(CONF, "dashboard-estilo"), encoding="utf-8").read().strip()
        except OSError:
            v = ""
        return v if v in ("vidro", "classico") else "classico"

    menuStyle = Property(str, _get_menu_style, notify=menuStyleChanged)

    @Slot()
    def toggleMenuStyle(self):
        new = "vidro" if self._get_menu_style() == "classico" else "classico"
        os.makedirs(CONF, exist_ok=True)
        open(os.path.join(CONF, "dashboard-estilo"), "w", encoding="utf-8").write(new)
        self.menuStyleChanged.emit()

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
        # sons do usuario (pacote no pendrive) tem prioridade: ~/.local/share/oshl/sons/<nome>.wav
        wav = os.path.join(USER_SONS, name + ".wav")
        if not os.path.exists(wav):
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
    engine.rootContext().setContextProperty("deskMode", os.environ.get("OSHL_MODO") == "area")
    engine.rootContext().setContextProperty("previewPath", os.environ.get("OSHL_PREVIEW", ""))
    sim = os.environ.get("OSHL_SIM_QML", "")
    engine.rootContext().setContextProperty("simPath", QUrl.fromLocalFile(sim).toString() if sim else "")
    engine.rootContext().setContextProperty("simIcons", QUrl.fromLocalFile(os.environ.get("OSHL_SIM_ICONS", "")).toString())
    engine.load(QUrl.fromLocalFile(os.path.join(HERE, "Dashboard.qml")))
    if not engine.rootObjects():
        sys.exit(1)
    threading.Thread(target=gamepad_loop, args=(backend,), daemon=True).start()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
