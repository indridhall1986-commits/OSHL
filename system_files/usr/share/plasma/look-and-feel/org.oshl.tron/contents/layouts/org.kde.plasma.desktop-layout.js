// Layout inicial do OSHL: barra de tarefas no estilo Windows +
// painel HUD (OSHL HUD) cobrindo a area de trabalho.

// ---------- Area de trabalho ----------
var desk = desktops()[0];
desk.wallpaperPlugin = "org.kde.image";
desk.currentConfigGroup = ["Wallpaper", "org.kde.image", "General"];
desk.writeConfig("Image", "file:///usr/share/wallpapers/OSHL-tron/");
desk.currentConfigGroup = [];

// Painel HUD em tela cheia (acima da barra de tarefas)
var geo = screenGeometry(desk.screen);
desk.addWidget("org.oshl.hud", 0, 0, geo.width, geo.height - 46);

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
clock.writeConfig("fontFamily", "Fira Mono");

panel.addWidget("org.kde.plasma.showdesktop");            // Canto direito, igual Windows
