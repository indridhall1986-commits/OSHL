import QtQuick
import QtQuick.Effects

// Barra de uso: rotulo + trilho de vidro + preenchimento luminoso.
Item {
    id: b
    property real value: 0               // 0..100
    property string label: ""
    property string info: ""
    property var pal
    property string fam
    property string track
    height: width * 0.2
    Behavior on value { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }

    Text { id: lbl; text: b.label; color: b.pal.bright; font.family: b.fam; font.pixelSize: b.height * 0.32; font.letterSpacing: 2 }
    Text { anchors.right: parent.right; anchors.baseline: lbl.baseline; text: b.info; color: "white"; font.family: b.fam; font.pixelSize: b.height * 0.3 }
    Item {
        id: bar
        anchors.left: parent.left; anchors.right: parent.right; anchors.bottom: parent.bottom
        height: b.height * 0.5
        Rectangle {                                   // preenchimento por dentro do trilho
            x: bar.height * 0.22; anchors.verticalCenter: parent.verticalCenter
            height: bar.height * 0.42; radius: height / 2
            width: Math.max(height, (bar.width - bar.height * 0.44) * Math.min(100, Math.max(0, b.value)) / 100)
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0; color: b.pal.accent }
                GradientStop { position: 1; color: b.pal.bright }
            }
            layer.enabled: true
            layer.effect: MultiEffect { shadowEnabled: true; shadowColor: b.pal.bright; shadowBlur: 0.6; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
        }
        Image { anchors.fill: parent; source: b.track; smooth: true; mipmap: true }
    }
}
