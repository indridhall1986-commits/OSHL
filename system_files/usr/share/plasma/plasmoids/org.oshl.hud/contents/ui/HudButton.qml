import QtQuick

// Botao no estilo "tecla" do HUD
Rectangle {
    id: btn
    property var t
    property real u: 1
    property string label: ""
    signal activated()

    color: ma.containsMouse ? btn.t.accent : "transparent"
    border.color: btn.t.accent
    border.width: 1
    radius: 2

    Rectangle { anchors.fill: parent; color: btn.t.bg; opacity: ma.containsMouse ? 0 : 0.55; z: -1 }

    Text {
        anchors.centerIn: parent
        text: btn.label
        color: ma.containsMouse ? btn.t.bg : btn.t.accent
        font.family: "Fira Mono"
        font.pixelSize: Math.round(Math.min(16 * btn.u, btn.height * 0.38))
        font.letterSpacing: 2 * btn.u
    }
    MouseArea {
        id: ma
        anchors.fill: parent
        hoverEnabled: true
        cursorShape: Qt.PointingHandCursor
        onClicked: btn.activated()
    }
}
