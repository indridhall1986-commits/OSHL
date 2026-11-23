import QtQuick

// Globo de pontos girando, com "pings" de rede
Item {
    id: gl
    property var t
    property real angle: 0
    property var pts: []
    property var pings: []

    Component.onCompleted: {
        var a = [], n = 650, gold = Math.PI * (3 - Math.sqrt(5))
        for (var i = 0; i < n; i++) {
            var y = 1 - (i / (n - 1)) * 2, rr = Math.sqrt(1 - y * y), th = gold * i
            a.push([Math.cos(th) * rr, y, Math.sin(th) * rr])
        }
        pts = a
    }

    Timer {
        interval: 50
        running: gl.visible
        repeat: true
        onTriggered: {
            gl.angle += 0.01
            var p = []
            for (var i = 0; i < gl.pings.length; i++)
                if (gl.pings[i].life > 0) p.push({ i: gl.pings[i].i, life: gl.pings[i].life - 1 })
            if (Math.random() < 0.04 && gl.pts.length) p.push({ i: Math.floor(Math.random() * gl.pts.length), life: 40 })
            gl.pings = p
            cv.requestPaint()
        }
    }

    Canvas {
        id: cv
        anchors.fill: parent
        onPaint: {
            var ctx = getContext("2d")
            ctx.reset()
            if (!gl.t || !gl.pts.length) return
            var cx = width / 2, cy = height / 2, R = Math.min(width, height) / 2 * 0.86
            var ca = Math.cos(gl.angle), sa = Math.sin(gl.angle), tl = 0.4, ct = Math.cos(tl), stl = Math.sin(tl)
            function proj(p) {
                var x = p[0] * ca + p[2] * sa, z = -p[0] * sa + p[2] * ca, y = p[1]
                return [x, y * ct - z * stl, y * stl + z * ct]
            }
            ctx.strokeStyle = gl.t.accent
            ctx.globalAlpha = 0.25
            ctx.lineWidth = 1
            ctx.beginPath(); ctx.arc(cx, cy, R, 0, 2 * Math.PI); ctx.stroke()
            ctx.fillStyle = gl.t.accent
            for (var i = 0; i < gl.pts.length; i++) {
                var q = proj(gl.pts[i])
                ctx.globalAlpha = q[2] < 0 ? 0.1 : 0.3 + 0.7 * q[2]
                ctx.fillRect(cx + q[0] * R, cy + q[1] * R, 2, 2)
            }
            for (var k = 0; k < gl.pings.length; k++) {
                var pg = gl.pings[k], s = proj(gl.pts[pg.i])
                if (s[2] < 0) continue
                var px = cx + s[0] * R, py = cy + s[1] * R, life = pg.life / 40
                ctx.globalAlpha = life
                ctx.strokeStyle = gl.t.bright
                ctx.beginPath(); ctx.arc(px, py, (1 - life) * 14 + 2, 0, 2 * Math.PI); ctx.stroke()
                ctx.beginPath(); ctx.moveTo(px, py); ctx.lineTo(px + s[0] * 25, py + s[1] * 25); ctx.stroke()
            }
            ctx.globalAlpha = 1
        }
    }
}
