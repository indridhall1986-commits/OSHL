import QtQuick
import QtQuick.Effects

// Relogio analogico: mostrador de vidro + ponteiros de vidro girando no eixo detectado.
Item {
    id: c
    property var pal
    property string dial
    property string handHour
    property string handMin
    property var pivots: ({ "hand-hour": { pivot_x: 0.5, pivot_y: 0.70 }, "hand-min": { pivot_x: 0.5, pivot_y: 0.688 } })
    property date now: new Date()
    readonly property real dd: Math.min(width, height)
    Timer { interval: 250; running: true; repeat: true; onTriggered: c.now = new Date() }

    Image { anchors.fill: parent; source: c.dial; smooth: true; mipmap: true }

    // Ponteiro: imagem quadrada com o eixo em (px, py); 'len' = comprimento do eixo ate a ponta.
    component Hand: Image {
        property real len
        property real px: 0.5
        property real py: 0.69
        property real tipY: 0.035
        property real ang: 0
        readonly property real sz: len / (py - tipY)
        width: sz; height: sz
        x: c.width / 2 - sz * px; y: c.height / 2 - sz * py
        smooth: true; mipmap: true
        transform: Rotation { origin.x: sz * px; origin.y: sz * py; angle: ang }
    }
    Hand {
        source: c.handHour
        px: c.pivots["hand-hour"].pivot_x; py: c.pivots["hand-hour"].pivot_y; tipY: 0.088
        len: c.dd * 0.25
        ang: ((c.now.getHours() % 12) + c.now.getMinutes() / 60) * 30
    }
    Hand {
        source: c.handMin
        px: c.pivots["hand-min"].pivot_x; py: c.pivots["hand-min"].pivot_y; tipY: 0.034
        len: c.dd * 0.36
        ang: (c.now.getMinutes() + c.now.getSeconds() / 60) * 6
    }
    Hand {                                         // segundos: ponteiro de minutos afinado
        id: secHand
        source: c.handMin
        px: c.pivots["hand-min"].pivot_x; py: c.pivots["hand-min"].pivot_y; tipY: 0.034
        len: c.dd * 0.39
        opacity: 0.85
        layer.enabled: true
        layer.effect: MultiEffect { brightness: 0.3 }
        transform: [
            Scale { origin.x: secHand.width * secHand.px; origin.y: secHand.height * secHand.py; xScale: 0.45 },
            Rotation { origin.x: secHand.width * secHand.px; origin.y: secHand.height * secHand.py; angle: c.now.getSeconds() * 6 + c.now.getMilliseconds() * 0.006 }
        ]
    }
}
