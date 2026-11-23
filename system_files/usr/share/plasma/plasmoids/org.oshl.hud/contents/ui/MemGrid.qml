import QtQuick

// Matriz de pontos: proporcao de memoria em uso
Item {
    id: m
    property var t
    property real u: 1
    property real ratio: 0

    onRatioChanged: cv.requestPaint()
    onTChanged: cv.requestPaint()
    onWidthChanged: cv.requestPaint()
    onHeightChanged: cv.requestPaint()

    Canvas {
        id: cv
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (!m.t) return
            var cell = Math.max(4, Math.round(6 * m.u))
            var cols = Math.floor(width / cell), rows = Math.floor(height / cell)
            var n = cols * rows, filled = Math.round(m.ratio * n)
            for (var k = 0; k < n; k++) {
                var used = k < filled
                ctx.fillStyle = used ? m.t.accent : m.t.dim
                ctx.globalAlpha = used ? (Math.random() < 0.12 ? 0.4 : 0.95) : 0.5
                ctx.fillRect(Math.floor(k / rows) * cell, (k % rows) * cell, cell - 2, cell - 2)
            }
            ctx.globalAlpha = 1
        }
    }
}
