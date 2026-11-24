import QtQuick
import QtQuick.Effects

// Relogio digital no visor de vidro.
Item {
    id: d
    property var pal
    property string fam
    property string panel
    property date now: new Date()
    readonly property var dias: ["DOMINGO", "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO"]
    readonly property var meses: ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    Timer { interval: 1000; running: true; repeat: true; onTriggered: d.now = new Date() }
    function pad(n) { return (n < 10 ? "0" : "") + n }

    Image { anchors.fill: parent; source: d.panel; smooth: true; mipmap: true }
    Row {
        anchors.centerIn: parent
        spacing: d.height * 0.22
        Text {
            anchors.verticalCenter: parent.verticalCenter
            text: d.pad(d.now.getHours()) + ":" + d.pad(d.now.getMinutes())
            color: "white"; font.family: d.fam; font.pixelSize: d.height * 0.46; font.bold: true; font.letterSpacing: 3
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowColor: d.pal.bright; shadowBlur: 0.7; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
        }
        Column {
            anchors.verticalCenter: parent.verticalCenter
            Text { text: d.dias[d.now.getDay()]; color: d.pal.bright; font.family: d.fam; font.pixelSize: d.height * 0.17; font.letterSpacing: 2 }
            Text { text: d.pad(d.now.getDate()) + " " + d.meses[d.now.getMonth()] + " " + d.now.getFullYear(); color: Qt.rgba(1, 1, 1, 0.75); font.family: d.fam; font.pixelSize: d.height * 0.15 }
        }
    }
}
