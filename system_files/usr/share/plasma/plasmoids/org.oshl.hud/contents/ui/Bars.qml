import QtQuick

// Barras verticais com rotulo (items: [{label, value}])
Item {
    id: b
    property var t
    property real u: 1
    property var items: []

    Row {
        id: row
        anchors.fill: parent
        spacing: 10 * b.u
        Repeater {
            model: b.items
            Item {
                width: (row.width - row.spacing * Math.max(0, b.items.length - 1)) / Math.max(1, b.items.length)
                height: row.height
                Text {
                    id: val
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: Math.round(modelData.value) + "%"
                    color: b.t.bright
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(10 * b.u)
                }
                Text {
                    id: lbl
                    anchors.bottom: parent.bottom
                    anchors.horizontalCenter: parent.horizontalCenter
                    text: modelData.label
                    color: b.t.accent
                    opacity: 0.8
                    font.family: "Fira Mono"
                    font.pixelSize: Math.round(10 * b.u)
                }
                Rectangle {
                    anchors.top: val.bottom
                    anchors.bottom: lbl.top
                    anchors.topMargin: 4 * b.u
                    anchors.bottomMargin: 4 * b.u
                    anchors.horizontalCenter: parent.horizontalCenter
                    width: Math.min(parent.width * 0.5, 18 * b.u)
                    color: "transparent"
                    border.color: b.t.dim
                    border.width: 1
                    Rectangle {
                        anchors.bottom: parent.bottom
                        anchors.bottomMargin: 2
                        anchors.horizontalCenter: parent.horizontalCenter
                        width: parent.width - 4
                        height: Math.max(0, (parent.height - 4) * Math.min(100, Math.max(0, modelData.value)) / 100)
                        color: b.t.accent
                    }
                }
            }
        }
    }
}
