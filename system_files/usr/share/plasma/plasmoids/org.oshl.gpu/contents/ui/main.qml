import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "file:///usr/share/oshl/dashboard"

// Ficha da placa de video OSHL (widget da area de trabalho).
PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    OshlData { id: dados; wantStats: true }
    fullRepresentation: Item {
        Layout.preferredWidth: 340; Layout.preferredHeight: 167
        Layout.minimumWidth: 170; Layout.minimumHeight: 84
        HoverHandler { id: hv }
        InfoCard {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height * 1400 / 688)
            pal: dados.pal; fam: dados.fam
            card: dados.asset("w2/card.png")
            title: "PLACA DE VIDEO"; tag: dados.stats.gpuName || "GPU"
            fields: [{ k: "USO", v: Math.round(dados.stats.gpu) + "%" },
                     { k: "TEMP", v: Math.round(dados.stats.gpuTemp) + "°C" },
                     { k: "VRAM", v: (dados.stats.vramUsed / 1024).toFixed(1) + " GB" }]
            CloseBtn { show: hv.hovered; pal: dados.pal; onClicked: Plasmoid.internalAction("remove").trigger() }
        }
    }
}
