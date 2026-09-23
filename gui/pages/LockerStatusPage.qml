import QtQuick 2.15
import QtQuick.Controls 2.15


Rectangle {
    id: root

    objectName: "lockerStatusPage"

    signal backRequested()

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    // =========================================================
    // STATUS HELPERS
    // =========================================================

    function statusText(
        actualState,
        expectedState,
        fault
    ) {

        if (fault === "unexpected_open")
            return qsTr("باز شدن غیرمجاز")

        if (fault === "failed_to_open")
            return qsTr("عدم باز شدن")

        if (fault === "communication_lost")
            return qsTr("قطع ارتباط")

        if (fault !== "none")
            return qsTr("خطا")

        if (actualState === "open")
            return qsTr("باز")

        if (actualState === "unknown")
            return qsTr("نامشخص")

        if (expectedState === "open")
            return qsTr("در حال باز شدن")

        return qsTr("بسته / آماده")
    }


    function cardColor(
        actualState,
        expectedState,
        fault
    ) {

        if (fault !== "none")
            return "#3F1D24"

        if (actualState === "open")
            return "#3A2C12"

        if (actualState === "unknown")
            return "#1E293B"

        if (expectedState === "open")
            return "#13384A"

        return "#153526"
    }


    function borderColor(
        actualState,
        expectedState,
        fault
    ) {

        if (fault !== "none")
            return "#EF4444"

        if (actualState === "open")
            return "#F59E0B"

        if (actualState === "unknown")
            return "#64748B"

        if (expectedState === "open")
            return "#38BDF8"

        return "#22C55E"
    }


    function statusColor(
        actualState,
        expectedState,
        fault
    ) {

        if (fault !== "none")
            return "#F87171"

        if (actualState === "open")
            return "#FBBF24"

        if (actualState === "unknown")
            return "#94A3B8"

        if (expectedState === "open")
            return "#7DD3FC"

        return "#86EFAC"
    }


    // =========================================================
    // TITLE
    // =========================================================

    Text {
        id: titleText

        anchors.top: parent.top
        anchors.topMargin: 68

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("وضعیت کمدها")

        color: "#F8FAFC"

        font.pixelSize: 27
        font.bold: true
    }


    Text {
        id: subtitleText

        anchors.top:
            titleText.bottom

        anchors.topMargin: 2

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("وضعیت لحظه‌ای کمدها و خطاهای سخت‌افزاری")

        color: "#94A3B8"

        font.pixelSize: 14
    }


    // =========================================================
    // BACK TO MENU
    // =========================================================

    Button {
        id: backButton

        width: 135
        height: 38

        anchors.left:
            parent.left

        anchors.leftMargin: 18

        anchors.top:
            parent.top

        anchors.topMargin: 70

        text:
            qsTr("بازگشت به منو")


        onClicked: {

            root.backRequested()
        }


        background: Rectangle {

            radius: 10

            color:
                backButton.pressed
                ? "#475569"
                : "#253247"

            border.width: 1
            border.color: "#475569"
        }


        contentItem: Text {

            text:
                backButton.text

            color: "#E2E8F0"

            font.pixelSize: 14

            horizontalAlignment:
                Text.AlignHCenter

            verticalAlignment:
                Text.AlignVCenter
        }
    }


    // =========================================================
    // LOCKER GRID
    // =========================================================

    Rectangle {
        id: gridContainer

        width: 680
        height: 254

        anchors.top:
            subtitleText.bottom

        anchors.topMargin: 14

        anchors.horizontalCenter:
            parent.horizontalCenter

        radius: 16

        color: "#111C2F"

        border.width: 1
        border.color: "#26364D"


        GridView {
            id: lockerGrid

            anchors.fill: parent
            anchors.margins: 10

            clip: true

            model: lockerModel

            cellWidth: 160
            cellHeight: 78

            boundsBehavior:
                Flickable.StopAtBounds


            ScrollBar.vertical:
                ScrollBar {

                    policy:
                        ScrollBar.AsNeeded
                }


            delegate: Item {

                width:
                    lockerGrid.cellWidth

                height:
                    lockerGrid.cellHeight


                Rectangle {
                    id: lockerCard

                    width: 148
                    height: 68

                    anchors.centerIn:
                        parent

                    radius: 13

                    color:
                        root.cardColor(
                            actualState,
                            expectedState,
                            fault
                        )

                    border.width: 2

                    border.color:
                        root.borderColor(
                            actualState,
                            expectedState,
                            fault
                        )


                    Column {
                        anchors.centerIn:
                            parent

                        width: 132

                        spacing: 1


                        Text {
                            width: parent.width

                            text:
                                qsTr("کمد ")
                                + lockerId

                            color: "#F8FAFC"

                            font.pixelSize: 18
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {
                            width: parent.width

                            text:
                                root.statusText(
                                    actualState,
                                    expectedState,
                                    fault
                                )

                            color:
                                root.statusColor(
                                    actualState,
                                    expectedState,
                                    fault
                                )

                            font.pixelSize: 12
                            font.bold:
                                fault !== "none"

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {
                            width: parent.width

                            text:
                                qsTr("برد ")
                                + slaveAddress
                                + qsTr("  •  کانال ")
                                + channel

                            color: "#64748B"

                            font.pixelSize: 10

                            horizontalAlignment:
                                Text.AlignHCenter
                        }
                    }
                }
            }
        }
    }


    // =========================================================
    // LEGEND
    // =========================================================

    Row {
        anchors.top:
            gridContainer.bottom

        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter

        spacing: 20


        Row {
            spacing: 6

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: "#22C55E"
                anchors.verticalCenter:
                    parent.verticalCenter
            }

            Text {
                text: qsTr("آماده")
                color: "#94A3B8"
                font.pixelSize: 11
            }
        }


        Row {
            spacing: 6

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: "#F59E0B"
                anchors.verticalCenter:
                    parent.verticalCenter
            }

            Text {
                text: qsTr("باز")
                color: "#94A3B8"
                font.pixelSize: 11
            }
        }


        Row {
            spacing: 6

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: "#38BDF8"
                anchors.verticalCenter:
                    parent.verticalCenter
            }

            Text {
                text: qsTr("در حال باز شدن")
                color: "#94A3B8"
                font.pixelSize: 11
            }
        }


        Row {
            spacing: 6

            Rectangle {
                width: 10
                height: 10
                radius: 5
                color: "#EF4444"
                anchors.verticalCenter:
                    parent.verticalCenter
            }

            Text {
                text: qsTr("خطا")
                color: "#94A3B8"
                font.pixelSize: 11
            }
        }
    }
}
