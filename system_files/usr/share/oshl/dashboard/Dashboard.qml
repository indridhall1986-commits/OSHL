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
    property real scroll: cur                        // posicao animada da "roda" do menu
    Behavior on scroll { NumberAnimation { duration: 600; easing.type: Easing.OutCubic } }
    property int parentIdx: 0
    readonly property var model: level === 0 ? menus : (menus[parentIdx].items || [])
    readonly property bool vidro: backend.menuStyle === "vidro"      // estilo VIDRO (1a versao) ou CLASSICO
    readonly property real coreSize: height * (vidro ? 0.50 : 0.60)
    readonly property real coreR: coreSize * (vidro ? 0.49 : 0.41)
    readonly property real coreCx: width * 0.30
    readonly property real coreCy: height * 0.52

    function al(c, a) { var q = Qt.lighter(c, 1.0); return Qt.rgba(q.r, q.g, q.b, a) }

    function move(d) {
        if (!model.length) return
        var n = Math.max(0, Math.min(model.length - 1, cur + d))
        if (n === cur) return
        cur = n
        backend.sound("move")
    }
    function activate() {
        var e = model[cur]
        if (!e) return
        if (e.items) {
            parentIdx = cur; level = 1; cur = 0
            backend.sound("select"); switchAnim.restart()
        } else if (e.action === "style") {
            backend.sound("select"); backend.toggleMenuStyle(); toast.show("ESTILO: " + (win.vidro ? "VIDRO" : "CLASSICO"))
        } else if (e.action === "widgets") {
            backend.sound("select"); backend.showAllWidgets(); toast.show("WIDGETS VISIVEIS")
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
        id: dashRoot
        anchors.fill: parent
        focus: true
        WheelHandler {                       // rodinha: 1 passo por "clique", com pausa entre passos
            property real acc: 0
            property real last: 0
            onWheel: function (ev) {
                acc += ev.angleDelta.y
                var now = Date.now()
                if (Math.abs(acc) < 100 || now - last < 280) return
                win.move(acc > 0 ? -1 : 1)
                acc = 0; last = now
            }
        }
        Keys.onPressed: function (ev) {
            if (ev.key === Qt.Key_Up) win.move(-1)
            else if (ev.key === Qt.Key_Down) win.move(1)
            else if (ev.key === Qt.Key_Return || ev.key === Qt.Key_Enter || ev.key === Qt.Key_Right || ev.key === Qt.Key_Space) win.activate()
            else if (ev.key === Qt.Key_Escape || ev.key === Qt.Key_Backspace || ev.key === Qt.Key_Left) win.back()
            else if (ev.key === Qt.Key_W || ev.key === Qt.Key_Y) backend.nextWallpaper()
            else if (ev.key === Qt.Key_E) { backend.toggleMenuStyle(); toast.show("ESTILO: " + (win.vidro ? "VIDRO" : "CLASSICO")) }
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
                width: parent.width; height: parent.height
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
                    source: backend.asset(win.vidro ? "core.png" : "m4/core.png")
                    layer.enabled: true
                    layer.effect: MultiEffect { blurEnabled: true; blur: 1.0; blurMax: 64; brightness: 0.25 }
                    opacity: 0.3
                }
                Image {
                    id: coreImg
                    anchors.fill: parent; source: backend.asset(win.vidro ? "core.png" : "m4/core.png"); fillMode: Image.PreserveAspectFit
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
        // ================= widgets organicos (relogio holografico, sistema, placa de video)
        readonly property real bottomReserve: (backend.windowMode && simPath === "") ? 0 : 64 * win.u   // espaco da barra de tarefas

        HoloClock {
            visible: backend.widgets["clock"] !== false
            HoverHandler { id: hv_clock }
            CloseBtn { show: hv_clock.hovered; pal: win.pal; onClicked: backend.setWidget("clock", false) }
            x: win.width - width - 60 * win.u; y: 18 * win.u
            width: 300 * win.u
            pal: win.pal; fam: win.fam
            emblem: backend.asset("w2/emblem.png"); sphere: backend.asset("w2/sphere.png")
        }
        OrganicMonitor {
            visible: backend.widgets["monitor"] !== false
            HoverHandler { id: hv_monitor }
            CloseBtn { show: hv_monitor.hovered; pal: win.pal; onClicked: backend.setWidget("monitor", false) }
            x: win.width - width - 75 * win.u; y: 360 * win.u
            width: 290 * win.u
            pal: win.pal; fam: win.fam; stats: backend.stats
            frame: backend.asset("w2/frame.png"); row: backend.asset("w2/row.png"); rowSel: backend.asset("w2/row-sel.png")
        }
        InfoCard {
            visible: backend.widgets["gpu"] !== false
            HoverHandler { id: hv_gpu }
            CloseBtn { show: hv_gpu.hovered; pal: win.pal; onClicked: backend.setWidget("gpu", false) }
            x: 55 * win.u; y: win.height - parent.bottomReserve - height - 6 * win.u
            width: 340 * win.u
            pal: win.pal; fam: win.fam
            card: backend.asset("w2/card.png")
            title: "PLACA DE VIDEO"; tag: backend.stats.gpuName || "GPU"
            fields: [{ k: "USO", v: Math.round(backend.stats.gpu) + "%" },
                     { k: "TEMP", v: Math.round(backend.stats.gpuTemp) + "°C" },
                     { k: "VRAM", v: (backend.stats.vramUsed / 1024).toFixed(1) + " GB" }]
        }

        // ================= menu em arco ao redor do nucleo
        Item {
            id: menuLayer
            anchors.fill: parent
            // mouse parado sobre o menu central: o Dashboard pega o foco e as setas do teclado giram o menu
            HoverHandler {
                onHoveredChanged: if (hovered) { win.requestActivate(); dashRoot.forceActiveFocus() }
            }
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
                    readonly property real ang: -0.12 + (index - win.scroll) * 0.33   // foco um pouco acima do meio
                    opacity: Math.max(0, 1 - Math.max(0, Math.abs(ang + 0.12) - 0.9) / 0.3)
                    visible: opacity > 0.01
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

                    Tinted {
                        id: bubble
                        tint: win.pal.tint; tintColor: win.pal.accent
                        width: ent.bs; height: ent.bs
                        source: backend.asset(win.vidro ? "bubble.png" : (ent.active ? "m4/socket-sel.png" : "m4/socket.png"))
                        opacity: ent.active ? 1.0 : (win.vidro ? 0.75 : 0.85)
                    }

                    // conector (fio com presilhas) do soquete ate a placa
                    Tinted {
                        tint: win.pal.tint; tintColor: win.pal.accent
                        source: backend.asset("m4/link.png")
                        x: ent.bs * 0.82; width: 62 * win.u + ent.bs * 0.22; height: width * 205 / 1211
                        y: ent.bs / 2 - height * 0.62
                        visible: !win.vidro
                        opacity: ent.active ? 1.0 : 0.75
                    }
                    // placa do menu
                    Item {
                        id: pill
                        width: (win.vidro ? 480 : 420) * win.u; height: win.vidro ? 67 * win.u : width * 318 / 2031
                        readonly property real ph: height
                        readonly property real body: win.vidro ? 0.5 : 0.59                 // centro do corpo da placa
                        x: ent.bs + (win.vidro ? 18 : 62) * win.u
                        y: ent.bs / 2 - height * body
                        transformOrigin: Item.Left
                        scale: ent.active ? 1.08 : 1.0
                        Behavior on scale { NumberAnimation { duration: 180; easing.type: Easing.OutBack } }
                        transform: Translate { x: ent.active ? 14 * win.u : 0; Behavior on x { NumberAnimation { duration: 180; easing.type: Easing.OutCubic } } }
                        layer.enabled: ent.active
                        layer.effect: MultiEffect { brightness: 0.15; shadowEnabled: true; shadowColor: win.pal.accent; shadowBlur: 1.0; shadowHorizontalOffset: 0; shadowVerticalOffset: 0; shadowOpacity: 0.7 }
                        Tinted {
                            tint: win.pal.tint; tintColor: win.pal.accent
                            anchors.fill: parent
                            source: backend.asset(win.vidro ? "pill.png" : (ent.active ? "m4/plate-sel.png" : "m4/plate.png"))
                            opacity: ent.active ? 1.0 : (win.vidro ? 0.5 : 0.9)
                            Behavior on opacity { NumberAnimation { duration: 150 } }
                        }
                        Text {
                            anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: pill.height * pill.body
                            x: win.vidro ? pill.height * 0.7 : pill.width * 0.1
                            text: ent.modelData.label + (ent.modelData.items ? "  >" : "")
                            color: ent.active ? (win.vidro ? "white" : "#1a2600") : win.pal.bright
                            font.family: win.fam; font.pixelSize: 25 * win.u; font.bold: true; font.letterSpacing: 3 * win.u
                        }
                    }

                    MouseArea {
                        anchors.fill: parent
                        hoverEnabled: true
                        cursorShape: Qt.PointingHandCursor
                        onClicked: {                  // 1o clique: gira ate o foco; clique no item em foco: abre
                            if (win.cur !== ent.index) { win.cur = ent.index; backend.sound("move") }
                            else win.activate()
                        }
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
                        Tinted { anchors.fill: parent; anchors.margins: -4 * win.u; source: backend.asset("bubble.png"); tint: win.pal.tint; tintColor: win.pal.accent }
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

    // Simulador da area de trabalho (apenas em teste: OSHL_SIM_QML)
    Loader {
        anchors.fill: parent; z: 50
        active: simPath !== ""
        source: simPath
        onLoaded: item.backdrop = dashRoot
    }
}
