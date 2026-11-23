import QtQuick

// Rotulo pequeno + valor
Column {
    id: c
    property var t
    property real u: 1
    property string label: ""
    property string value: ""
    property bool alert: false
    spacing: 1
    Text {
        text: c.label
        color: c.t.accent
        opacity: 0.6
        font.family: "Fira Mono"
        font.pixelSize: Math.round(10 * c.u)
        font.letterSpacing: 1
    }
    Text {
        text: c.value
        color: c.alert ? c.t.alert : c.t.bright
        font.family: "Fira Mono"
        font.pixelSize: Math.round(15 * c.u)
    }
}
