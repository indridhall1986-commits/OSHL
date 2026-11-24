import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "file:///usr/share/oshl/dashboard"

// Relogio holografico OSHL (widget da area de trabalho). Tamanho: arraste a borda no modo de edicao.
PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    OshlData { id: dados; wantStats: true }
    fullRepresentation: Item {
        Layout.preferredWidth: 300; Layout.preferredHeight: 333
        Layout.minimumWidth: 120; Layout.minimumHeight: 133
        HoverHandler { id: hv }
        HoloClock {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height * 1023 / 1135)
            pal: dados.pal; fam: dados.fam
            emblem: dados.asset("w2/emblem.png"); sphere: dados.asset("w2/sphere.png")
            CloseBtn { show: hv.hovered; pal: dados.pal; onClicked: Plasmoid.internalAction("remove").trigger() }
        }
    }
}
