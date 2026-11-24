import QtQuick
import QtQuick.Window
import QtQuick.Shapes
import QtQuick.Effects

// Dashboard OSHL: nucleo de vidro + menu de esferas e capsulas sobre a malha orbital.
Window {
    id: win
    width: backend.windowMode ? 1280 : 1920
    height: backend.windowMode ? 720 : 1080
    visible: true
    visibility: (previewMode || backend.windowMode) ? Window.Windowed : Window.FullScreen
    flags: (previewMode || backend.windowMode) ? Qt.Window : Qt.FramelessWindowHint
    color: "black"
    title: "Dashboard OSHL"

    readonly property var pal: backend.palette
    readonly property string fam: backend.fontFamily
    readonly property real u: Math.min(width / 1920, height / 1080)
    readonly property var menus: backend.menus
    property int level: 0
    property int cur: 0
    property int parentIdx: 0
    readonly property var model: level === 0 ? menus : (menus[parentIdx].items || [])
    readonly property real coreSize: height * 0.50
    readonly property real coreR: coreSize * 0.49
    readonly property real coreCx: width * 0.30
    readonly property real coreCy: height * 0.52

    function al(c, a) { var q = Qt.lighter(c, 1.0); return Qt.rgba(q.r, q.g, q.b, a) }

    function move(d) {
        if (!model.length) return
        cur = (cur + d + model.length) % model.length
        backend.sound("move")
    }
    function activate() {
        var e = model[cur]
        if (!e) return
        if (e.items) {
            parentIdx = cur; level = 1; cur = 0
            backend.sound("select"); switchAnim.restart()
        } else if (e.cmd) {
            backend.sound("select")
            if (backend.testMode) { toast.show("ABRIRIA: " + e.label); return }
            backend.launch(e.cmd)
            quitTimer.start()
        }
    }
    function back() {
        if (level === 1) {
            level = 0; cur = parentIdx
            backend.sound("back"); switchAnim.restart()
        } else {
            backend.sound("back")
            quitTimer.start()
        }
    }

    Timer { id: quitTimer; interval: 260; onTriggered: backend.quit() }

    // aviso do modo de teste (Windows): mostra o que seria aberto
    Rectangle {
        id: toast
        z: 100
        function show(msg) { toastText.text = msg; toastAnim.restart() }
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.86
        width: toastText.implicitWidth + 60 * win.u; height: 64 * win.u
        radius: height / 2
        color: win.al(win.pal.bg, 0.85)
        border.color: win.pal.accent; border.width: 2
        opacity: 0
        Text { id: toastText; anchors.centerIn: parent; color: win.pal.bright; font.family: win.fam; font.pixelSize: 26 * win.u; font.letterSpacing: 3 * win.u }
        SequentialAnimation {
            id: toastAnim
            NumberAnimation { target: toast; property: "opacity"; to: 1; duration: 150 }
            PauseAnimation { duration: 1400 }
            NumberAnimation { target: toast; property: "opacity"; to: 0; duration: 400 }
        }
    }
    Text {
        visible: backend.testMode
        z: 100
        anchors.horizontalCenter: parent.horizontalCenter; anchors.top: parent.top; anchors.topMargin: 14 * win.u
        text: "MODO DE TESTE  -  ESC SAI"
        color: win.al(win.pal.bright, 0.6)
        font.family: win.fam; font.pixelSize: 18 * win.u; font.letterSpacing: 3 * win.u
    }
    Timer {
        interval: 2500; running: previewMode
        onTriggered: win.contentItem.grabToImage(function (r) { r.saveToFile(previewPath); backend.quit() })
    }

    Connections {
        target: backend
        function onPadUp() { win.move(-1) }
        function onPadDown() { win.move(1) }
        function onPadA() { win.activate() }
        function onPadB() { win.back() }
        function onPadRight() { win.activate() }
        function onPadLeft() { win.back() }
        function onPadY() { backend.nextWallpaper() }
    }

    Item {
        anchors.fill: parent
        focus: true
        Keys.onPressed: function (ev) {
            if (ev.key === Qt.Key_Up) win.move(-1)
            else if (ev.key === Qt.Key_Down) win.move(1)
            else if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter || ev.key === Qt.Key_Right || ev.key === Qt.Key_Space) win.activate()
            else if (ev.key === Qt.Key_Escape || ev.key === Qt.Key_Backspace || ev.key === Qt.Key_Left) win.back()
            else if (ev.key === Qt.Key_W || ev.key === Qt.Key_Y) backend.nextWallpaper()
            else return
            ev.accepted = true
        }

        // ================= cena (fundo, malha, nucleo) - tingida nos temas nao verdes
        Item {
            id: scene
            anchors.fill: parent
            layer.enabled: win.pal.tint
            layer.effect: MultiEffect { colorization: 1.0; colorizationColor: win.pal.accent }

            Item {                           // papel de parede com "respiracao" lenta e troca suave (2 camadas)
                id: bgHolder
                anchors.centerIn: parent
                width: parent.width * 1.12; height: parent.height * 1.12
                property bool showA: true
                function swap(url) {
                    var incoming = showA ? bgB : bgA
                    incoming.pending = true
                    incoming.source = url
                    if (incoming.status === Image.Ready) incoming.reveal()
                }
                Component.onCompleted: bgA.source = backend.wallpaper
                Image {
                    id: bgA
                    property bool pending: false
                    function reveal() { pending = false; opacity = 1; bgB.opacity = 0; bgHolder.showA = true }
                    anchors.fill: parent; fillMode: Image.PreserveAspectCrop; asynchronous: true
                    onStatusChanged: if (status === Image.Ready && pending) reveal()
                    Behavior on opacity { NumberAnimation { duration: 900; easing.type: Easing.InOutQuad } }
                }
                Image {
                    id: bgB
                    property bool pending: false
                    function reveal() { pending = false; opacity = 1; bgA.opacity = 0; bgHolder.showA = false }
                    anchors.fill: parent; fillMode: Image.PreserveAspectCrop; asynchronous: true; opacity: 0
                    onStatusChanged: if (status === Image.Ready && pending) reveal()
                    Behavior on opacity { NumberAnimation { duration: 900; easing.type: Easing.InOutQuad } }
                }
                Connections { target: backend; function onWallpaperChanged() { bgHolder.swap(backend.wallpaper) } }
                SequentialAnimation on scale {
                    loops: Animation.Infinite; running: !previewMode
                    NumberAnimation { to: 1.06; duration: 14000; easing.type: Easing.InOutSine }
                    NumberAnimation { to: 1.0; duration: 14000; easing.type: Easing.InOutSine }
                }
                SequentialAnimation on rotation {
                    loops: Animation.Infinite; running: !previewMode
                    NumberAnimation { to: 2.5; duration: 22000; easing.type: Easing.InOutSine }
                    NumberAnimation { to: -2.5; duration: 22000; easing.type: Easing.InOutSine }
                }
            }
            Rectangle { anchors.fill: parent; color: "black"; opacity: 0.38 }   // escurece o fundo

            Item {
                id: coreItem
                width: win.coreSize; height: win.coreSize
                x: win.coreCx - width / 2; y: win.coreCy - height / 2
                scale: 0.6
                opacity: 0
                Component.onCompleted: { intro.start(); backend.sound("open") }
                ParallelAnimation {
                    id: intro
                    NumberAnimation { target: coreItem; property: "scale"; to: 1.0; duration: previewMode ? 1 : 900; easing.type: Easing.OutBack }
                    NumberAnimation { target: coreItem; property: "opacity"; to: 1.0; duration: previewMode ? 1 : 700 }
                }
                Image {                      // brilho pulsando atras do vidro
                    anchors.centerIn: parent
                    width: parent.width * 1.12; height: parent.height * 1.12
                    source: backend.asset("core.png")
                    layer.enabled: true
                    layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64; brightness: 0.25 }
                    SequentialAnimation on opacity {
                        loops: Animation.Infinite; running: !previewMode
                        NumberAnimation { from: 0.15; to: 0.42; duration: 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { from: 0.42; to: 0.15; duration: 1800; easing.type: Easing.InOutSine }
                    }
                    opacity: 0.3
                }
                Image {
                    id: coreImg
                    anchors.fill: parent; source: backend.asset("core.png"); fillMode: Image.PreserveAspectFit
                    SequentialAnimation on scale {
                        loops: Animation.Infinite; running: !previewMode
                        NumberAnimation { to: 1.035; duration: 1800; easing.type: Easing.InOutSine }
                        NumberAnimation { to: 1.0; duration: 1800; easing.type: Easing.InOutSine }
                    }
                }
            }
        }

        // ================= titulo e relogio
        Column {
            x: 90 * win.u; y: 60 * win.u
            spacing: 4 * win.u
            Text {
                text: "OSHL"
                color: win.al(win.pal.accent, 0.8)
                font.family: win.fam; font.pixelSize: 22 * win.u; font.letterSpacing: 8 * win.u
            }
            Text {
                id: title
                text: win.level === 0 ? "PAINEL" : win.menus[win.parentIdx].label
                color: win.pal.bright
                font.family: win.fam; font.pixelSize: 64 * win.u; font.bold: true; font.letterSpacing: 4 * win.u
                layer.enabled: true
                layer.effect: MultiEffect { shadowEnabled: true; shadowColor: win.pal.accent; shadowBlur: 0.8; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
            }
        }
        // ================= widgets (relogios e monitoramento)
        readonly property real colW: 300 * win.u
        readonly property real colX: win.width - colW - 70 * win.u
        readonly property real bottomReserve: backend.windowMode ? 0 : 64 * win.u   // espaco da barra de tarefas

        AnalogClock {
            x: parent.colX + (parent.colW - width) / 2; y: 40 * win.u
            width: 250 * win.u; height: width
            pal: win.pal
            dial: backend.asset("widgets/dial.png")
            handHour: backend.asset("widgets/hand-hour.png")
            handMin: backend.asset("widgets/hand-min.png")
            pivots: backend.pivots
        }

        Item {
            id: monitor
            x: parent.colX; y: 320 * win.u
            width: parent.colW; height: 470 * win.u
            GlassFrame { anchors.fill: parent; source: backend.asset("widgets/frame.png"); thickness: 34 * win.u }
            Column {
                anchors.fill: parent; anchors.margins: 38 * win.u
                spacing: 14 * win.u
                Text { text: "SISTEMA"; color: win.pal.bright; font.family: win.fam; font.pixelSize: 20 * win.u; font.letterSpacing: 5 * win.u }
                Row {
                    spacing: 10 * win.u
                    Gauge { width: 105 * win.u; height: width; value: backend.stats.cpu; label: "CPU"; pal: win.pal; fam: win.fam; dial: backend.asset("widgets/dial.png") }
                    Gauge { width: 105 * win.u; height: width; value: backend.stats.gpu; label: "GPU"; pal: win.pal; fam: win.fam; dial: backend.asset("widgets/dial.png") }
                }
                BarMeter { width: parent.width; value: backend.stats.ram; label: "RAM"; info: Math.round(backend.stats.ram) + "%"; pal: win.pal; fam: win.fam; track: backend.asset("widgets/track.png") }
                BarMeter { width: parent.width; value: backend.stats.disk; label: "DISCO"; info: Math.round(backend.stats.disk) + "%"; pal: win.pal; fam: win.fam; track: backend.asset("widgets/track.png") }
                BarMeter {
                    width: parent.width; value: Math.min(100, backend.stats.rx / 250000); label: "REDE"
                    info: (backend.stats.rx / 1048576).toFixed(1) + " MB/s"; pal: win.pal; fam: win.fam; track: backend.asset("widgets/track.png")
                }
                Text { text: "TEMP  " + Math.round(backend.stats.temp) + "°C"; color: "white"; font.family: win.fam; font.pixelSize: 16 * win.u; font.letterSpacing: 2 * win.u }
            }
        }

        DigitalClock {
            x: 80 * win.u; y: win.height - parent.bottomReserve - height - 36 * win.u
            width: 400 * win.u; height: width * 0.26
            pal: win.pal; fam: win.fam
            panel: backend.asset("widgets/panel.png")
        }

        // ================= menu em arco ao redor do nucleo
        Item {
            id: menuLayer
            anchors.fill: parent
            transform: Translate { id: menuShift; x: 0 }
            ParallelAnimation {
                id: switchAnim
                NumberAnimation { target: menuLayer; property: "opacity"; from: 0; to: 1; duration: 320 }
                NumberAnimation { target: menuShift; property: "x"; from: 60 * win.u; to: 0; duration: 320; easing.type: Easing.OutCubic }
            }

            Repeater {
                id: rep
                model: win.model
                delegate: Item {
                    id: ent
                    required property var modelData
                    required property int index
                    readonly property bool active: index === win.cur
                    readonly property int n: rep.count
                    readonly property real ang: n <= 1 ? 0 : (-0.60 + 1.20 * index / (n - 1))
                    readonly property real rad: win.coreR * 1.42
                    property real bs: (active ? 88 : 70) * win.u
                    readonly property real bx: win.coreCx + rad * Math.cos(ang)
                    readonly property real by: win.coreCy + rad * Math.sin(ang)
                    x: bx - bs / 2
                    y: by - bs / 2
                    width: bs + 24 * win.u + pill.width
                    height: bs
                    Behavior on bs { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }

                    // fio curvo do nucleo ate a esfera
                    Shape {
                        z: -1
                        preferredRendererType: Shape.CurveRenderer
                        ShapePath {
                            strokeColor: win.al(win.pal.accent, ent.active ? 0.85 : 0.35)
                            strokeWidth: (ent.active ? 2.4 : 1.4) * win.u
                            fillColor: "transparent"
                            startX: win.coreCx + win.coreR * 1.05 * Math.cos(ent.ang) - ent.x
                            startY: win.coreCy + win.coreR * 1.05 * Math.sin(ent.ang) - ent.y
                            PathQuad {
                                x: ent.bs / 2 - ent.bs / 2 * 0.9; y: ent.bs / 2
                                controlX: (win.coreCx + win.coreR * 1.5 * Math.cos(ent.ang * 0.4)) - ent.x
                                controlY: (win.coreCy + win.coreR * 1.5 * Math.sin(ent.ang * 1.6)) - ent.y
                            }
                        }
                    }

                    Image {
                        id: bubble
                        width: ent.bs; height: ent.bs
                        source: backend.asset("bubble.png")
                        opacity: ent.active ? 1.0 : 0.75
                    }

                    // capsula com ponta cortada
                    Item {
                        id: pill
                        readonly property real ph: 67 * win.u
                        width: 480 * win.u; height: ph
                        x: ent.bs + 18 * win.u
                        y: (ent.bs - ph) / 2
                        transformOrigin: Item.Left
                        scale: ent.active ? 1.08 : 1.0
                        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
                        transform: Translate { x: ent.active ? 14 * win.u : 0; Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } } }
                        layer.enabled: ent.active
                        layer.effect: MultiEffect { brightness: 0.15; shadowEnabled: true; shadowColor: win.pal.accent; shadowBlur: 1.0; shadowHorizontalOffset: 0; shadowVerticalOffset: 0; shadowOpacity: 0.7 }
                        Image {
                            anchors.fill: parent
                            source: backend.asset("pill.png")
                            opacity: ent.active ? 1.0 : 0.5
                            Behavior on opacity { NumberAnimation { duration: 150 } }
                        }
                        Text {
                            anchors.verticalCenter: parent.verticalCenter
                            x: pill.ph * 0.7
                            text: ent.modelData.label + (ent.modelData.items ? "  >" : "")
                            color: ent.active ? "white" : win.al(win.pal.bright, 0.8)
                            font.family: win.fam; font.pixelSize: 28 * win.u; font.bold: true; font.letterSpacing: 3 * win.u
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onEntered: if (win.cur !== ent.index) { win.cur = ent.index; backend.sound("move") }
                        onClicked: win.activate()
                    }
                }
            }
        }

        // ================= dicas de botoes (A / B)
        Row {
            anchors.right: parent.right; anchors.rightMargin: 90 * win.u
            anchors.bottom: parent.bottom; anchors.bottomMargin: 40 * win.u + parent.bottomReserve
            spacing: 50 * win.u
            Repeater {
                model: [{ k: "Y", t: "FUNDO " + backend.wallpaperInfo, f: function () { backend.nextWallpaper() } },
                        { k: "B", t: win.level === 0 ? "SAIR" : "VOLTAR", f: function () { win.back() } },
                        { k: "A", t: "SELECIONAR", f: function () { win.activate() } }]
                Row {
                    required property var modelData
                    spacing: 22 * win.u
                    Item {
                        width: 54 * win.u; height: 54 * win.u
                        Image { anchors.fill: parent; anchors.margins: -4 * win.u; source: backend.asset("bubble.png") }
                        Text {
                            anchors.centerIn: parent
                            text: modelData.k
                            color: "white"
                            font.family: win.fam; font.pixelSize: 26 * win.u; font.bold: true
                        }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: modelData.f() }
                    }
                    Text {
                        anchors.verticalCenter: parent.verticalCenter
                        text: modelData.t
                        color: win.pal.bright
                        font.family: win.fam; font.pixelSize: 24 * win.u; font.letterSpacing: 3 * win.u
                    }
                }
            }
        }
    }
}
