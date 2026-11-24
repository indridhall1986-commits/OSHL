import QtQuick
import QtQuick.Effects

// Relogio holografico: emblema organico (esfera + placa), globo de grade pulsando,
// hora digital dentro da esfera, ponto de luz orbitando nos segundos e data na placa.
Item {
    id: h
    property var pal
    property string fam
    property string emblem
    property string sphere
    height: width * 1135 / 1023
    property date now: new Date()
    Timer { interval: 200; running: true; repeat: true; onTriggered: h.now = new Date() }
    readonly property var dias: ["DOMINGO", "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO"]
    readonly property var meses: ["JAN", "FEV", "MAR", "ABR", "MAI", "JUN", "JUL", "AGO", "SET", "OUT", "NOV", "DEZ"]
    function pad(n) { return (n < 10 ? "0" : "") + n }
    // geometria medida na arte (fracoes da largura/altura)
    readonly property real cx: width * 0.497
    readonly property real cy: height * 0.330
    readonly property real r: width * 0.305

    Tinted { anchors.fill: parent; source: h.emblem; tint: h.pal.tint; tintColor: h.pal.accent }
    Tinted {                                    // globo de grade dentro da esfera
        tint: h.pal.tint; tintColor: h.pal.accent
        x: h.cx - h.r * 0.92; y: h.cy - h.r * 0.92; width: h.r * 1.84; height: h.r * 1.84
        source: h.sphere
        SequentialAnimation on opacity {
            loops: Animation.Infinite; running: typeof previewMode === "undefined" || !previewMode
            NumberAnimation { from: 0.25; to: 0.55; duration: 2400; easing.type: Easing.InOutSine }
            NumberAnimation { from: 0.55; to: 0.25; duration: 2400; easing.type: Easing.InOutSine }
        }
        opacity: 0.4
    }
    Column {
        anchors.horizontalCenter: parent.left; anchors.horizontalCenterOffset: h.cx
        anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: h.cy
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: h.pad(h.now.getHours()) + ":" + h.pad(h.now.getMinutes())
            color: "white"; font.family: h.fam; font.pixelSize: h.r * 0.46; font.bold: true
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowColor: h.pal.bright; shadowBlur: 0.8; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: h.pad(h.now.getSeconds())
            color: h.pal.bright; font.family: h.fam; font.pixelSize: h.r * 0.17
        }
    }
    Rectangle {                                 // ponto de luz orbitando (segundos)
        readonly property real a: (h.now.getSeconds() + h.now.getMilliseconds() / 1000) * 6 * Math.PI / 180 - Math.PI / 2
        width: h.r * 0.11; height: width; radius: width / 2
        x: h.cx + h.r * 1.04 * Math.cos(a) - width / 2
        y: h.cy + h.r * 1.04 * Math.sin(a) - height / 2
        color: "white"
        layer.enabled: true
        layer.effect: MultiEffect { shadowEnabled: true; shadowColor: h.pal.bright; shadowBlur: 1.0; shadowScale: 1.6; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
    }
    Column {                                    // data na placa inferior
        anchors.horizontalCenter: parent.left; anchors.horizontalCenterOffset: h.width * 0.53
        anchors.verticalCenter: parent.top; anchors.verticalCenterOffset: h.height * 0.814
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: h.dias[h.now.getDay()]
            color: h.pal.bright; font.family: h.fam; font.pixelSize: h.width * 0.075; font.bold: true; font.letterSpacing: 3
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: h.pad(h.now.getDate()) + " " + h.meses[h.now.getMonth()] + " " + h.now.getFullYear()
            color: "white"; font.family: h.fam; font.pixelSize: h.width * 0.052; font.letterSpacing: 2
        }
    }
}
