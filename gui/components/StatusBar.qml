import QtQuick 2.15
import QtQuick.Controls 2.15

Item {
    id: root

    width: parent ? parent.width : 800
    height: 56

    // =========================================================
    // Public properties
    // =========================================================

    property bool ethernetConnected: false
    property bool mainsAvailable: true
    property int batteryPercent: 100
    property bool batteryCharging: false

    // Used by Main.qml
    property bool warningVisible: false

    property bool initialized: false
    property int previousBatteryState: -1

    // 0 = normal
    // 1 = low
    // 2 = critical
    readonly property int batteryState: {
        if (batteryPercent <= 15)
            return 2
        if (batteryPercent <= 30)
            return 1
        return 0
    }

    // =========================================================
    // Colors
    // =========================================================

    readonly property color greenColor: "#22C55E"
    readonly property color orangeColor: "#F59E0B"
    readonly property color redColor: "#EF4444"

    readonly property color lightColor: "#E5E7EB"
    readonly property color mutedColor: "#CBD5E1"

    readonly property color barColor: "#0F172A"
    readonly property color popupColor: "#1E293B"

    // =========================================================
    // Popup data
    // =========================================================

    property string popupTitle: ""
    property string popupMessage: ""
    property string popupType: "warning"   // success / warning / critical

    function popupAccentColor() {
        if (popupType === "success")
            return greenColor
        if (popupType === "critical")
            return redColor
        return orangeColor
    }

    function popupIconBackground() {
        if (popupType === "success")
            return "#143323"
        if (popupType === "critical")
            return "#3F1D24"
        return "#3A2C12"
    }

    function popupIconText() {
        if (popupType === "success")
            return "✓"
        if (popupType === "critical")
            return "!"
        return "!"
    }

    // =========================================================
    // Top status bar
    // =========================================================

    Rectangle {
        id: bar

        anchors.top: parent.top
        anchors.left: parent.left
        anchors.right: parent.right

        height: root.height

        color: root.barColor

        // -----------------------------------------------------
        // Network - left
        // -----------------------------------------------------

        Row {
            anchors.left: parent.left
            anchors.leftMargin: 18
            anchors.verticalCenter: parent.verticalCenter

            spacing: 8

            Text {
                text: qsTr("شبکه")
                color: root.lightColor
                font.pixelSize: 15
            }

            Rectangle {
                width: 18
                height: 18
                radius: 9

                color: root.ethernetConnected
                       ? root.greenColor
                       : root.redColor

                border.width: 2
                border.color: root.ethernetConnected
                              ? "#166534"
                              : "#7F1D1D"

                anchors.verticalCenter: parent.verticalCenter
            }
        }

        // -----------------------------------------------------
        // Power status - center
        // -----------------------------------------------------

        Row {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.verticalCenter: parent.verticalCenter

            spacing: 10

            Text {
                text: root.mainsAvailable
                      ? qsTr("برق شهر")
                      : qsTr("حالت باتری")

                color: root.lightColor
                font.pixelSize: 16

                anchors.verticalCenter: parent.verticalCenter
            }

            Canvas {
                id: powerIcon

                width: 40
                height: 40

                anchors.verticalCenter: parent.verticalCenter

                onPaint: {
                    var ctx = getContext("2d")
                    ctx.reset()

                    var color = root.mainsAvailable
                                ? root.greenColor
                                : root.orangeColor

                    ctx.strokeStyle = color
                    ctx.lineWidth = 2.5
                    ctx.lineCap = "round"
                    ctx.lineJoin = "round"

                    ctx.beginPath()
                    ctx.arc(
                        20,
                        20,
                        15,
                        -Math.PI / 4,
                        5 * Math.PI / 4
                    )
                    ctx.stroke()

                    ctx.beginPath()
                    ctx.moveTo(20, 5)
                    ctx.lineTo(20, 20)
                    ctx.stroke()
                }

                Connections {
                    target: root

                    function onMainsAvailableChanged() {
                        powerIcon.requestPaint()
                    }
                }
            }
        }

        // -----------------------------------------------------
        // Battery - right
        // -----------------------------------------------------

        Row {
            anchors.right: parent.right
            anchors.rightMargin: 22
            anchors.verticalCenter: parent.verticalCenter

            spacing: 5

            Rectangle {
                width: 4
                height: 10
                radius: 2
                color: root.lightColor
                anchors.verticalCenter: parent.verticalCenter
            }

            Item {
                id: batteryBody

                width: 48
                height: 26

                anchors.verticalCenter: parent.verticalCenter

                Rectangle {
                    anchors.fill: parent
                    radius: 5
                    color: "transparent"
                    border.width: 2
                    border.color: root.lightColor
                }

                Rectangle {
                    x: 4
                    y: 4

                    width: Math.max(
                               4,
                               (batteryBody.width - 8)
                               * Math.max(0, Math.min(100, root.batteryPercent))
                               / 100
                           )

                    height: batteryBody.height - 8
                    radius: 3

                    color: {
                        if (root.batteryPercent <= 20)
                            return root.redColor
                        if (root.batteryPercent <= 40)
                            return root.orangeColor
                        return root.greenColor
                    }

                    Behavior on width {
                        NumberAnimation {
                            duration: 250
                        }
                    }
                }

                Canvas {
                    anchors.centerIn: parent
                    width: 22
                    height: 22

                    visible: root.batteryCharging

                    onPaint: {
                        var ctx = getContext("2d")
                        ctx.reset()

                        ctx.fillStyle = "#FFFFFF"

                        ctx.beginPath()
                        ctx.moveTo(12, 1)
                        ctx.lineTo(5, 11)
                        ctx.lineTo(10, 11)
                        ctx.lineTo(8, 21)
                        ctx.lineTo(17, 9)
                        ctx.lineTo(12, 9)
                        ctx.closePath()
                        ctx.fill()
                    }
                }
            }
        }
    }

    // =========================================================
    // Modal overlay
    // =========================================================

    Rectangle {
        id: modalOverlay

        x: 0
        y: root.height

        width: root.width
        height: {
            var h = root.parent ? root.parent.height : 480
            return Math.max(0, h - root.height)
        }

        visible: root.warningVisible
        color: "#99000000"
        z: 4000

        MouseArea {
            anchors.fill: parent
            acceptedButtons: Qt.AllButtons
            onClicked: {
                // Do nothing - block clicks behind popup
            }
        }
    }

    // =========================================================
    // Popup
    // =========================================================

    Rectangle {
        id: warningCard

        width: 560
        height: 190

        x: (root.width - width) / 2
        y: {
            var h = root.parent ? root.parent.height : 480
            return (h - height) / 2
        }

        visible: root.warningVisible
        z: 5000

        radius: 18
        color: root.popupColor

        border.width: 2
        border.color: root.popupAccentColor()

        // Right stripe
        Rectangle {
            width: 7
            height: parent.height - 26

            anchors.right: parent.right
            anchors.rightMargin: 10
            anchors.verticalCenter: parent.verticalCenter

            radius: 4
            color: root.popupAccentColor()
        }

        // Icon circle
        Rectangle {
            id: popupIconCircle

            width: 48
            height: 48
            radius: 24

            anchors.right: parent.right
            anchors.rightMargin: 28
            anchors.top: parent.top
            anchors.topMargin: 22

            color: root.popupIconBackground()

            Text {
                anchors.centerIn: parent
                text: root.popupIconText()
                color: root.popupAccentColor()
                font.pixelSize: 26
                font.bold: true
            }
        }

        // Title
        Text {
            id: popupTitleText

            anchors.top: parent.top
            anchors.topMargin: 24

            anchors.right: popupIconCircle.left
            anchors.rightMargin: 16

            anchors.left: parent.left
            anchors.leftMargin: 26

            text: root.popupTitle
            color: root.lightColor

            font.pixelSize: 22
            font.bold: true

            horizontalAlignment: Text.AlignRight
        }

        // Message
        Text {
            id: popupMessageText

            anchors.top: popupTitleText.bottom
            anchors.topMargin: 14

            anchors.right: parent.right
            anchors.rightMargin: 28

            anchors.left: parent.left
            anchors.leftMargin: 26

            text: root.popupMessage
            color: root.mutedColor

            font.pixelSize: 18

            wrapMode: Text.WordWrap
            horizontalAlignment: Text.AlignRight
            lineHeight: 1.25
        }

        // Confirm button - centered and better positioned
        Button {
            id: confirmButton

            width: 130
            height: 42

            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: 16

            text: qsTr("تأیید")

            font.pixelSize: 17

            onClicked: {
                root.warningVisible = false
            }

            background: Rectangle {
                radius: 12

                color: confirmButton.pressed
                       ? "#475569"
                       : "#334155"

                border.width: 1
                border.color: "#54657D"
            }

            contentItem: Text {
                text: confirmButton.text
                color: "#F8FAFC"
                font.pixelSize: 17
                font.bold: true

                horizontalAlignment: Text.AlignHCenter
                verticalAlignment: Text.AlignVCenter
            }
        }
    }

    // =========================================================
    // Popup logic
    // =========================================================

    function showPopup(title, message, type) {
        // Replace current popup with new one
        root.warningVisible = false

        root.popupTitle = title
        root.popupMessage = message
        root.popupType = type

        Qt.callLater(function() {
            root.warningVisible = true
        })
    }

    // =========================================================
    // Status change reactions
    // =========================================================

    onMainsAvailableChanged: {
        if (!initialized)
            return

        if (mainsAvailable) {
            showPopup(
                qsTr("وضعیت برق"),
                qsTr("برق شهر مجدداً وصل شد."),
                "success"
            )
        } else {
            showPopup(
                qsTr("هشدار برق"),
                qsTr("برق شهر قطع شده است. سیستم در حال کار با باتری است."),
                "warning"
            )
        }
    }

    onBatteryStateChanged: {
        if (!initialized)
            return

        if (batteryState === previousBatteryState)
            return

        if (batteryState === 1) {
            showPopup(
                qsTr("باتری ضعیف"),
                qsTr("سطح شارژ باتری پایین است."),
                "warning"
            )
        } else if (batteryState === 2) {
            showPopup(
                qsTr("هشدار باتری"),
                qsTr("سطح شارژ باتری در وضعیت بحرانی است."),
                "critical"
            )
        }

        previousBatteryState = batteryState
    }

    // =========================================================
    // Init
    // =========================================================

    Component.onCompleted: {
        previousBatteryState = batteryState
        initialized = true
    }
}