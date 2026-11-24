// Layout inicial do OSHL: barra de tarefas de vidro no estilo Windows +
// widgets OSHL soltos na area de trabalho (menu da esfera, relogio, sistema, placa de video).

// ---------- Area de trabalho ----------
var desk = desktops()[0];
desk.wallpaperPlugin = "org.kde.image";
desk.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
desk.writeConfig("Image", "file:///usr/share/wallpapers/OSHL-tron/");
desk.currentConfigGroup = [];

// Widgets OSHL (botao direito na area de trabalho > Adicionar widgets para por/tirar)
var geo = screenGeometry(desk.screen);
desk.addWidget("org.oshl.menu", 40, Math.round(geo.height * 0.18), 760, 480);
desk.addWidget("org.oshl.relogio", geo.width - 340, 20, 300, 333);
desk.addWidget("org.oshl.sistema", geo.width - 330, 380, 290, 379);
desk.addWidget("org.oshl.gpu", 40, geo.height - 60 - 190, 340, 167);

// ---------- Barra de tarefas (estilo Windows) ----------
var panel = new Panel;
panel.location = "bottom";
panel.height = 60;
panel.alignment = "center";
panel.floating = false;

var start = panel.addWidget("org.kde.plasma.kickoff");   // Menu Iniciar (tecla Windows)
start.currentConfigGroup = ["General"];
start.writeConfig("icon", "oshl-orb");

panel.addWidget("org.kde.plasma.marginsseparator");

var tasks = panel.addWidget("org.kde.plasma.icontasks"); // Apps fixados + abertos
tasks.currentConfigGroup = ["General"];
tasks.writeConfig("launchers", [
    "preferred://filemanager",
    "preferred://browser",
    "applications:steam.desktop",
    "applications:org.strawberrymusicplayer.strawberry.desktop",
    "applications:org.kde.konsole.desktop",
    "applications:oshl-temas.desktop"
]);

panel.addWidget("org.kde.plasma.panelspacer");
panel.addWidget("org.kde.plasma.systemtray");             // Wi-Fi, som, bluetooth, bateria

var clock = panel.addWidget("org.kde.plasma.digitalclock");
clock.currentConfigGroup = ["Appearance"];
clock.writeConfig("showDate", "true");
clock.writeConfig("dateFormat", "shortDate");
clock.writeConfig("fontFamily", "Orbitron");
clock.writeConfig("autoFontAndSize", "false");
clock.writeConfig("fontSize", "11");

panel.addWidget("org.kde.plasma.showdesktop");            // Canto direito, igual Windows
