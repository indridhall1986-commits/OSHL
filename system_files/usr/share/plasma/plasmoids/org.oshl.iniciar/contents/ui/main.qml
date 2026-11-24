import QtQuick
import QtQuick.Layouts
import QtQuick.Effects
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import org.kde.plasma.plasma5support as P5Support
import org.kde.kirigami as Kirigami
import "file:///usr/share/oshl/dashboard"

// Menu Iniciar OSHL (igual a previa): esfera na barra; ao abrir: cabecalho com o usuario e o tema,
// busca, grade de 12 programas fixados (ou todos os programas) e Desligar / Reiniciar / Suspender.
// Tecla Windows abre (X-Plasma-Provides: launchermenu). Digitar ja busca; Enter abre o 1o resultado.
PlasmoidItem {
    id: root
    preferredRepresentation: compactRepresentation
    switchWidth: 1; switchHeight: 1

    OshlData { id: dados; wantStats: false }
    property var apps: []
    property string userName: "USUARIO"
    property bool showAll: false
    property string query: ""
    // 12 fixados (na ordem da previa); para cada um, o primeiro .desktop que existir
    readonly property var favSlots: [
        ["steam.desktop", "com.valvesoftware.Steam.desktop"],
        ["oshl-browser.desktop", "firefox.desktop", "org.mozilla.firefox.desktop"],
        ["vlc.desktop", "org.videolan.vlc.desktop", "org.videolan.VLC.desktop"],
        ["com.obsproject.Studio.desktop", "obs.desktop"],
        ["gimp.desktop", "org.gimp.GIMP.desktop"],
        ["org.kde.krita.desktop", "krita.desktop"],
        ["org.kde.dolphin.desktop"],
        ["org.kde.konsole.desktop"],
        ["org.kde.kwrite.desktop", "org.kde.kate.desktop"],
        ["org.kde.kcalc.desktop", "org.kde.kalk.desktop"],
        ["systemsettings.desktop", "org.kde.systemsettings.desktop"],
        ["org.strawberrymusicplayer.strawberry.desktop"]]
    readonly property var favorites: {
        var byId = {}, out = []
        for (var i = 0; i < apps.length; i++) byId[apps[i].id] = apps[i]
        for (var s = 0; s < favSlots.length; s++)
            for (var c = 0; c < favSlots[s].length; c++)
                if (byId[favSlots[s][c]]) { out.push(byId[favSlots[s][c]]); break }
        return out
    }
    readonly property var shown: {
        var q = query.trim().toLowerCase()
        if (q === "") return showAll ? apps : favorites
        return apps.filter(function (a) {
            return (a.name + " " + a.generic + " " + a.keys).toLowerCase().indexOf(q) >= 0
        })
    }

    function launch(a) {
        dados.run("setsid -f sh -c " + dados.q("kioclient exec " + dados.q(a.file) + " || gtk-launch "
                  + dados.q(a.id.replace(/\.desktop$/, ""))) + " >/dev/null 2>&1")
        root.expanded = false
    }
    function refresh() {
        exe.connectSource("/usr/libexec/oshl-apps")
        exe.connectSource("n=$(getent passwd \"$USER\" | cut -d: -f5 | cut -d, -f1); echo \"${n:-$USER}\"")
        dados.run(dados.statsCmd)
    }
    onExpandedChanged: if (expanded) { query = ""; showAll = false; refresh() }
    Component.onCompleted: refresh()

    P5Support.DataSource {
        id: exe
        engine: "executable"
        connectedSources: []
        onNewData: function (src, data) {
            exe.disconnectSource(src)
            var out = (data["stdout"] || "").trim()
            if (src === "/usr/libexec/oshl-apps") { try { root.apps = JSON.parse(out) } catch (e) { console.warn("oshl-iniciar:", e) } }
            else if (out) root.userName = out.toUpperCase()
        }
    }

    // ---------------- esfera na barra
    compactRepresentation: Item {
        Layout.minimumWidth: height
        Layout.preferredWidth: height
        Image {
            anchors.fill: parent; anchors.margins: 2
            source: "file:///usr/share/oshl/orbital/core.png"
            fillMode: Image.PreserveAspectFit; smooth: true; mipmap: true
            scale: ma.containsMouse || root.expanded ? 1.1 : 1.0
            Behavior on scale { NumberAnimation { duration: 140 } }
            layer.enabled: dados.pal.tint === true
            layer.effect: MultiEffect { colorization: 1.0; colorizationColor: dados.pal.accent }
        }
        MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; onClicked: root.expanded = !root.expanded }
    }

    // ---------------- menu aberto
    fullRepresentation: Item {
        id: menu
        Layout.preferredWidth: 620; Layout.preferredHeight: 640
        Layout.minimumWidth: 620; Layout.minimumHeight: 640
        readonly property color accent: dados.pal.accent
        readonly property color bright: dados.pal.bright
        function al(c, a) { var q = Qt.lighter(c, 1.0); return Qt.rgba(q.r, q.g, q.b, a) }
        Keys.forwardTo: [search]

        Tinted { x: 24; y: 20; width: 54; height: 54; source: dados.asset("bubble.png"); tint: dados.pal.tint === true; tintColor: menu.accent }
        Text { x: 90; y: 26; text: root.userName; color: menu.bright; font.family: dados.fam; font.pixelSize: 18; font.letterSpacing: 3 }
        Text { x: 90; y: 52; text: "OSHL // " + String(dados.pal.key || "orbital").toUpperCase(); color: menu.accent; font.pixelSize: 13 }
        Rectangle {
            x: parent.width - width - 24; y: 28; width: 260; height: 40; radius: 20
            color: menu.al("black", 0.4); border.color: menu.al(menu.accent, 0.6)
            TextInput {
                id: search
                anchors.fill: parent; anchors.leftMargin: 18; anchors.rightMargin: 14
                verticalAlignment: TextInput.AlignVCenter
                color: menu.bright; font.pixelSize: 15; selectionColor: menu.al(menu.accent, 0.5)
                focus: root.expanded
                onTextChanged: root.query = text
                Keys.onReturnPressed: if (root.shown.length) root.launch(root.shown[0])
                Keys.onEscapePressed: root.expanded = false
                Text { anchors.verticalCenter: parent.verticalCenter; visible: !search.text; text: "Buscar programas..."
                       color: menu.al(menu.bright, 0.5); font.pixelSize: 15 }
            }
        }

        // grade (4 colunas); rola quando ha mais programas
        Flickable {
            id: fl
            x: 24; y: 100; width: parent.width - 48; height: parent.height - 100 - 78
            contentHeight: grid.height; clip: true
            boundsBehavior: Flickable.StopAtBounds
            Grid {
                id: grid
                columns: 4; columnSpacing: 14; rowSpacing: 14
                Repeater {
                    model: root.shown
                    Rectangle {
                        required property var modelData
                        width: 132; height: 116; radius: 14
                        color: tma.containsMouse ? menu.al(menu.accent, 0.2) : menu.al("black", 0.15)
                        border.color: tma.containsMouse ? menu.al(menu.accent, 0.8) : menu.al(menu.accent, 0.15)
                        Kirigami.Icon { anchors.horizontalCenter: parent.horizontalCenter; y: 14; width: 54; height: 54; source: modelData.icon }
                        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 78; width: parent.width - 12
                               horizontalAlignment: Text.AlignHCenter; elide: Text.ElideRight
                               text: modelData.name; color: menu.bright; font.pixelSize: 14 }
                        MouseArea { id: tma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                                    onClicked: root.launch(modelData) }
                    }
                }
            }
        }
        Text {
            visible: root.shown.length === 0 && root.query !== ""
            anchors.centerIn: fl; text: "Nada encontrado"; color: menu.al(menu.bright, 0.6); font.pixelSize: 15
        }

        // rodape: todos os programas + energia
        Row {
            x: 24; anchors.bottom: parent.bottom; anchors.bottomMargin: 18; spacing: 8
            Item { width: 36; height: 36
                Tinted { anchors.fill: parent; anchors.margins: -3; source: dados.asset("bubble.png"); tint: dados.pal.tint === true; tintColor: menu.accent }
                Text { anchors.centerIn: parent; text: root.showAll ? "★" : "▦"; color: "white"; font.pixelSize: 15 } }
            Text { anchors.verticalCenter: parent.verticalCenter; text: root.showAll ? "FIXADOS" : "TODOS OS PROGRAMAS"
                   color: menu.al(menu.bright, 0.8); font.family: dados.fam; font.pixelSize: 12; font.letterSpacing: 2 }
        }
        MouseArea { x: 24; anchors.bottom: parent.bottom; anchors.bottomMargin: 18; width: 230; height: 36
                    cursorShape: Qt.PointingHandCursor; onClicked: { root.showAll = !root.showAll; search.text = ""; fl.contentY = 0 } }
        Row {
            anchors.right: parent.right; anchors.rightMargin: 24; anchors.bottom: parent.bottom; anchors.bottomMargin: 18; spacing: 22
            Repeater {
                model: [["⏻", "DESLIGAR", "qdbus6 org.kde.LogoutPrompt /LogoutPrompt promptShutDown"],
                        ["↻", "REINICIAR", "qdbus6 org.kde.LogoutPrompt /LogoutPrompt promptReboot"],
                        ["☾", "SUSPENDER", "systemctl suspend"]]
                Row {
                    required property var modelData
                    spacing: 8
                    Item { width: 36; height: 36
                        Tinted { anchors.fill: parent; anchors.margins: -3; source: dados.asset("bubble.png"); tint: dados.pal.tint === true; tintColor: menu.accent }
                        Text { anchors.centerIn: parent; text: modelData[0]; color: "white"; font.pixelSize: 16 }
                        MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                                    onClicked: { root.expanded = false; dados.run(modelData[2]) } } }
                    Text { anchors.verticalCenter: parent.verticalCenter; text: modelData[1]
                           color: menu.al(menu.bright, 0.8); font.family: dados.fam; font.pixelSize: 12; font.letterSpacing: 2 }
                }
            }
        }
    }
}
