import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support

// OSHL HUD: painel de monitoramento em tela cheia na area de trabalho.
// Dados: /usr/libexec/oshl-hud-stats (JSON, 1x/s). Cores: tema ativo (oshl-temas).
PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation

    property var s: ({})
    property var pal: ({ accent: "#aacfd1", bright: "#e6fbff", dim: "#24383c",
                         bg: "#05080d", bg2: "#0a1117", alert: "#ff5c5c" })
    property var cpuHist: []
    property var gpuHist: []
    property var rxHist: []
    property var txHist: []
    property var feed: []
    property int tick: 0
    property date now: new Date()
    readonly property int histLen: 120
    readonly property var meses: ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    readonly property var dias: ["DOMINGO", "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO"]

    // ---------- utilitarios ----------
    function g(path, def) {
        var o = s, parts = path.split(".")
        for (var i = 0; i < parts.length; i++) {
            if (o === undefined || o === null) return def
            o = o[parts[i]]
        }
        return (o === undefined || o === null) ? def : o
    }
    function pad(n) { return (n < 10 ? "0" : "") + n }
    function hms(d) { return pad(d.getHours()) + ":" + pad(d.getMinutes()) + ":" + pad(d.getSeconds()) }
    function bytes(b) {
        var u = ["B", "KB", "MB", "GB", "TB"], i = 0
        while (b >= 1024 && i < u.length - 1) { b /= 1024; i++ }
        return (i === 0 ? Math.round(b) : b.toFixed(1)) + " " + u[i]
    }
    function dur(sec) {
        var d = Math.floor(sec / 86400), h = Math.floor(sec % 86400 / 3600), m = Math.floor(sec % 3600 / 60)
        return (d > 0 ? d + "d " : "") + pad(h) + ":" + pad(m)
    }
    function shortModel() {
        return String(g("cpu.model", "CPU")).replace(/\(R\)|\(TM\)|CPU|Processor|@.*$/g, "").replace(/\s+/g, " ").trim()
    }
    function push(arr, v) {
        var a = arr.slice()
        a.push(v)
        while (a.length > histLen) a.shift()
        return a
    }
    function launch(cmd) { launcher.connectSource("setsid -f " + cmd + " >/dev/null 2>&1") }

    function update(d) {
        s = d
        if (d.palette && d.palette.accent) pal = d.palette
        cpuHist = push(cpuHist, d.cpu.total)
        gpuHist = push(gpuHist, d.gpu ? d.gpu.util : 0)
        rxHist = push(rxHist, d.net.rx)
        txHist = push(txHist, d.net.tx)

        tick++
        var t = "[" + hms(new Date()) + "] ", sp = "           ", L = feed.slice()
        L.push(t + "cpu " + d.cpu.total.toFixed(1) + "%  mem " + d.mem.pct.toFixed(1) + "%  load " + d.load.join(" "))
        if (tick % 2 === 0)
            L.push(sp + "net  rx " + bytes(d.net.rx) + "/s  tx " + bytes(d.net.tx) + "/s  if " + d.net.iface + "  ip " + d.net.ip)
        if (tick % 3 === 0 && d.procs.length)
            L.push(sp + "proc " + d.procs[0].name + "  pid " + d.procs[0].pid + "  cpu " + d.procs[0].cpu + "%")
        if (tick % 5 === 0)
            L.push(sp + (d.gpu ? "gpu  " + d.gpu.name + "  util " + d.gpu.util + "%  " + d.gpu.temp + "C  vram "
                                  + Math.round(d.gpu.memUsed) + "/" + Math.round(d.gpu.memTotal) + " MiB"
                               : "gpu  driver nvidia indisponivel"))
        if (tick % 7 === 0)
            L.push(sp + "disk r " + bytes(d.disk.read) + "/s  w " + bytes(d.disk.write) + "/s  uso " + d.disk.pct + "%")
        if (tick % 11 === 0)
            L.push(sp + "sec  firewall ativo  dns quad9/dot  rede " + (d.net.online ? "ONLINE" : "ISOLADA"))
        while (L.length > 80) L.shift()
        feed = L
    }

    // ---------- fontes de dados ----------
    P5Support.DataSource {
        id: stats
        engine: "executable"
        connectedSources: []
        onNewData: function (source, data) {
            stats.disconnectSource(source)
            try { root.update(JSON.parse(data["stdout"])) }
            catch (e) { console.warn("oshl-hud:", e) }
        }
    }
    P5Support.DataSource {
        id: launcher
        engine: "executable"
        connectedSources: []
        onNewData: function (source, data) { launcher.disconnectSource(source) }
    }
    Timer {
        interval: 1000
        running: true
        repeat: true
        triggeredOnStart: true
        onTriggered: {
            root.now = new Date()
            stats.connectSource("/usr/libexec/oshl-hud-stats")
        }
    }

    fullRepresentation: Item {
        id: hud
        Layout.minimumWidth: 640
        Layout.minimumHeight: 400
        clip: true

        readonly property var t: root.pal
        readonly property real u: Math.max(0.5, Math.min(width / 1920, height / 1030))
        readonly property real gap: Math.round(14 * u)
        readonly property real sideW: Math.round(width * 0.215)
        readonly property real barH: Math.round(46 * u)
        readonly property real colH: height - barH - 3 * gap

        // ================= COLUNA ESQUERDA =================
        Column {
            id: left
            x: hud.gap
            y: hud.gap
            width: hud.sideW
            height: hud.colH
            spacing: hud.gap
            clip: true

            Panel {
                t: hud.t; u: hud.u
                title: "PAINEL"; tag: "SISTEMA"
                width: parent.width; height: 150 * hud.u
                Text {
                    id: clock
                    text: root.hms(root.now)
                    color: hud.t.bright
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(54 * hud.u)
                    font.letterSpacing: 4 * hud.u
                }
                Row {
                    anchors.top: clock.bottom
                    anchors.topMargin: 6 * hud.u
                    spacing: 18 * hud.u
                    InfoCell { t: hud.t; u: hud.u; label: String(root.now.getFullYear()); value: root.meses[root.now.getMonth()] + " " + root.pad(root.now.getDate()) }
                    InfoCell { t: hud.t; u: hud.u; label: "UPTIME"; value: root.dur(root.g("uptime", 0)) }
                    InfoCell { t: hud.t; u: hud.u; label: "TIPO"; value: "OSHL" }
                    InfoCell { t: hud.t; u: hud.u; label: "ENERGIA"; value: root.g("battery", null) === null ? "AC" : root.g("battery", 0) + "%" }
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "USO DE CPU"; tag: root.shortModel()
                width: parent.width; height: 240 * hud.u
                Graph { id: cpuG; t: hud.t; width: parent.width; height: parent.height * 0.42; values: root.cpuHist; capacity: root.histLen }
                Row {
                    id: coreRow
                    readonly property var cores: root.g("cpu.cores", [])
                    anchors.top: cpuG.bottom
                    anchors.topMargin: 8 * hud.u
                    width: parent.width
                    height: parent.height * 0.26
                    spacing: 2
                    Repeater {
                        model: coreRow.cores
                        Item {
                            width: Math.max(2, (coreRow.width - coreRow.spacing * (coreRow.cores.length - 1)) / Math.max(1, coreRow.cores.length))
                            height: coreRow.height
                            Rectangle { anchors.fill: parent; color: "transparent"; border.color: hud.t.dim; border.width: 1 }
                            Rectangle {
                                anchors.bottom: parent.bottom
                                width: parent.width
                                height: parent.height * Math.min(100, modelData) / 100
                                color: hud.t.accent
                                opacity: 0.85
                            }
                        }
                    }
                }
                Row {
                    anchors.bottom: parent.bottom
                    spacing: 18 * hud.u
                    InfoCell { t: hud.t; u: hud.u; label: "TEMP"; value: root.g("cpu.temp", null) === null ? "--" : root.g("cpu.temp", 0) + "°C"; alert: root.g("cpu.temp", 0) > 85 }
                    InfoCell { t: hud.t; u: hud.u; label: "CARGA"; value: root.g("load", ["0"])[0] }
                    InfoCell { t: hud.t; u: hud.u; label: "TAREFAS"; value: String(root.g("tasks", 0)) }
                    InfoCell { t: hud.t; u: hud.u; label: "THREADS"; value: String(root.g("threads", 0)) }
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "MEMORIA"
                tag: "USANDO " + (root.g("mem.used", 0) / 1073741824).toFixed(1) + " DE " + (root.g("mem.total", 0) / 1073741824).toFixed(1) + " GiB"
                width: parent.width; height: 140 * hud.u
                MemGrid { id: memGrid; t: hud.t; u: hud.u; width: parent.width; height: parent.height - 22 * hud.u; ratio: root.g("mem.pct", 0) / 100 }
                Text {
                    anchors.bottom: parent.bottom
                    text: "SWAP " + root.bytes(root.g("mem.swapUsed", 0)) + " / " + root.bytes(root.g("mem.swapTotal", 0)) + "   USO " + root.g("mem.pct", 0) + "%"
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(11 * hud.u)
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "TOP PROCESSOS"; tag: "PID | NOME | CPU | MEM"
                width: parent.width
                height: Math.max(80, hud.colH - (150 + 240 + 140) * hud.u - 3 * hud.gap)
                Column {
                    width: parent.width
                    spacing: 3 * hud.u
                    Repeater {
                        model: root.g("procs", [])
                        Row {
                            width: parent.width
                            Text { width: parent.width * 0.2; text: modelData.pid; color: hud.t.accent; opacity: 0.7; font.family: "Fira Mono"; font.pixelSize: Math.round(12 * hud.u) }
                            Text { width: parent.width * 0.46; text: modelData.name; elide: Text.ElideRight; color: hud.t.bright; font.family: "Fira Mono"; font.pixelSize: Math.round(12 * hud.u) }
                            Text { width: parent.width * 0.17; text: modelData.cpu + "%"; color: hud.t.accent; font.family: "Fira Mono"; font.pixelSize: Math.round(12 * hud.u) }
                            Text { width: parent.width * 0.17; text: modelData.mem + "%"; color: hud.t.accent; font.family: "Fira Mono"; font.pixelSize: Math.round(12 * hud.u) }
                        }
                    }
                }
            }
        }

        // ================= COLUNA CENTRAL =================
        Item {
            id: center
            x: left.x + left.width + hud.gap
            y: hud.gap
            width: hud.width - 2 * hud.sideW - 4 * hud.gap
            height: hud.colH

            Item {
                id: head
                width: parent.width
                height: 30 * hud.u
                Text {
                    anchors.verticalCenter: parent.verticalCenter
                    text: "OSHL  //  NEURAL SHELL"
                    color: hud.t.bright
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(18 * hud.u)
                    font.letterSpacing: 5 * hud.u
                }
                Text {
                    anchors.right: parent.right
                    anchors.verticalCenter: parent.verticalCenter
                    text: "HOST " + root.g("info.host", "-") + "   KERNEL " + root.g("info.kernel", "-") + "   TEMA " + root.g("themeName", "TRON")
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(11 * hud.u)
                }
                Rectangle { anchors.bottom: parent.bottom; width: parent.width; height: 1; color: hud.t.accent; opacity: 0.6 }
            }

            Panel {
                id: core
                t: hud.t; u: hud.u
                anchors.top: head.bottom
                anchors.topMargin: hud.gap
                width: parent.width
                height: parent.height * 0.44
                title: "NUCLEO"; tag: "MONITOR EM TEMPO REAL"

                Row {
                    id: gauges
                    width: parent.width
                    height: parent.height * 0.68
                    spacing: 14 * hud.u
                    readonly property real ring: Math.min(height, (width - 4 * spacing) / 5.2)
                    Ring {
                        t: hud.t; u: hud.u; width: gauges.ring; height: gauges.ring
                        value: root.now.getDate() / new Date(root.now.getFullYear(), root.now.getMonth() + 1, 0).getDate() * 100
                        center: root.pad(root.now.getDate())
                        sub: root.meses[root.now.getMonth()]
                        label: root.dias[root.now.getDay()]
                    }
                    Ring { t: hud.t; u: hud.u; width: gauges.ring; height: gauges.ring; value: root.g("cpu.total", 0); label: "CPU" }
                    Ring { t: hud.t; u: hud.u; width: gauges.ring; height: gauges.ring; value: root.g("mem.pct", 0); label: "RAM" }
                    Ring {
                        t: hud.t; u: hud.u; width: gauges.ring; height: gauges.ring
                        value: root.g("gpu.util", 0)
                        center: root.g("gpu", null) ? Math.round(root.g("gpu.util", 0)) + "%" : "N/D"
                        label: "GPU"
                    }
                    Bars {
                        t: hud.t; u: hud.u
                        width: Math.max(60, gauges.width - 4 * (gauges.ring + gauges.spacing))
                        height: gauges.height
                        items: [
                            { label: "CPU", value: root.g("cpu.total", 0) },
                            { label: "RAM", value: root.g("mem.pct", 0) },
                            { label: "GPU", value: root.g("gpu.util", 0) },
                            { label: "VRAM", value: root.g("gpu", null) ? 100 * root.g("gpu.memUsed", 0) / Math.max(1, root.g("gpu.memTotal", 1)) : 0 },
                            { label: "DISCO", value: root.g("disk.pct", 0) }
                        ]
                    }
                }

                Row {
                    id: clockRings
                    anchors.top: gauges.bottom
                    anchors.topMargin: 8 * hud.u
                    width: parent.width
                    height: parent.height - gauges.height - 8 * hud.u
                    spacing: 14 * hud.u
                    Ring { t: hud.t; u: hud.u; width: clockRings.height; height: clockRings.height; value: root.now.getHours() / 24 * 100; center: root.pad(root.now.getHours()); label: "HORA" }
                    Ring { t: hud.t; u: hud.u; width: clockRings.height; height: clockRings.height; value: root.now.getMinutes() / 60 * 100; center: root.pad(root.now.getMinutes()); label: "MIN" }
                    Ring { t: hud.t; u: hud.u; width: clockRings.height; height: clockRings.height; value: root.now.getSeconds() / 60 * 100; center: root.pad(root.now.getSeconds()); label: "SEG" }
                    Grid {
                        anchors.verticalCenter: parent.verticalCenter
                        columns: 3
                        columnSpacing: 22 * hud.u
                        rowSpacing: 6 * hud.u
                        InfoCell { t: hud.t; u: hud.u; label: "GPU"; value: root.g("gpu.name", "N/D") }
                        InfoCell { t: hud.t; u: hud.u; label: "TEMP GPU"; value: root.g("gpu", null) ? Math.round(root.g("gpu.temp", 0)) + "°C" : "--"; alert: root.g("gpu.temp", 0) > 83 }
                        InfoCell { t: hud.t; u: hud.u; label: "POTENCIA"; value: root.g("gpu", null) ? Math.round(root.g("gpu.power", 0)) + " W" : "--" }
                        InfoCell { t: hud.t; u: hud.u; label: "VRAM"; value: root.g("gpu", null) ? (root.g("gpu.memUsed", 0) / 1024).toFixed(1) + " / " + (root.g("gpu.memTotal", 0) / 1024).toFixed(1) + " GB" : "--" }
                        InfoCell { t: hud.t; u: hud.u; label: "DISCO"; value: (root.g("disk.used", 0) / 1073741824).toFixed(0) + " / " + (root.g("disk.total", 0) / 1073741824).toFixed(0) + " GB" }
                        InfoCell { t: hud.t; u: hud.u; label: "USUARIO"; value: String(root.g("info.user", "-")).toUpperCase() }
                    }
                }
            }

            Panel {
                id: term
                t: hud.t; u: hud.u
                anchors.top: core.bottom
                anchors.topMargin: hud.gap
                anchors.bottom: parent.bottom
                width: parent.width
                title: "TERMINAL"; tag: "SHELL PRINCIPAL"

                Row {
                    id: tabs
                    width: parent.width
                    height: 30 * hud.u
                    spacing: 4 * hud.u
                    Repeater {
                        model: ["MAIN - oshl", "REDE", "GPU", "LOG", "VAZIO"]
                        Rectangle {
                            width: (tabs.width - 4 * tabs.spacing) / 5
                            height: tabs.height
                            color: index === 0 ? hud.t.accent : "transparent"
                            border.color: hud.t.accent
                            border.width: 1
                            opacity: index === 0 ? 1 : 0.6
                            Text {
                                anchors.centerIn: parent
                                text: modelData
                                color: index === 0 ? hud.t.bg : hud.t.accent
                                font.family: "Fira Mono"
                                font.pixelSize: Math.round(14 * hud.u)
                            }
                        }
                    }
                }
                Text {
                    anchors.top: tabs.bottom
                    anchors.topMargin: 8 * hud.u
                    anchors.bottom: parent.bottom
                    width: parent.width
                    clip: true
                    verticalAlignment: Text.AlignBottom
                    text: root.feed.join("\n")
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(13 * hud.u)
                }
            }
        }

        // ================= COLUNA DIREITA =================
        Column {
            id: right
            x: hud.width - hud.sideW - hud.gap
            y: hud.gap
            width: hud.sideW
            height: hud.colH
            spacing: hud.gap
            clip: true

            Panel {
                t: hud.t; u: hud.u
                title: "STATUS DA REDE"; tag: "REDE"
                width: parent.width; height: 112 * hud.u
                Grid {
                    columns: 3
                    columnSpacing: 20 * hud.u
                    rowSpacing: 6 * hud.u
                    InfoCell { t: hud.t; u: hud.u; label: "ESTADO"; value: root.g("net.online", false) ? "ONLINE" : "ISOLADA" }
                    InfoCell { t: hud.t; u: hud.u; label: "IPv4"; value: root.g("net.ip", "-") }
                    InfoCell { t: hud.t; u: hud.u; label: "INTERFACE"; value: root.g("net.iface", "-") }
                    InfoCell { t: hud.t; u: hud.u; label: "DNS"; value: "QUAD9 DoT" }
                    InfoCell { t: hud.t; u: hud.u; label: "FIREWALL"; value: "ATIVO" }
                    InfoCell { t: hud.t; u: hud.u; label: "HOST"; value: root.g("info.host", "-") }
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "VISAO GLOBAL"; tag: "MAPA DE REDE"
                width: parent.width; height: 240 * hud.u
                Globe { t: hud.t; anchors.fill: parent }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "TRAFEGO DE REDE"
                tag: "DOWN " + root.bytes(root.g("net.rx", 0)) + "/s  UP " + root.bytes(root.g("net.tx", 0)) + "/s"
                width: parent.width; height: 150 * hud.u
                Graph { t: hud.t; width: parent.width; height: parent.height - 20 * hud.u; values: root.rxHist; values2: root.txHist; autoMax: true; capacity: root.histLen }
                Text {
                    anchors.bottom: parent.bottom
                    text: "TOTAL  IN " + root.bytes(root.g("net.rxTotal", 0)) + "   OUT " + root.bytes(root.g("net.txTotal", 0))
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(11 * hud.u)
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "GPU"; tag: root.g("gpu.name", "NVIDIA")
                width: parent.width; height: 150 * hud.u
                Graph { t: hud.t; width: parent.width; height: parent.height - 20 * hud.u; values: root.gpuHist; capacity: root.histLen }
                Text {
                    anchors.bottom: parent.bottom
                    text: root.g("gpu", null) ? "UTIL " + Math.round(root.g("gpu.util", 0)) + "%   " + Math.round(root.g("gpu.temp", 0)) + "°C   " + Math.round(root.g("gpu.power", 0)) + " W"
                                              : "DRIVER NVIDIA INDISPONIVEL"
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(11 * hud.u)
                }
            }

            Panel {
                t: hud.t; u: hud.u
                title: "ARMAZENAMENTO"; tag: "USO " + root.g("disk.pct", 0) + "%"
                width: parent.width
                height: Math.max(70, hud.colH - (112 + 240 + 150 + 150) * hud.u - 4 * hud.gap)
                Rectangle {
                    id: diskBar
                    width: parent.width
                    height: 10 * hud.u
                    color: "transparent"
                    border.color: hud.t.dim
                    border.width: 1
                    Rectangle {
                        x: 2; y: 2
                        height: parent.height - 4
                        width: Math.max(0, (parent.width - 4) * root.g("disk.pct", 0) / 100)
                        color: hud.t.accent
                    }
                }
                Text {
                    anchors.top: diskBar.bottom
                    anchors.topMargin: 8 * hud.u
                    text: "LEITURA " + root.bytes(root.g("disk.read", 0)) + "/s   ESCRITA " + root.bytes(root.g("disk.write", 0)) + "/s"
                    color: hud.t.accent
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(11 * hud.u)
                }
            }
        }

        // ================= BARRA DE COMANDOS =================
        Row {
            id: cmdBar
            x: hud.gap
            y: hud.height - hud.barH - hud.gap
            width: hud.width - 2 * hud.gap
            height: hud.barH
            spacing: 8 * hud.u
            readonly property var cmds: [
                { label: "TEMAS", cmd: "oshl-temas" },
                { label: "TERMINAL", cmd: "konsole" },
                { label: "ARQUIVOS", cmd: "dolphin" },
                { label: "MUSICA", cmd: "strawberry" },
                { label: "VIDEO", cmd: "vlc" },
                { label: "JOGOS", cmd: "steam" },
                { label: "NAVEGADOR", cmd: "oshl-browser" },
                { label: "BUSCAR", cmd: "krunner" },
                { label: "ATUALIZAR", cmd: "oshl-atualizar" },
                { label: "CONFIG", cmd: "systemsettings" }
            ]
            Repeater {
                model: cmdBar.cmds
                HudButton {
                    t: hud.t; u: hud.u
                    width: (cmdBar.width - cmdBar.spacing * (cmdBar.cmds.length - 1)) / cmdBar.cmds.length
                    height: cmdBar.height
                    label: modelData.label
                    onActivated: root.launch(modelData.cmd)
                }
            }
        }
    }
}
