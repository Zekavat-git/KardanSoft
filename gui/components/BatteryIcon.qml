import QtQuick 2.15

Item {
    id: root

    width: 52
    height: 28

    property int level: 80
    property bool charging: false

    property color goodColor: "#22C55E"
    property color warningColor: "#F59E0B"
    property color criticalColor: "#EF4444"

    property color levelColor: {
        if (level <= 15)
            return criticalColor

        if (level <= 30)
            return warningColor

        return goodColor
    }

    // Battery body
    Rectangle {
        id: batteryBody

        width: 44
        height: 22

        anchors.left: parent.left
        anchors.verticalCenter: parent.verticalCenter

        radius: 5

        color: "transparent"

        border.width: 2
        border.color: "#CBD5E1"

        // Battery charge level
        Rectangle {
            id: batteryFill

            x: 4
            y: 4

            height: parent.height - 8

            width: Math.max(
                       2,
                       (parent.width - 8) * root.level / 100
                   )

            radius: 2.5

            color: root.levelColor

            Behavior on width {
                NumberAnimation {
                    duration: 300
                    easing.type: Easing.OutCubic
                }
            }

            Behavior on color {
                ColorAnimation {
                    duration: 200
                }
            }
        }
    }

    // Battery terminal
    Rectangle {
        width: 5
        height: 10

        anchors.left: batteryBody.right
        anchors.leftMargin: 2

        anchors.verticalCenter: batteryBody.verticalCenter

        radius: 2

        color: "#CBD5E1"
    }

    // Charging lightning
    Canvas {
        id: chargingCanvas

        visible: root.charging

        width: 14
        height: 18

        anchors.centerIn: batteryBody

        onPaint: {
            var ctx = getContext("2d")

            ctx.clearRect(0, 0, width, height)

            ctx.fillStyle = "#FFFFFF"

            ctx.beginPath()

            ctx.moveTo(8, 0)
            ctx.lineTo(2, 10)
            ctx.lineTo(7, 10)
            ctx.lineTo(5, 18)
            ctx.lineTo(13, 7)
            ctx.lineTo(8, 7)

            ctx.closePath()
            ctx.fill()
        }
    }
}