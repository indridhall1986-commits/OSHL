import QtQuick
import QtQuick.Shapes
import QtQuick.Effects

// Medidor circular: aro de vidro + arco de uso que acende conforme o valor.
Item {
    id: g
    property real value: 0               // 0..100
    property string label: ""
    property string sub: ""
    property var pal
    property string fam
    property string dial
    readonly property real r: width * 0.395
    Behavior on value { NumberAnimation { duration: 700; easing.type: Easing.OutCubic } }

    Image { anchors.fill: parent; source: g.dial; smooth: true; mipmap: true; opacity: 0.9 }
    Shape {
        anchors.fill: parent
        layer.enabled: true; layer.samples: 4
        layer.effect: MultiEffect { shadowEnabled: true; shadowColor: g.pal.bright; shadowBlur: 0.7; shadowHorizontalOffset: 0; shadowVerticalOffset: 0 }
        ShapePath {
            strokeColor: g.pal.bright
            strokeWidth: g.width * 0.045
            fillColor: "transparent"
            capStyle: ShapePath.RoundCap
            PathAngleArc {
                centerX: g.width / 2; centerY: g.height / 2
                radiusX: g.r; radiusY: g.r
                startAngle: -90; sweepAngle: Math.max(0.5, Math.min(100, g.value)) * 3.6
            }
        }
    }
    Column {
        anchors.centerIn: parent
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: Math.round(g.value) + "%"
            color: "white"; font.family: g.fam; font.pixelSize: g.width * 0.2; font.bold: true
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: g.label
            color: g.pal.bright; font.family: g.fam; font.pixelSize: g.width * 0.095; font.letterSpacing: 2
        }
        Text {
            visible: g.sub !== ""
            anchors.horizontalCenter: parent.horizontalCenter
            text: g.sub
            color: Qt.rgba(1, 1, 1, 0.6); font.family: g.fam; font.pixelSize: g.width * 0.075
        }
    }
}
