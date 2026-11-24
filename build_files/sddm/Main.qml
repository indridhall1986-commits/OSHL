import QtQuick
import QtQuick.Effects

// Tela de login OSHL (SDDM): papel de parede do tema escurecido, relogio no topo, cartao de vidro
// com a esfera, nome do usuario, senha em capsula e botoes-bolha Desligar / Reiniciar / Suspender.
// Cores e fundo vem do theme.conf (gerado por tema). So usa QtQuick: se algo falhar, o SDDM cai
// no tema interno dele (o login continua possivel).
Rectangle {
    id: root
    width: 1920; height: 1080
    color: "#020401"
    readonly property real u: Math.min(width / 1920, height / 1080)
    readonly property color accent: config.accent || "#b9e52b"
    readonly property color bright: config.bright || "#f3ff8f"
    readonly property bool tint: config.tint === "true"
    readonly property string fam: "Orbitron"
    function al(c, a) { var q = Qt.lighter(c, 1.0); return Qt.rgba(q.r, q.g, q.b, a) }
    property int userIdx: userModel.lastIndex >= 0 ? userModel.lastIndex : 0
    property string userName: userModel.lastUser || ""
    property string userReal: ""
    property bool failed: false
    property date now: new Date()
    Timer { interval: 1000; running: true; repeat: true; onTriggered: root.now = new Date() }
    readonly property var dias: ["DOMINGO", "SEGUNDA", "TERCA", "QUARTA", "QUINTA", "SEXTA", "SABADO"]
    readonly property var meses: ["JANEIRO", "FEVEREIRO", "MARCO", "ABRIL", "MAIO", "JUNHO", "JULHO", "AGOSTO", "SETEMBRO", "OUTUBRO", "NOVEMBRO", "DEZEMBRO"]

    Connections {
        target: sddm
        function onLoginFailed() { root.failed = true; pass.text = ""; pass.forceActiveFocus(); shake.restart() }
        function onLoginSucceeded() { root.failed = false }
    }
    function login() { root.failed = false; sddm.login(root.userName, pass.text, sessionModel.lastIndex >= 0 ? sessionModel.lastIndex : 0) }

    // nome do usuario (o lembrado; senao o primeiro da lista)
    Repeater {
        model: userModel
        Item {
            required property int index
            required property string name
            required property string realName
            Component.onCompleted: if ((root.userName === "" && index === 0) || name === root.userName) {
                root.userName = name; root.userReal = realName
            }
        }
    }

    Item {
        id: scene
        anchors.fill: parent
        Image { anchors.fill: parent; source: config.background || ""; fillMode: Image.PreserveAspectCrop; asynchronous: false }
        Rectangle { anchors.fill: parent; color: "black"; opacity: 0.45 }
    }

    Text { x: 50 * root.u; y: 40 * root.u; text: "OSHL"; color: root.al(root.bright, 0.7)
           font.family: root.fam; font.pixelSize: 30 * root.u; font.bold: true; font.letterSpacing: 10 * root.u }
    Column {
        anchors.horizontalCenter: parent.horizontalCenter; y: 40 * root.u; spacing: 4 * root.u
        Text { anchors.horizontalCenter: parent.horizontalCenter; text: Qt.formatTime(root.now, "hh:mm"); color: "white"
               font.family: root.fam; font.bold: true; font.pixelSize: 40 * root.u; font.letterSpacing: 6 * root.u }
        Text { anchors.horizontalCenter: parent.horizontalCenter
               text: root.dias[root.now.getDay()] + ", " + root.now.getDate() + " DE " + root.meses[root.now.getMonth()]
               color: root.bright; font.family: root.fam; font.pixelSize: 15 * root.u; font.letterSpacing: 5 * root.u }
    }

    // ---------------- cartao de vidro
    Item {
        id: card
        anchors.horizontalCenter: parent.horizontalCenter
        y: parent.height * 0.22
        width: 520 * root.u; height: 470 * root.u
        transform: Translate { id: shakeT; x: 0 }
        SequentialAnimation { id: shake
            NumberAnimation { target: shakeT; property: "x"; to: 14 * root.u; duration: 50 }
            NumberAnimation { target: shakeT; property: "x"; to: -14 * root.u; duration: 80 }
            NumberAnimation { target: shakeT; property: "x"; to: 0; duration: 60 } }
        ShaderEffectSource { id: ses; anchors.fill: parent; visible: false; sourceItem: scene
            sourceRect: Qt.rect(card.x, card.y, card.width, card.height) }
        Rectangle { id: mk; anchors.fill: parent; radius: 28 * root.u; visible: false; layer.enabled: true }
        MultiEffect { anchors.fill: parent; source: ses; blurEnabled: true; blur: 1; blurMax: 64; maskEnabled: true; maskSource: mk }
        Rectangle { anchors.fill: parent; radius: 28 * root.u; color: "#050a02"; opacity: 0.5 }
        Rectangle { anchors.fill: parent; radius: 28 * root.u; color: "transparent"; border.color: root.accent; border.width: 1.5; opacity: 0.6 }

        Image { anchors.horizontalCenter: parent.horizontalCenter; y: 30 * root.u; width: 170 * root.u; height: width
                source: "core.png"; smooth: true; mipmap: true
                layer.enabled: root.tint; layer.effect: MultiEffect { colorization: 1.0; colorizationColor: root.accent } }
        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 214 * root.u
               text: (root.userReal || root.userName || "USUARIO").toUpperCase()
               color: root.bright; font.family: root.fam; font.pixelSize: 30 * root.u; font.bold: true; font.letterSpacing: 6 * root.u }
        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 258 * root.u; text: "OSHL // " + (config.themeName || "ORBITAL")
               color: root.al(root.accent, 0.85); font.family: root.fam; font.pixelSize: 14 * root.u; font.letterSpacing: 5 * root.u }
        Rectangle {
            anchors.horizontalCenter: parent.horizontalCenter; y: 310 * root.u
            width: 400 * root.u; height: 58 * root.u; radius: height / 2
            color: root.al("black", 0.45); border.color: root.failed ? "#ff5c5c" : root.al(root.accent, 0.8); border.width: 1.5
            TextInput {
                id: pass
                anchors.fill: parent; anchors.leftMargin: 26 * root.u; anchors.rightMargin: 64 * root.u
                verticalAlignment: TextInput.AlignVCenter
                echoMode: TextInput.Password; passwordCharacter: "●"
                color: root.bright; font.pixelSize: 19 * root.u; font.letterSpacing: 4 * root.u
                focus: true
                Keys.onReturnPressed: root.login()
                Keys.onEnterPressed: root.login()
                Text { anchors.verticalCenter: parent.verticalCenter; visible: !pass.text; text: "Senha"
                       color: root.al(root.bright, 0.45); font.pixelSize: 19 * root.u }
            }
            Item { anchors.right: parent.right; anchors.rightMargin: 4 * root.u; anchors.verticalCenter: parent.verticalCenter
                   width: 50 * root.u; height: width
                Image { anchors.fill: parent; source: "bubble.png"
                        layer.enabled: root.tint; layer.effect: MultiEffect { colorization: 1.0; colorizationColor: root.accent } }
                Text { anchors.centerIn: parent; text: "›"; color: "white"; font.pixelSize: 30 * root.u; font.bold: true }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor; onClicked: root.login() } }
        }
        Text { anchors.horizontalCenter: parent.horizontalCenter; y: 392 * root.u
               text: root.failed ? "SENHA INCORRETA - TENTE DE NOVO" : (keyboard.capsLock ? "CAPS LOCK LIGADO" : "ENTER PARA ENTRAR")
               color: root.failed ? "#ff8080" : root.al(root.bright, 0.55); font.family: root.fam; font.pixelSize: 12 * root.u; font.letterSpacing: 4 * root.u }
    }

    // ---------------- energia
    Row {
        anchors.horizontalCenter: parent.horizontalCenter; anchors.bottom: parent.bottom; anchors.bottomMargin: 50 * root.u
        spacing: 40 * root.u
        Repeater {
            model: [["⏻", "DESLIGAR", 0], ["↻", "REINICIAR", 1], ["☾", "SUSPENDER", 2]]
            Item {
                required property var modelData
                visible: modelData[2] === 0 ? sddm.canPowerOff : modelData[2] === 1 ? sddm.canReboot : sddm.canSuspend
                width: lab.x + lab.implicitWidth; height: 60 * root.u
                Image { id: bi; width: 54 * root.u; height: width; source: "bubble.png"
                        layer.enabled: root.tint; layer.effect: MultiEffect { colorization: 1.0; colorizationColor: root.accent } }
                Text { anchors.centerIn: bi; text: modelData[0]; color: "white"; font.pixelSize: 22 * root.u }
                Text { id: lab; x: bi.width + 12 * root.u; anchors.verticalCenter: bi.verticalCenter; text: modelData[1]
                       color: root.al(root.bright, 0.85); font.family: root.fam; font.pixelSize: 15 * root.u; font.letterSpacing: 3 * root.u }
                MouseArea { anchors.fill: parent; cursorShape: Qt.PointingHandCursor
                    onClicked: modelData[2] === 0 ? sddm.powerOff() : modelData[2] === 1 ? sddm.reboot() : sddm.suspend() }
            }
        }
    }
    Component.onCompleted: pass.forceActiveFocus()
}
