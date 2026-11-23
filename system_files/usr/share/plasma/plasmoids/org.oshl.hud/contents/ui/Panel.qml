import QtQuick

// Moldura com titulo, linha e cantoneiras (estilo HUD)
Item {
    id: p
    property var t
    property real u: 1
    property string title: ""
    property string tag: ""
    default property alias content: inner.data

    Rectangle { anchors.fill: parent; color: p.t.bg; opacity: 0.55 }

    Text {
        id: ttl
        x: 2
        text: p.title
        color: p.t.accent
        font.family: "Fira Mono"
        font.pixelSize: Math.round(11 * p.u)
        font.letterSpacing: 1.5 * p.u
    }
    Text {
        anchors.right: parent.right
        anchors.rightMargin: 2
        anchors.baseline: ttl.baseline
        width: Math.max(0, parent.width - ttl.width - 16)
        horizontalAlignment: Text.AlignRight
        elide: Text.ElideLeft
        text: p.tag
        color: p.t.accent
        opacity: 0.6
        font.family: "Fira Mono"
        font.pixelSize: Math.round(10 * p.u)
    }
    Rectangle { id: line; y: ttl.height + 3 * p.u; width: parent.width; height: 1; color: p.t.accent; opacity: 0.6 }
    Rectangle { x: 0; y: line.y; width: 1; height: 7 * p.u; color: p.t.accent }
    Rectangle { x: parent.width - 1; y: line.y; width: 1; height: 7 * p.u; color: p.t.accent }
    Rectangle { x: 0; y: parent.height - 1; width: 12 * p.u; height: 1; color: p.t.accent; opacity: 0.7 }
    Rectangle { x: parent.width - 12 * p.u; y: parent.height - 1; width: 12 * p.u; height: 1; color: p.t.accent; opacity: 0.7 }

    Item {
        id: inner
        anchors.fill: parent
        anchors.topMargin: line.y + 8 * p.u
        anchors.leftMargin: 6 * p.u
        anchors.rightMargin: 6 * p.u
        anchors.bottomMargin: 6 * p.u
    }
}
