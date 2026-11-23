import QtQuick

// Grafico de linha com grade (historico). values2 = segunda serie opcional.
Item {
    id: g
    property var t
    property var values: []
    property var values2: null
    property real maxValue: 100
    property bool autoMax: false
    property int capacity: 120

    onValuesChanged: cv.requestPaint()
    onTChanged: cv.requestPaint()
    onWidthChanged: cv.requestPaint()
    onHeightChanged: cv.requestPaint()

    function series(ctx, arr, mx, color, w, h, doFill) {
        if (!arr || arr.length < 2) return
        var step = w / (g.capacity - 1)
        var x0 = w - (arr.length - 1) * step
        ctx.beginPath()
        for (var i = 0; i < arr.length; i++) {
            var x = x0 + i * step
            var y = h - Math.min(1, arr[i] / mx) * (h - 2) - 1
            if (i === 0) ctx.moveTo(x, y)
            else ctx.lineTo(x, y)
        }
        ctx.strokeStyle = color
        ctx.lineWidth = 1.5
        ctx.stroke()
        if (doFill) {
            ctx.lineTo(w, h)
            ctx.lineTo(x0, h)
            ctx.closePath()
            ctx.fillStyle = color
            ctx.globalAlpha = 0.13
            ctx.fill()
            ctx.globalAlpha = 1
        }
    }

    Canvas {
        id: cv
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (!g.t) return
            var w = width, h = height
            ctx.strokeStyle = g.t.dim
            ctx.lineWidth = 1
            for (var i = 1; i < 4; i++) {
                var y = Math.round(h * i / 4) + 0.5
                ctx.beginPath(); ctx.moveTo(0, y); ctx.lineTo(w, y); ctx.stroke()
            }
            for (var j = 1; j < 8; j++) {
                var x = Math.round(w * j / 8) + 0.5
                ctx.beginPath(); ctx.moveTo(x, 0); ctx.lineTo(x, h); ctx.stroke()
            }
            var mx = g.maxValue
            if (g.autoMax) {
                mx = 1
                var all = (g.values || []).concat(g.values2 || [])
                for (var k = 0; k < all.length; k++) mx = Math.max(mx, all[k])
                mx *= 1.15
            }
            g.series(ctx, g.values, mx, g.t.accent, w, h, true)
            if (g.values2) g.series(ctx, g.values2, mx, g.t.bright, w, h, false)
        }
    }
}
