import QtQuick 2.15
import QtQuick.Controls 2.15


Rectangle {
    id: root

    objectName: "openLockerPage"

    // Main.qml owns all navigation.
    signal backRequested()

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    // =========================================================
    // SELECTION
    // =========================================================

    property var selectedLockers: []

    property string pageMessage:
        qsTr("یک یا چند کمد را انتخاب کنید")


    // =========================================================
    // CHECK SELECTION
    // =========================================================

    function isSelected(lockerId) {

        return (
            selectedLockers.indexOf(
                lockerId
            ) !== -1
        )
    }


    // =========================================================
    // TOGGLE SELECTION
    // =========================================================

    function toggleLocker(lockerId) {

        var newList =
            selectedLockers.slice()

        var index =
            newList.indexOf(
                lockerId
            )

        if (index === -1) {

            newList.push(
                lockerId
            )

        } else {

            newList.splice(
                index,
                1
            )
        }

        selectedLockers =
            newList
    }


    // =========================================================
    // REMOVE SELECTION
    // =========================================================

    function removeSelection(lockerId) {

        var newList =
            selectedLockers.slice()

        var index =
            newList.indexOf(
                lockerId
            )

        if (index === -1)
            return

        newList.splice(
            index,
            1
        )

        selectedLockers =
            newList
    }


    // =========================================================
    // CLEAR
    // =========================================================

    function clearSelection() {

        selectedLockers = []
    }


    function preparePage() {

        selectedLockers = []

        pageMessage =
            qsTr("یک یا چند کمد را انتخاب کنید")
    }


    // =========================================================
    // STATUS TEXT
    // =========================================================

    function lockerStatusText(
        actualState,
        expectedState,
        fault
    ) {

        if (fault !== "none")
            return qsTr("خطا")

        if (actualState === "open")
            return qsTr("باز")

        if (actualState === "unknown")
            return qsTr("نامشخص")

        if (
            expectedState === "open"
        )
            return qsTr("در حال باز شدن")

        return qsTr("آماده")
    }


    // =========================================================
    // TITLE
    // =========================================================

    Text {
        id: titleText

        anchors.top:
            parent.top

        anchors.topMargin: 68

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("باز کردن کمدها")

        color: "#F8FAFC"

        font.pixelSize: 27
        font.bold: true
    }


    Text {
        id: subtitleText

        anchors.top:
            titleText.bottom

        anchors.topMargin: 1

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr(
                "کمدهای مورد نظر را انتخاب کنید"
            )

        color: "#94A3B8"

        font.pixelSize: 15
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
        height: 235

        anchors.top:
            subtitleText.bottom

        anchors.topMargin: 12

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
            cellHeight: 72

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


                property bool selectable:
                    actualState === "closed"
                    &&
                    expectedState === "closed"
                    &&
                    fault === "none"


                property bool selected:
                    root.isSelected(
                        lockerId
                    )


                Rectangle {
                    id: lockerCard

                    width: 148
                    height: 62

                    anchors.centerIn:
                        parent

                    radius: 13

                    border.width:
                        selected ? 3 : 2


                    border.color: {

                        if (selected)
                            return "#38BDF8"

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


                    color: {

                        if (selected)
                            return "#123A54"

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


                    Column {

                        anchors.centerIn:
                            parent

                        spacing: 0


                        Text {

                            width: 125

                            text:
                                qsTr("کمد ")
                                + lockerId

                            color: "#F8FAFC"

                            font.pixelSize: 19
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {

                            width: 125

                            text:
                                root.lockerStatusText(
                                    actualState,
                                    expectedState,
                                    fault
                                )

                            color: {

                                if (selected)
                                    return "#7DD3FC"

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

                            font.pixelSize: 13

                            horizontalAlignment:
                                Text.AlignHCenter
                        }
                    }


                    MouseArea {

                        anchors.fill:
                            parent


                        onClicked: {

                            if (!selectable) {

                                root.pageMessage =
                                    qsTr("کمد ")
                                    + lockerId
                                    + qsTr(
                                        " در حال حاضر قابل انتخاب نیست"
                                    )

                                return
                            }


                            root.toggleLocker(
                                lockerId
                            )


                            if (
                                root.selectedLockers.length
                                === 0
                            ) {

                                root.pageMessage =
                                    qsTr(
                                        "یک یا چند کمد را انتخاب کنید"
                                    )

                            } else {

                                root.pageMessage =
                                    root.selectedLockers.length
                                    + qsTr(
                                        " کمد انتخاب شده است"
                                    )
                            }
                        }
                    }
                }
            }
        }
    }


    // =========================================================
    // MESSAGE
    // =========================================================

    Text {
        id: messageText

        anchors.top:
            gridContainer.bottom

        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            root.pageMessage

        color: "#CBD5E1"

        font.pixelSize: 14
    }


    // =========================================================
    // ACTION BAR
    // =========================================================

    Row {
        id: actionRow

        anchors.top:
            messageText.bottom

        anchors.topMargin: 7

        anchors.horizontalCenter:
            parent.horizontalCenter

        spacing: 12


        Button {
            id: clearButton

            width: 135
            height: 42

            enabled:
                root.selectedLockers.length > 0


            text:
                qsTr("پاک کردن انتخاب")


            onClicked: {

                root.clearSelection()

                root.pageMessage =
                    qsTr(
                        "یک یا چند کمد را انتخاب کنید"
                    )
            }


            background: Rectangle {

                radius: 11

                color:
                    !clearButton.enabled
                    ? "#1E293B"
                    : clearButton.pressed
                      ? "#475569"
                      : "#334155"

                border.width: 1
                border.color: "#475569"
            }


            contentItem: Text {

                text:
                    clearButton.text

                color:
                    clearButton.enabled
                    ? "#F8FAFC"
                    : "#64748B"

                font.pixelSize: 14

                horizontalAlignment:
                    Text.AlignHCenter

                verticalAlignment:
                    Text.AlignVCenter
            }
        }


        Button {
            id: openSelectedButton

            width: 210
            height: 42


            enabled:
                root.selectedLockers.length > 0
                &&
                !lockerController.batchBusy


            text: {

                if (
                    lockerController.batchBusy
                )
                    return qsTr(
                        "در حال اجرای فرمان‌ها..."
                    )


                if (
                    root.selectedLockers.length
                    === 0
                )
                    return qsTr(
                        "باز کردن کمد"
                    )


                return (
                    qsTr("باز کردن ")
                    + root.selectedLockers.length
                    + qsTr(" کمد")
                )
            }


            onClicked: {

                var count =
                    lockerController.openLockers(
                        root.selectedLockers
                    )


                if (count > 0) {

                    root.pageMessage =
                        count
                        + qsTr(
                            " کمد در صف باز شدن قرار گرفت"
                        )

                    root.clearSelection()
                }
            }


            background: Rectangle {

                radius: 11


                color: {

                    if (
                        !openSelectedButton.enabled
                    )
                        return "#1E293B"


                    if (
                        openSelectedButton.pressed
                    )
                        return "#0369A1"


                    return "#0284C7"
                }


                border.width: 1

                border.color:
                    openSelectedButton.enabled
                    ? "#38BDF8"
                    : "#334155"
            }


            contentItem: Text {

                text:
                    openSelectedButton.text

                color:
                    openSelectedButton.enabled
                    ? "#FFFFFF"
                    : "#64748B"

                font.pixelSize: 15
                font.bold: true

                horizontalAlignment:
                    Text.AlignHCenter

                verticalAlignment:
                    Text.AlignVCenter
            }
        }
    }


    // =========================================================
    // LIVE CONTROLLER EVENTS
    // =========================================================

    Connections {
        target: lockerController


        function onStatusChanged(message) {

            root.pageMessage =
                message
        }


        function onLockerStateChanged(
            lockerId,
            actualState,
            fault
        ) {

            if (
                actualState !== "closed"
                ||
                fault !== "none"
            ) {

                root.removeSelection(
                    lockerId
                )
            }
        }
    }
}
