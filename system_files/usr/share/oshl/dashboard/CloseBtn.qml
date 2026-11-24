import QtQuick

// Botao de fechar widget: aparece ao passar o mouse sobre o widget (show = hover do pai).
Rectangle {
    id: b
    property bool show: false
    property var pal
    signal clicked()
    width: 30; height: 30; radius: 15
    anchors.right: parent.right; anchors.top: parent.top
    color: ma.containsMouse ? b.pal.accent : Qt.rgba(0, 0, 0, 0.55)
    border.color: b.pal.bright; border.width: 1.5
    opacity: b.show || ma.containsMouse ? 1 : 0
    Behavior on opacity { NumberAnimation { duration: 150 } }
    Text { anchors.centerIn: parent; text: "✕"; color: "white"; font.pixelSize: 15; font.bold: true }
    MouseArea { id: ma; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: b.clicked() }
}
