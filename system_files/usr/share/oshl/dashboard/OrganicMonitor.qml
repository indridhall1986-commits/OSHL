import QtQuick

// Monitor do sistema: moldura organica com titulo no topo e itens em placas de lista.
// O item com maior uso fica "selecionado" (placa limao acesa), como na referencia.
Item {
    id: m
    property var pal
    property string fam
    property string frame
    property string row
    property string rowSel
    property var stats: ({})
    height: width * 1211 / 928
    readonly property var items: [
        { k: "CPU", v: m.stats.cpu || 0, t: Math.round(m.stats.cpu || 0) + "%" },
        { k: "GPU", v: m.stats.gpu || 0, t: Math.round(m.stats.gpu || 0) + "%" },
        { k: "RAM", v: m.stats.ram || 0, t: Math.round(m.stats.ram || 0) + "%" },
        { k: "DISCO", v: m.stats.disk || 0, t: Math.round(m.stats.disk || 0) + "%" },
        { k: "REDE", v: Math.min(100, (m.stats.rx || 0) / 250000), t: ((m.stats.rx || 0) / 1048576).toFixed(1) + " MB/s" },
        { k: "TEMP", v: m.stats.cpuTemp || 0, t: Math.round(m.stats.cpuTemp || 0) + "°C" }
    ]
    readonly property int topIdx: {
        var best = 0
        for (var i = 1; i < 4; i++) if (items[i].v > items[best].v) best = i
        return best
    }

    Image { anchors.fill: parent; source: m.frame; smooth: true; mipmap: true }
    Text {
        anchors.horizontalCenter: parent.left; anchors.horizontalCenterOffset: m.width * 0.53
        anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: m.height * 0.115
        text: "SISTEMA"
        color: "white"; font.family: m.fam; font.pixelSize: m.width * 0.085; font.bold: true; font.letterSpacing: 4
    }
    Column {
        x: m.width * 0.15; y: m.height * 0.25
        width: m.width * 0.71
        spacing: m.height * 0.012
        Repeater {
            model: m.items
            Item {
                required property var modelData
                required property int index
                readonly property bool sel: index === m.topIdx
                width: parent.width; height: width * 0.155
                Image { anchors.fill: parent; source: sel ? m.rowSel : m.row; smooth: true; mipmap: true }
                Text {
                    x: parent.width * 0.09; anchors.verticalCenter: parent.verticalCenter
                    text: modelData.k
                    color: sel ? "#162300" : m.pal.bright
                    font.family: m.fam; font.pixelSize: parent.height * 0.36; font.bold: true; font.letterSpacing: 2
                }
                Text {
                    anchors.right: parent.right; anchors.rightMargin: parent.width * 0.16; anchors.verticalCenter: parent.verticalCenter
                    text: modelData.t
                    color: sel ? "#162300" : "white"
                    font.family: m.fam; font.pixelSize: parent.height * 0.36; font.bold: sel
                }
            }
        }
    }
}
