import QtQuick
import QtQuick.Effects
import org.kde.kirigami as Kirigami

// Tela "carregando a sessao" do OSHL (depois do login): esfera, OSHL em Orbitron e barra de progresso.
// A cor segue o esquema de cores do tema (destaque = cor do tema).
Rectangle {
    id: root
    color: "#020401"
    property int stage
    readonly property real u: Math.min(width / 1920, height / 1080)
    readonly property color accent: Kirigami.Theme.highlightColor
    readonly property bool green: accent.hslHue > 0.15 && accent.hslHue < 0.40
    Item {
        id: orb
        anchors.centerIn: parent; anchors.verticalCenterOffset: -60 * root.u
        width: 360 * root.u; height: width
        layer.enabled: !root.green
        layer.effect: MultiEffect { colorization: 1.0; colorizationColor: root.accent }
        Image { anchors.centerIn: parent; width: parent.width * 1.17; height: width; source: "file:///usr/share/oshl/orbital/m4/core.png"; opacity: 0.35
                layer.enabled: true; layer.effect: MultiEffect { blurEnabled: true; blur: 1; blurMax: 64 } }
        Image { anchors.fill: parent; source: "file:///usr/share/oshl/orbital/m4/core.png"; smooth: true; mipmap: true }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter; anchors.top: orb.bottom; anchors.topMargin: 30 * root.u
        text: "OSHL"; color: Qt.lighter(root.accent, 1.35)
        font.family: "Orbitron"; font.pixelSize: 72 * root.u; font.bold: true; font.letterSpacing: 24 * root.u
    }
    Rectangle {
        id: bar
        anchors.horizontalCenter: parent.horizontalCenter; y: parent.height * 0.86
        width: 420 * root.u; height: 8 * root.u; radius: height / 2
        color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.15)
        border.color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.5)
        Rectangle { height: parent.height; radius: height / 2; color: root.accent
                    width: parent.width * Math.min(1, root.stage / 6); Behavior on width { NumberAnimation { duration: 400 } } }
    }
    Text {
        anchors.horizontalCenter: parent.horizontalCenter; anchors.top: bar.bottom; anchors.topMargin: 16 * root.u
        text: "INICIANDO SISTEMA"; color: Qt.rgba(root.accent.r, root.accent.g, root.accent.b, 0.8)
        font.family: "Orbitron"; font.pixelSize: 16 * root.u; font.letterSpacing: 6 * root.u
    }
}
