import QtQuick

// Moldura de vidro esticavel (9 partes): os cantos nao deformam em nenhum tamanho.
Item {
    id: f
    property string source
    property real thickness: 40          // espessura visual da borda, em pixels
    readonly property real srcBorder: 235 // borda na imagem original (1194 x 1176)
    readonly property real k: thickness / srcBorder
    BorderImage {
        width: f.width / f.k; height: f.height / f.k
        transformOrigin: Item.TopLeft
        scale: f.k
        source: f.source
        border { left: f.srcBorder; right: f.srcBorder; top: f.srcBorder; bottom: f.srcBorder }
        horizontalTileMode: BorderImage.Stretch; verticalTileMode: BorderImage.Stretch
        smooth: true
    }
}
