import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "file:///usr/share/oshl/dashboard"

// Monitor do sistema OSHL (widget da area de trabalho).
PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    OshlData { id: dados; wantStats: true }
    fullRepresentation: Item {
        Layout.preferredWidth: 290; Layout.preferredHeight: 379
        Layout.minimumWidth: 140; Layout.minimumHeight: 183
        HoverHandler { id: hv }
        OrganicMonitor {
            anchors.centerIn: parent
            width: Math.min(parent.width, parent.height * 928 / 1211)
            pal: dados.pal; fam: dados.fam; stats: dados.stats
            frame: dados.asset("w2/frame.png"); row: dados.asset("w2/row.png"); rowSel: dados.asset("w2/row-sel.png")
            CloseBtn { show: hv.hovered; pal: dados.pal; onClicked: Plasmoid.internalAction("remove").trigger() }
        }
    }
}
