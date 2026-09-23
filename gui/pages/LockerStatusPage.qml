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

    function occupancyText(
        occupancyState
    ) {

        return (
            occupancyState === "occupied"
            ? qsTr("پر")
            : qsTr("آزاد")
        )
    }


    function physicalText(
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

        return qsTr("بسته")
    }


    function combinedStatusText(
        occupancyState,
        actualState,
        expectedState,
        fault
    ) {

        return (
            occupancyText(
                occupancyState
            )
            + qsTr(" • ")
            + physicalText(
                actualState,
                expectedState,
                fault
            )
        )
    }


    function cardColor(
        occupancyState,
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

        if (occupancyState === "occupied")
            return "#261D45"

        return "#153526"
    }


    function borderColor(
        occupancyState,
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

        if (occupancyState === "occupied")
            return "#8B5CF6"

        return "#22C55E"
    }


    function statusColor(
        occupancyState,
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

        if (occupancyState === "occupied")
            return "#C4B5FD"

        return "#86EFAC"
    }


    // =========================================================
    // TITLE
    // =========================================================

    Text {
        id: titleText

        anchors.top: parent.top
        anchors.topMargin: 63

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("وضعیت کمدها")

        color: "#F8FAFC"

        font.pixelSize: 25
        font.bold: true
    }


    Text {
        id: subtitleText

        anchors.top:
            titleText.bottom

        anchors.topMargin: 0

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr(
                "وضعیت تخصیص، درب و خطاهای کمدها"
            )

        color: "#94A3B8"

        font.pixelSize: 12
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
    // LIVE SUMMARY
    // =========================================================

    Row {
        id: summaryRow

        anchors.top:
            subtitleText.bottom

        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter

        spacing: 7


        Rectangle {
            width: 122
            height: 46
            radius: 11
            color: "#122A22"
            border.width: 1
            border.color: "#22C55E"

            Row {
                anchors.centerIn: parent
                spacing: 7

                Text {
                    text:
                        lockerModel.freeCount

                    color: "#86EFAC"
                    font.pixelSize: 21
                    font.bold: true
                }

                Text {
                    text: qsTr("آزاد")
                    color: "#CBD5E1"
                    font.pixelSize: 12
                }
            }
        }


        Rectangle {
            width: 122
            height: 46
            radius: 11
            color: "#261D45"
            border.width: 1
            border.color: "#8B5CF6"

            Row {
                anchors.centerIn: parent
                spacing: 7

                Text {
                    text:
                        lockerModel.occupiedCount

                    color: "#C4B5FD"
                    font.pixelSize: 21
                    font.bold: true
                }

                Text {
                    text: qsTr("پر")
                    color: "#CBD5E1"
                    font.pixelSize: 12
                }
            }
        }


        Rectangle {
            width: 122
            height: 46
            radius: 11
            color: "#302513"
            border.width: 1
            border.color: "#F59E0B"

            Row {
                anchors.centerIn: parent
                spacing: 7

                Text {
                    text:
                        lockerModel.openCount

                    color: "#FBBF24"
                    font.pixelSize: 21
                    font.bold: true
                }

                Text {
                    text: qsTr("باز")
                    color: "#CBD5E1"
                    font.pixelSize: 12
                }
            }
        }


        Rectangle {
            width: 122
            height: 46
            radius: 11
            color: "#351B22"
            border.width: 1
            border.color: "#EF4444"

            Row {
                anchors.centerIn: parent
                spacing: 7

                Text {
                    text:
                        lockerModel.faultCount

                    color: "#F87171"
                    font.pixelSize: 21
                    font.bold: true
                }

                Text {
                    text: qsTr("خطا")
                    color: "#CBD5E1"
                    font.pixelSize: 12
                }
            }
        }


        Rectangle {
            width: 122
            height: 46
            radius: 11
            color: "#1B2535"
            border.width: 1
            border.color: "#64748B"

            Row {
                anchors.centerIn: parent
                spacing: 7

                Text {
                    text:
                        lockerModel.unknownCount

                    color: "#CBD5E1"
                    font.pixelSize: 21
                    font.bold: true
                }

                Text {
                    text: qsTr("نامشخص")
                    color: "#CBD5E1"
                    font.pixelSize: 11
                }
            }
        }
    }


    // =========================================================
    // LOCKER GRID
    // =========================================================

    Rectangle {
        id: gridContainer

        width: 680
        height:
            developmentMode
            ? 181
            : 210

        anchors.top:
            summaryRow.bottom

        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter

        radius: 16

        color: "#111C2F"

        border.width: 1
        border.color: "#26364D"


        GridView {
            id: lockerGrid

            anchors.fill: parent
            anchors.margins: 7

            clip: true

            model: lockerModel

            cellWidth: 160
            cellHeight: 58

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
                    width: 148
                    height: 52

                    anchors.centerIn:
                        parent

                    radius: 11

                    color:
                        root.cardColor(
                            occupancyState,
                            actualState,
                            expectedState,
                            fault
                        )

                    border.width: 2

                    border.color:
                        root.borderColor(
                            occupancyState,
                            actualState,
                            expectedState,
                            fault
                        )


                    Column {
                        anchors.centerIn:
                            parent

                        width: 132

                        spacing: 0


                        Text {
                            width: parent.width

                            text:
                                qsTr("کمد ")
                                + lockerId

                            color: "#F8FAFC"

                            font.pixelSize: 15
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {
                            width: parent.width

                            text:
                                root.combinedStatusText(
                                    occupancyState,
                                    actualState,
                                    expectedState,
                                    fault
                                )

                            color:
                                root.statusColor(
                                    occupancyState,
                                    actualState,
                                    expectedState,
                                    fault
                                )

                            font.pixelSize: 10
                            font.bold:
                                fault !== "none"
                                ||
                                occupancyState === "occupied"

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {
                            width: parent.width

                            text:
                                occupancyState === "occupied"
                                && assignedTo.length > 0
                                ? assignedTo
                                : (
                                    qsTr("برد ")
                                    + slaveAddress
                                    + qsTr("  •  کانال ")
                                    + channel
                                )

                            color: "#64748B"

                            font.pixelSize: 9

                            elide:
                                Text.ElideRight

                            horizontalAlignment:
                                Text.AlignHCenter
                        }
                    }
                }
            }
        }
    }


    // =========================================================
    // FOOTER
    // =========================================================

    Text {
        anchors.top:
            gridContainer.bottom

        anchors.topMargin: 6

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("تعداد کل کمدها: ")
            + lockerModel.totalCount

        color: "#64748B"

        font.pixelSize: 11
    }
}
