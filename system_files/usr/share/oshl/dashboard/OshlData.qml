import QtQuick
import org.kde.plasma.plasma5support as P5Support

// Dados compartilhados pelos widgets OSHL da area de trabalho (so roda dentro do Plasma):
// cores do tema ativo, estatisticas (oshl-hud-stats), menus, estilo do menu, abrir programas e sons.
Item {
    id: d
    property var pal: ({ accent: "#b9e52b", bright: "#f3ff8f", dim: "#2d4a0a", bg: "#060c02", bg2: "#0f1a05", tint: false })
    property var stats: ({ cpu: 0, gpu: 0, ram: 0, disk: 0, temp: 0, cpuTemp: 0, gpuTemp: 0, vramUsed: 0, vramTotal: 0, rx: 0, tx: 0, gpuName: "GPU" })
    property var menus: []
    property bool vidro: false
    property bool wantStats: true
    property bool wantMenus: false
    readonly property string fam: "Orbitron"
    readonly property string assetDir: "file:///usr/share/oshl/orbital/"
    readonly property string statsCmd: "/usr/libexec/oshl-hud-stats"
    readonly property string menusCmd: "cat /usr/share/oshl/dashboard/menus.json"
    readonly property string styleCmd: "cat \"${XDG_CONFIG_HOME:-$HOME/.config}/oshl/dashboard-estilo\" 2>/dev/null || echo classico"

    function asset(n) { return assetDir + n }
    function q(s) { return "'" + String(s).replace(/'/g, "'\''") + "'" }
    function run(cmd) { exe.connectSource(cmd) }
    function launch(cmd) { run("setsid -f sh -c " + q(cmd) + " >/dev/null 2>&1") }
    function sound(n) {
        run("f=\"${XDG_DATA_HOME:-$HOME/.local/share}/oshl/sons/" + n + ".wav\"; [ -f \"$f\" ] && setsid -f pw-play \"$f\" >/dev/null 2>&1; true")
    }
    function toggleStyle() {
        vidro = !vidro
        run("mkdir -p \"${XDG_CONFIG_HOME:-$HOME/.config}/oshl\" && echo " + (vidro ? "vidro" : "classico")
            + " > \"${XDG_CONFIG_HOME:-$HOME/.config}/oshl/dashboard-estilo\"")
    }

    // "MOSTRAR WIDGETS" so faz sentido no Painel em tela cheia: some dos widgets
    function cleanMenus(list) {
        return list.filter(function (e) { return e.action !== "widgets" }).map(function (e) {
            if (!e.items) return e
            var c = {}; for (var k in e) c[k] = e[k]
            c.items = cleanMenus(e.items)
            return c
        })
    }
    function parseStats(txt) {
        var j = JSON.parse(txt), g = j.gpu || {}
        if (j.palette && j.palette.accent) {
            var p = j.palette
            pal = { accent: p.accent, bright: p.bright, dim: p.dim, bg: p.bg, bg2: p.bg2,
                    tint: !(j.theme === "orbital" || j.theme === "matrix"), key: j.theme }
        }
        stats = { cpu: j.cpu.total, gpu: g.util || 0, ram: j.mem.pct, disk: j.disk.pct,
                  temp: j.cpu.temp || g.temp || 0, cpuTemp: j.cpu.temp || 0, gpuTemp: g.temp || 0,
                  vramUsed: g.memUsed || 0, vramTotal: g.memTotal || 0, rx: j.net.rx, tx: j.net.tx,
                  gpuName: String(g.name || "GPU").replace(/NVIDIA |GeForce /g, "") }
    }

    P5Support.DataSource {
        id: exe
        engine: "executable"
        connectedSources: []
        onNewData: function (src, data) {
            exe.disconnectSource(src)
            var out = data["stdout"] || ""
            try {
                if (src === d.statsCmd) d.parseStats(out)
                else if (src === d.menusCmd) d.menus = d.cleanMenus(JSON.parse(out))
                else if (src === d.styleCmd) d.vidro = out.trim() === "vidro"
            } catch (e) { console.warn("oshl:", src, e) }
        }
    }
    Timer {
        interval: 2000; running: d.wantStats; repeat: true; triggeredOnStart: true
        onTriggered: exe.connectSource(d.statsCmd)
    }
    Component.onCompleted: {
        exe.connectSource(d.styleCmd)
        if (d.wantMenus) exe.connectSource(d.menusCmd)
    }
}
