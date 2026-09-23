import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15
import "components"
import "pages" as Pages


ApplicationWindow {
    id: root

    visible: true

    // =========================================================
    // WINDOW MODE
    // =========================================================

    width: developmentMode ? 800 : Screen.width
    height: developmentMode ? 480 : Screen.height

    visibility:
        developmentMode
        ? Window.Windowed
        : Window.FullScreen

    title: "KardanSoft"

    color: "#070D18"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    // =========================================================
    // LOGICAL GUI SIZE
    // =========================================================

    readonly property int designWidth: 800
    readonly property int designHeight: 480

    readonly property real uiScale: Math.min(
        width / designWidth,
        height / designHeight
    )


    // =========================================================
    // APPLICATION PAGE STATE
    // =========================================================

    // All pages are created exactly once at startup.
    // Navigation only changes visibility; no StackView push/pop/
    // replace and no repeated destruction/recreation of QML pages.
    property string currentPage: "idle"

    // Configurable from SettingsPage.
    // The default is 40 seconds.
    property int idleTimeoutSeconds: 40

    readonly property int idleTimeoutMs:
        idleTimeoutSeconds * 1000


    // =========================================================
    // PAGE ROUTER
    // =========================================================

    function setCurrentPage(pageName) {

        if (
            currentPage === "pattern"
            && pageName !== "pattern"
        ) {
            patternPage.deactivate()
        }

        currentPage = pageName

        console.log(
            "PAGE -> "
            + pageName
        )

        if (pageName === "open_locker") {

            openLockerPage.preparePage()
        }

        if (pageName === "idle") {

            inactivityTimer.stop()

        } else {

            inactivityTimer.restart()
        }
    }


    function showHomePage() {

        setCurrentPage("home")
    }


    function showIdlePage() {

        // Session lifetime ends only when returning to Idle.
        authManager.logoutAll()

        setCurrentPage("idle")
    }


    function requestProtectedPage(target) {

        // If this session already has the required authorization,
        // go directly to the persistent destination page.
        if (authManager.isAuthorized(target)) {

            if (target === "settings")
                setCurrentPage("settings")
            else
                setCurrentPage("open_locker")

            return
        }

        // Otherwise reuse the same persistent PatternLockPage.
        patternPage.prepareForTarget(target)

        setCurrentPage("pattern")
    }


    function handlePatternAuthorized(target) {

        if (!authManager.isAuthorized(target)) {

            console.log(
                "AUTHORIZATION STATE ERROR -> "
                + target
            )

            showHomePage()
            return
        }

        if (target === "settings")
            setCurrentPage("settings")
        else
            setCurrentPage("open_locker")
    }


    function backToMenu() {

        setCurrentPage("home")
    }


    function notifyUserActivity() {

        if (currentPage === "idle") {

            showHomePage()
            return
        }

        inactivityTimer.restart()
    }


    // =========================================================
    // LOGICAL 800 x 480 SURFACE
    // =========================================================

    Item {
        id: designSurface

        width: root.designWidth
        height: root.designHeight

        anchors.centerIn: parent

        transformOrigin: Item.Center
        scale: root.uiScale


        // =====================================================
        // PERSISTENT PAGES
        // =====================================================

        Pages.IdlePage {
            id: idlePage

            anchors.fill: parent

            visible:
                root.currentPage === "idle"

            enabled:
                visible

            z:
                visible ? 10 : 0
        }


        Pages.HomePage {
            id: homePage

            anchors.fill: parent

            visible:
                root.currentPage === "home"

            enabled:
                visible

            z:
                visible ? 10 : 0

            onProtectedPageRequested: function(target) {

                root.requestProtectedPage(
                    target
                )
            }
        }


        Pages.PatternLockPage {
            id: patternPage

            anchors.fill: parent

            visible:
                root.currentPage === "pattern"

            enabled:
                visible

            z:
                visible ? 10 : 0

            onAuthorized: function(target) {

                root.handlePatternAuthorized(
                    target
                )
            }
        }


        Pages.OpenLockerPage {
            id: openLockerPage

            anchors.fill: parent

            visible:
                root.currentPage === "open_locker"

            enabled:
                visible

            z:
                visible ? 10 : 0

            onBackRequested: {

                root.backToMenu()
            }
        }


        Pages.SettingsPage {
            id: settingsPage

            anchors.fill: parent

            visible:
                root.currentPage === "settings"

            enabled:
                visible

            z:
                visible ? 10 : 0

            idleTimeoutSeconds:
                root.idleTimeoutSeconds

            onIdleTimeoutRequested: function(seconds) {

                root.idleTimeoutSeconds =
                    Math.max(
                        10,
                        Math.min(
                            300,
                            seconds
                        )
                    )

                // Changing the setting is itself user activity,
                // so the new interval starts from this interaction.
                root.notifyUserActivity()

                console.log(
                    "IDLE TIMEOUT -> "
                    + root.idleTimeoutSeconds
                    + " s"
                )
            }

            onBackRequested: {

                root.backToMenu()
            }
        }


        // =====================================================
        // GLOBAL STATUS BAR
        // =====================================================

        StatusBar {
            id: globalStatusBar

            anchors.top: parent.top
            anchors.left: parent.left
            anchors.right: parent.right

            z: 3000

            ethernetConnected:
                appState.ethernetConnected

            mainsAvailable:
                appState.mainsAvailable

            batteryPercent:
                appState.batteryPercent

            batteryCharging:
                appState.batteryCharging
        }


        // =====================================================
        // RETURN TO FIRST PAGE
        // =====================================================

        Button {
            id: goToIdleButton

            visible:
                root.currentPage !== "idle"
                &&
                !globalStatusBar.warningVisible

            z: 2500

            width: 155
            height: 42

            anchors.left: parent.left
            anchors.leftMargin: 18

            anchors.bottom: parent.bottom
            anchors.bottomMargin: 16

            text:
                qsTr("بازگشت به صفحه اول")


            onClicked: {

                root.showIdlePage()
            }


            background: Rectangle {

                radius: 12

                color:
                    goToIdleButton.pressed
                    ? "#475569"
                    : "#334155"

                border.width: 1
                border.color: "#54657D"
            }


            contentItem: Text {

                text:
                    goToIdleButton.text

                color: "#F8FAFC"

                font.pixelSize: 14
                font.bold: true

                horizontalAlignment:
                    Text.AlignHCenter

                verticalAlignment:
                    Text.AlignVCenter
            }
        }


        // =====================================================
        // GLOBAL USER ACTIVITY
        // =====================================================

        TapHandler {
            id: globalActivityHandler

            enabled:
                !globalStatusBar.warningVisible

            // Restart on physical press/release. This also covers
            // touch screens, not only mouse clicks.
            onPressedChanged: {

                root.notifyUserActivity()
            }

            // Keep the completed-tap notification as a fallback.
            onTapped: {

                root.notifyUserActivity()
            }
        }
    }


    // =========================================================
    // INACTIVITY TIMER
    // =========================================================

    Timer {
        id: inactivityTimer

        interval:
            root.idleTimeoutMs

        repeat: false


        onTriggered: {

            // Do not hide an active warning popup.
            if (
                globalStatusBar.warningVisible
            ) {

                restart()
                return
            }

            root.showIdlePage()
        }
    }
}
