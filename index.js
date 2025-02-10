const { app, BrowserWindow } = require("electron");

let launchWindow;

function ElectronMainMethod() {
    launchWindow = new BrowserWindow({
        title: "School System",
        width: 777,
        height: 444,
    });

    const appURL = "http://127.0.0.1:8000";
    launchWindow.loadURL(appURL);

    // When the window is closed, quit the app (this will close the terminals if needed)
    launchWindow.on("closed", () => {
        app.quit();
    });
}

app.whenReady().then(ElectronMainMethod);

app.on("window-all-closed", () => {
    if (process.platform !== "darwin") {
        app.quit();
    }
});
