import QtQuick 2.15

Item {
    id: root

    width: 34
    height: 34

    property bool mainsAvailable: true

    property color activeColor: "#22C55E"
    property color batteryColor: "#F59E0B"

    property color iconColor:
        mainsAvailable ? activeColor : batteryColor

    Rectangle {
        anchors.fill: parent

        radius: width / 2

        color: root.mainsAvailable
               ? "#142A20"
               : "#2D2414"
    }

    Canvas {
        id: powerCanvas

        anchors.centerIn: parent

        width: 22
        height: 22

        onPaint: {
            var ctx = getContext("2d")

            ctx.clearRect(0, 0, width, height)

            ctx.strokeStyle = root.iconColor
            ctx.lineWidth = 2.4
            ctx.lineCap = "round"

            // Vertical power line
            ctx.beginPath()
            ctx.moveTo(width / 2, 2)
            ctx.lineTo(width / 2, 10)
            ctx.stroke()

            // Circular part of power symbol
            ctx.beginPath()

            ctx.arc(
                width / 2,
                height / 2 + 1,
                8,
                -0.75,
                Math.PI + 0.75,
                false
            )

            ctx.stroke()
        }

        Connections {
            target: root

            function onIconColorChanged() {
                powerCanvas.requestPaint()
            }
        }
    }
}