import QtQuick
import QtQuick.Effects

// Imagem de arte que acompanha a cor do tema (fica igual no ORBITAL/MATRIZ).
Image {
    property bool tint: false
    property color tintColor: "white"
    smooth: true; mipmap: true
    layer.enabled: tint
    layer.effect: MultiEffect { colorization: 1.0; colorizationColor: tintColor }
}
