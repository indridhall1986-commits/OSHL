// Layout inicial do OSHL: barra de tarefas no estilo Windows +
// painel de monitoramento no estilo eDEX-UI na area de trabalho.

// ---------- Area de trabalho ----------
var desk = desktops()[0];
desk.wallpaperPlugin = "org.kde.image";
desk.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
desk.writeConfig("Image", "file:///usr/share/wallpapers/OSHL/");
desk.currentConfigGroup = [];

// Coluna de monitores no lado direito (CPU, memoria, rede, disco)
var sw = screenGeometry(desk.screen).width;
var col = sw - 380;
desk.addWidget("org.kde.plasma.systemmonitor.cpu",       col,  40, 340, 220);
desk.addWidget("org.kde.plasma.systemmonitor.memory",    col, 280, 340, 220);
desk.addWidget("org.kde.plasma.systemmonitor.net",       col, 520, 340, 220);
desk.addWidget("org.kde.plasma.systemmonitor.diskusage", col, 760, 340, 180);

// ---------- Barra de tarefas (estilo Windows) ----------
var panel = new Panel;
panel.location = "bottom";
panel.height = 46;
panel.alignment = "center";
panel.floating = false;

var start = panel.addWidget("org.kde.plasma.kickoff");   // Menu Iniciar (tecla Windows)
start.currentConfigGroup = ["General"];
start.writeConfig("icon", "start-here-kde-symbolic");

panel.addWidget("org.kde.plasma.marginsseparator");

var tasks = panel.addWidget("org.kde.plasma.icontasks"); // Apps fixados + abertos
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "preferred://filemanager",
    "preferred://browser",
    "applications:steam.desktop",
    "applications:com.heroicgameslauncher.hgl.desktop",
    "applications:org.kde.konsole.desktop"
]);

panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");             // Wi-Fi, som, bluetooth, bateria

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("fontFamily", "Fira Mono");

panel.addWidget("org.kde.plasma.showdesktop");            // Canto direito, igual Windows
