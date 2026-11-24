import QtQuick

// Ficha de informacao (estilo "SOUNDTRACK 1 / TRACKS: 14"): titulo grande, rotulos pequenos e valores grandes.
Item {
    id: c
    property var pal
    property string fam
    property string card
    property string title: ""
    property string tag: ""
    property var fields: []                     // [{ k: "TEMP", v: "61 C" }, ...]
    height: width * 688 / 1400

    Tinted { anchors.fill: parent; source: c.card; tint: c.pal.tint; tintColor: c.pal.accent }
    Text {
        x: c.width * 0.08; anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: c.height * 0.19
        text: c.title
        color: "white"; font.family: c.fam; font.pixelSize: c.height * 0.095; font.bold: true; font.letterSpacing: 1
    }
    Text {
        anchors.right: parent.right; anchors.rightMargin: c.width * 0.1
        anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: c.height * 0.3
        text: c.tag
        color: c.pal.bright; font.family: c.fam; font.pixelSize: c.height * 0.075; font.letterSpacing: 2
    }
    Grid {
        x: c.width * 0.08; y: c.height * 0.38
        columns: 3; columnSpacing: c.width * 0.07; rowSpacing: c.height * 0.04
        Repeater {
            model: c.fields
            Column {
                required property var modelData
                Text { text: modelData.k + ":"; color: c.pal.bright; font.family: c.fam; font.pixelSize: c.height * 0.07; font.letterSpacing: 2 }
                Text { text: modelData.v; color: "white"; font.family: c.fam; font.pixelSize: c.height * 0.15 }
            }
        }
    }
}
