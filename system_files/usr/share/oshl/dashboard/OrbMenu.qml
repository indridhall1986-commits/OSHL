import QtQuick
import QtQuick.Shapes
import QtQuick.Effects

// Menu OSHL (esfera + menu em carrossel) como peca independente, usada pelo widget da area de trabalho.
// Nao depende do "backend" do Dashboard: quem usa fornece cores, menus e trata os sinais.
Item {
    id: m
    // ---- entradas
    property var pal: ({ accent: "#b9e52b", bright: "#f3ff8f", dim: "#2d4a0a", bg: "#060c02", bg2: "#0f1a05", tint: false })
    property string fam: ""
    property var menus: []
    property bool vidro: false                    // estilo VIDRO (1a versao) ou CLASSICO
    property string assetDir: "file:///usr/share/oshl/orbital/"
    // ---- saidas
    signal launchReq(string cmd, string label)
    signal soundReq(string name)
    signal actionReq(string name)

    function asset(n) { return assetDir + n }
    function al(c, a) { var q = Qt.lighter(c, 1.0); return Qt.rgba(q.r, q.g, q.b, a) }

    // geometria: tudo proporcional ao tamanho do widget
    readonly property real u: Math.min(width / 1000, height / 640)
    readonly property real coreSize: height * (vidro ? 0.66 : 0.80)
    readonly property real coreR: coreSize * (vidro ? 0.49 : 0.41)
    readonly property real coreCx: coreSize * 0.52
    readonly property real coreCy: height * 0.5

    property int level: 0
    property int cur: 0
    property int parentIdx: 0
    property real scroll: cur
    Behavior on scroll { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
    readonly property var model: level === 0 ? menus : ((menus[parentIdx] || {}).items || [])

    function move(d) {
        if (!model.length) return
        var n = Math.max(0, Math.min(model.length - 1, cur + d))
        if (n === cur) return
        cur = n
        soundReq("move")
    }
    function activate() {
        var e = model[cur]
        if (!e) return
        if (e.items) {
            parentIdx = cur; level = 1; cur = 0
            soundReq("select"); switchAnim.restart()
        } else if (e.action) {
            soundReq("select"); actionReq(e.action)
        } else if (e.cmd) {
            soundReq("select"); launchReq(e.cmd, e.label)
        }
    }
    function back() {
        if (level === 1) {
            level = 0; cur = parentIdx
            soundReq("back"); switchAnim.restart()
        }
    }

    focus: true
    Keys.onPressed: function (ev) {
        if (ev.key === Qt.Key_Up) m.move(-1)
        else if (ev.key === Qt.Key_Down) m.move(1)
        else if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter || ev.key === Qt.Key_Right || ev.key === Qt.Key_Space) m.activate()
        else if (ev.key === Qt.Key_Escape || ev.key === Qt.Key_Backspace || ev.key === Qt.Key_Left) m.back()
        else return
        ev.accepted = true
    }
    // rodinha: 1 passo por "clique"; aceita mouse comum (120 por clique) e rodinhas/touchpads finos
    WheelHandler {
        acceptedDevices: PointerDevice.Mouse | PointerDevice.TouchPad
        acceptedModifiers: Qt.NoModifier            // Ctrl + rodinha fica livre (redimensionar o widget)
        property real acc: 0
        property real last: 0
        onWheel: function (ev) {
            var d = ev.angleDelta.y !== 0 ? ev.angleDelta.y : ev.pixelDelta.y * 4
            acc += d
            var now = Date.now()
            if (Math.abs(acc) < 90 || now - last < 220) return
            m.move(acc > 0 ? -1 : 1)
            acc = 0; last = now
        }
    }

    // ---------------- esfera
    Item {
        id: core
        width: m.coreSize; height: m.coreSize
        x: m.coreCx - width / 2; y: m.coreCy - height / 2
        layer.enabled: m.pal.tint === true
        layer.effect: MultiEffect { colorization: 1.0; colorizationColor: m.pal.accent }
        Image {
            anchors.centerIn: parent
            width: parent.width * 1.12; height: parent.height * 1.12
            source: m.asset(m.vidro ? "core.png" : "m4/core.png")
            layer.enabled: true
            layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64; brightness: 0.25 }
            opacity: 0.3
        }
        Image { anchors.fill: parent; source: m.asset(m.vidro ? "core.png" : "m4/core.png"); fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true }
    }

    // ---------------- itens do menu em arco
    Item {
        id: menuLayer
        anchors.fill: parent
        transform: Translate { id: menuShift; x: 0 }
        ParallelAnimation {
            id: switchAnim
            NumberAnimation { target: menuLayer; property: "opacity"; from: 0; to: 1; duration: 320 }
            NumberAnimation { target: menuShift; property: "x"; from: 60 * m.u; to: 0; duration: 320; easing.type: Easing.OutCubic }
        }
        Repeater {
            id: rep
            model: m.model
            delegate: Item {
                id: ent
                required property var modelData
                required property int index
                readonly property bool active: index === m.cur
                readonly property real ang: -0.12 + (index - m.scroll) * 0.33
                opacity: Math.max(0, 1 - Math.max(0, Math.abs(ang + 0.12) - 0.9) / 0.3)
                visible: opacity > 0.01
                readonly property real rad: m.coreR * 1.42
                property real bs: (active ? 88 : 70) * m.u
                Behavior on bs { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
                x: m.coreCx + rad * Math.cos(ang) - bs / 2
                y: m.coreCy + rad * Math.sin(ang) - bs / 2
                width: bs + 24 * m.u + pill.width
                height: bs

                Shape {
                    z: -1
                    preferredRendererType: Shape.CurveRenderer
                    ShapePath {
                        strokeColor: m.al(m.pal.accent, ent.active ? 0.85 : 0.35)
                        strokeWidth: (ent.active ? 2.4 : 1.4) * m.u
                        fillColor: "transparent"
                        startX: m.coreCx + m.coreR * 1.05 * Math.cos(ent.ang) - ent.x
                        startY: m.coreCy + m.coreR * 1.05 * Math.sin(ent.ang) - ent.y
                        PathQuad {
                            x: ent.bs * 0.05; y: ent.bs / 2
                            controlX: (m.coreCx + m.coreR * 1.5 * Math.cos(ent.ang * 0.4)) - ent.x
                            controlY: (m.coreCy + m.coreR * 1.5 * Math.sin(ent.ang * 1.6)) - ent.y
                        }
                    }
                }
                Tinted {
                    tint: m.pal.tint === true; tintColor: m.pal.accent
                    width: ent.bs; height: ent.bs
                    source: m.asset(m.vidro ? "bubble.png" : (ent.active ? "m4/socket-sel.png" : "m4/socket.png"))
                    opacity: ent.active ? 1.0 : (m.vidro ? 0.75 : 0.85)
                }
                Tinted {
                    tint: m.pal.tint === true; tintColor: m.pal.accent
                    visible: !m.vidro
                    source: m.asset("m4/link.png")
                    x: ent.bs * 0.82; width: 62 * m.u + ent.bs * 0.22; height: width * 205 / 1211
                    y: ent.bs / 2 - height * 0.62
                    opacity: ent.active ? 1.0 : 0.75
                }
                Item {
                    id: pill
                    width: (m.vidro ? 480 : 420) * m.u; height: m.vidro ? 67 * m.u : width * 318 / 2031
                    readonly property real body: m.vidro ? 0.5 : 0.59
                    x: ent.bs + (m.vidro ? 18 : 62) * m.u
                    y: ent.bs / 2 - height * body
                    transformOrigin: Item.Left
                    scale: ent.active ? 1.08 : 1.0
                    Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
                    transform: Translate { x: ent.active ? 14 * m.u : 0; Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } } }
                    layer.enabled: true
                    layer.effect: MultiEffect {          // sombra escura: legivel em qualquer papel de parede
                        shadowEnabled: true; shadowColor: ent.active ? m.pal.accent : "black"
                        shadowBlur: 1.0; shadowHorizontalOffset: 0; shadowVerticalOffset: ent.active ? 0 : 2
                        shadowOpacity: ent.active ? 0.7 : 0.8; brightness: ent.active ? 0.15 : 0
                    }
                    Tinted {
                        tint: m.pal.tint === true; tintColor: m.pal.accent
                        anchors.fill: parent
                        source: m.asset(m.vidro ? "pill.png" : (ent.active ? "m4/plate-sel.png" : "m4/plate.png"))
                        opacity: ent.active ? 1.0 : (m.vidro ? 0.7 : 0.95)
                    }
                    Text {
                        anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: pill.height * pill.body
                        x: m.vidro ? pill.height * 0.7 : pill.width * 0.1
                        text: ent.modelData.label + (ent.modelData.items ? "  >" : "")
                        color: ent.active ? (m.vidro ? "white" : "#1a2600") : m.pal.bright
                        font.family: m.fam; font.pixelSize: 25 * m.u; font.bold: true; font.letterSpacing: 3 * m.u
                        style: ent.active ? Text.Normal : Text.Outline; styleColor: Qt.rgba(0, 0, 0, 0.55)
                    }
                }
                MouseArea {
                    anchors.fill: parent
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        m.forceActiveFocus()
                        if (m.cur !== ent.index) { m.cur = ent.index; m.soundReq("move") }
                        else m.activate()
                    }
                }
            }
        }
    }

    // botao "voltar" discreto dentro de um submenu (clique na esfera tambem volta)
    MouseArea {
        x: core.x + core.width * 0.2; y: core.y + core.height * 0.2
        width: core.width * 0.6; height: core.height * 0.6
        cursorShape: m.level === 1 ? Qt.PointingHandCursor : Qt.ArrowCursor
        onClicked: { m.forceActiveFocus(); m.back() }
    }
}
