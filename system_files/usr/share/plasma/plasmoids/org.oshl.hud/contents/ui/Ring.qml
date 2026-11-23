import QtQuick

// Medidor circular com marcacoes (0-100)
Item {
    id: r
    property var t
    property real u: 1
    property real value: 0
    property string center: Math.round(value) + "%"
    property string sub: ""
    property string label: ""
    property real thick: Math.max(3, width * 0.06)

    onValueChanged: cv.requestPaint()
    onTChanged: cv.requestPaint()
    onWidthChanged: cv.requestPaint()
    onHeightChanged: cv.requestPaint()

    Canvas {
        id: cv
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (!r.t) return
            var cx = width / 2, cy = height / 2
            var R = Math.min(width, height) / 2 - 8
            if (R <= r.thick + 6) return
            ctx.strokeStyle = r.t.accent
            ctx.lineWidth = 1
            for (var i = 0; i < 60; i++) {
                var a = i / 60 * 2 * Math.PI
                var r1 = R - 1, r2 = R + (i % 5 === 0 ? 6 : 3)
                ctx.globalAlpha = i % 5 === 0 ? 0.8 : 0.3
                ctx.beginPath()
                ctx.moveTo(cx + r1 * Math.cos(a), cy + r1 * Math.sin(a))
                ctx.lineTo(cx + r2 * Math.cos(a), cy + r2 * Math.sin(a))
                ctx.stroke()
            }
            ctx.globalAlpha = 1
            var rad = R - r.thick / 2 - 4
            ctx.lineWidth = r.thick
            ctx.strokeStyle = r.t.dim
            ctx.beginPath()
            ctx.arc(cx, cy, rad, 0, 2 * Math.PI)
            ctx.stroke()
            var v = Math.max(0, Math.min(100, r.value)) / 100
            if (v > 0) {
                ctx.strokeStyle = r.t.accent
                ctx.beginPath()
                ctx.arc(cx, cy, rad, -Math.PI / 2, -Math.PI / 2 + v * 2 * Math.PI, false)
                ctx.stroke()
            }
            ctx.lineWidth = 1
            ctx.strokeStyle = r.t.accent
            ctx.globalAlpha = 0.35
            ctx.beginPath()
            ctx.arc(cx, cy, rad - r.thick / 2 - 5, 0, 2 * Math.PI)
            ctx.stroke()
            ctx.globalAlpha = 1
        }
    }

    Column {
        anchors.centerIn: parent
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            text: r.center
            color: r.t.bright
            font.family: "Fira Mono"
            font.pixelSize: Math.max(8, r.width * 0.19)
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: r.sub !== ""
            text: r.sub
            color: r.t.accent
            font.family: "Fira Mono"
            font.pixelSize: Math.max(7, r.width * 0.09)
        }
        Text {
            anchors.horizontalCenter: parent.horizontalCenter
            visible: r.label !== ""
            text: r.label
            color: r.t.accent
            opacity: 0.7
            font.family: "Fira Mono"
            font.pixelSize: Math.max(7, r.width * 0.075)
            font.letterSpacing: 2
        }
    }
}
