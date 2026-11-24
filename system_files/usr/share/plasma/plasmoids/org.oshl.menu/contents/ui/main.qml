import QtQuick
import QtQuick.Layouts
import org.kde.plasma.plasmoid
import org.kde.plasma.core as PlasmaCore
import "file:///usr/share/oshl/dashboard"

// Menu OSHL: esfera + menu em carrossel, solto na area de trabalho (janelas ficam por cima).
// Rodinha / setas giram, clique ou Enter abre, Esc ou clique na esfera volta. Tecla E troca o estilo.
PlasmoidItem {
    id: root
    Plasmoid.backgroundHints: PlasmaCore.Types.NoBackground
    preferredRepresentation: fullRepresentation
    OshlData { id: dados; wantStats: true; wantMenus: true }
    fullRepresentation: Item {
        Layout.preferredWidth: 760; Layout.preferredHeight: 480
        Layout.minimumWidth: 380; Layout.minimumHeight: 240
        HoverHandler { id: hv; onHoveredChanged: if (hovered) menu.forceActiveFocus() }
        OrbMenu {
            id: menu
            anchors.fill: parent
            pal: dados.pal; fam: dados.fam; menus: dados.menus; vidro: dados.vidro; assetDir: dados.assetDir
            onSoundReq: function (n) { dados.sound(n) }
            onLaunchReq: function (cmd, label) { dados.launch(cmd) }
            onActionReq: function (a) { if (a === "style") dados.toggleStyle() }
            Keys.onPressed: function (ev) { if (ev.key === Qt.Key_E) { dados.toggleStyle(); ev.accepted = true } }
        }
        CloseBtn { show: hv.hovered; pal: dados.pal; onClicked: Plasmoid.internalAction("remove").trigger() }
    }
}
