import QtQuick 2.15
import QtQuick.Controls 2.15


Rectangle {
    id: root

    objectName: "settingsPage"

    signal backRequested()

    // In Production this signal will be connected to the real
    // RS485/UART diagnostic backend.
    signal slaveTestRequested(int slaveAddress)

    // Main.qml owns the inactivity timer. Settings only requests
    // a new timeout value.
    signal idleTimeoutRequested(int seconds)

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true

    Component.onCompleted: {
        console.log(
            "SETTINGS PAGE | v3.4.1 SAFE | LOADED"
        )
    }


    // =========================================================
    // THEME
    // =========================================================

    readonly property color panelColor: "#111C2F"
    readonly property color cardColor: "#172337"
    readonly property color borderColor: "#334155"
    readonly property color accentColor: "#38BDF8"
    readonly property color accentSoftColor: "#23344D"
    readonly property color textColor: "#F8FAFC"
    readonly property color subTextColor: "#94A3B8"
    readonly property color greenColor: "#22C55E"
    readonly property color redColor: "#EF4444"


    // =========================================================
    // SETTINGS STATE
    // =========================================================

    property string currentSection: "network"

    property string deviceIp: "192.168.1.134"
    property string subnetMask: "255.255.255.0"
    property string gatewayIp: "192.168.1.1"
    property string tcpPort: "5000"

    property string transportType: "RS485"
    property string baudRate: "115200"

    property string slaveCount: "1"
    property int totalLockerCount: 12

    // Bound from Main.qml. Default remains 40 seconds.
    property int idleTimeoutSeconds: 40

    // Pattern-change UI state
    property bool patternChangeVisible: false
    property string patternChangeRole: "operator"
    // 0 = verify current pattern
    // 1 = enter new pattern
    // 2 = confirm new pattern
    property int patternChangeStep: 0
    property string firstPatternValue: ""
    property var patternSelectedNodes: []
    property bool patternDrawing: false
    property real patternPointerX: 0
    property real patternPointerY: 0
    property int patternVerificationState: 0
    property string patternMessage: ""

    // Hardware UI state
    property string openHardwareDropdown: ""
    property bool slaveConfigVisible: false


    ListModel {
        id: slaveConfigModel

        ListElement {
            slaveAddress: 1
            activeChannels: 12
            communicationState: "unknown"
            deviceIdentifier: ""
        }
    }


    function syncSlaveConfigModel(
        requestedCount
    ) {

        var count =
            parseInt(
                requestedCount
            )

        if (isNaN(count))
            count = 1

        count =
            Math.max(
                1,
                Math.min(
                    32,
                    count
                )
            )

        root.slaveCount =
            count.toString()

        while (
            slaveConfigModel.count
            < count
        ) {

            slaveConfigModel.append(
                {
                    "slaveAddress":
                        slaveConfigModel.count + 1,

                    "activeChannels":
                        12,

                    "communicationState":
                        "unknown",

                    "deviceIdentifier":
                        ""
                }
            )
        }

        while (
            slaveConfigModel.count
            > count
        ) {

            slaveConfigModel.remove(
                slaveConfigModel.count - 1
            )
        }

        recalculateTotalLockers()
    }


    function recalculateTotalLockers() {

        var total = 0

        for (
            var i = 0;
            i < slaveConfigModel.count;
            i++
        ) {

            total +=
                slaveConfigModel.get(
                    i
                ).activeChannels
        }

        root.totalLockerCount =
            total
    }


    function changeActiveChannels(
        rowIndex,
        delta
    ) {

        if (
            rowIndex < 0
            || rowIndex >= slaveConfigModel.count
        ) {
            return
        }

        var current =
            slaveConfigModel.get(
                rowIndex
            ).activeChannels

        var next =
            Math.max(
                0,
                Math.min(
                    12,
                    current + delta
                )
            )

        slaveConfigModel.setProperty(
            rowIndex,
            "activeChannels",
            next
        )

        recalculateTotalLockers()
    }


    function activeChannelRange(
        count
    ) {

        if (count <= 0)
            return qsTr("غیرفعال")

        return (
            qsTr("کانال‌های 1 تا ")
            + count
        )
    }


    function addSlave() {

        if (slaveConfigModel.count >= 32)
            return

        slaveConfigModel.append(
            {
                "slaveAddress":
                    slaveConfigModel.count + 1,

                "activeChannels":
                    12,

                "communicationState":
                    "unknown",

                "deviceIdentifier":
                    ""
            }
        )

        root.slaveCount =
            slaveConfigModel.count.toString()

        recalculateTotalLockers()
    }


    function removeLastSlave() {

        if (slaveConfigModel.count <= 1)
            return

        slaveConfigModel.remove(
            slaveConfigModel.count - 1
        )

        root.slaveCount =
            slaveConfigModel.count.toString()

        recalculateTotalLockers()
    }


    function slaveStateText(
        state
    ) {

        if (state === "online")
            return qsTr("متصل")

        if (state === "offline")
            return qsTr("بدون پاسخ")

        if (state === "checking")
            return qsTr("در حال بررسی")

        return qsTr("بررسی نشده")
    }


    function slaveStateColor(
        state
    ) {

        if (state === "online")
            return root.greenColor

        if (state === "offline")
            return root.redColor

        if (state === "checking")
            return root.accentColor

        return root.subTextColor
    }


    function findSlaveRow(
        slaveAddress
    ) {

        for (
            var i = 0;
            i < slaveConfigModel.count;
            i++
        ) {

            if (
                slaveConfigModel.get(
                    i
                ).slaveAddress
                === slaveAddress
            ) {
                return i
            }
        }

        return -1
    }


    function updateSlaveDiagnostic(
        slaveAddress,
        state,
        identifier
    ) {

        var row =
            findSlaveRow(
                slaveAddress
            )

        if (row < 0)
            return

        slaveConfigModel.setProperty(
            row,
            "communicationState",
            state
        )

        if (
            identifier !== undefined
            && identifier !== null
        ) {

            slaveConfigModel.setProperty(
                row,
                "deviceIdentifier",
                identifier
            )
        }
    }


    function requestSlaveDiagnostic(
        rowIndex,
        slaveAddress
    ) {

        if (
            rowIndex < 0
            || rowIndex >= slaveConfigModel.count
        ) {
            return
        }

        slaveConfigModel.setProperty(
            rowIndex,
            "communicationState",
            "checking"
        )

        if (developmentMode) {

            diagnosticSimulationTimer.targetRow =
                rowIndex

            diagnosticSimulationTimer.targetSlave =
                slaveAddress

            diagnosticSimulationTimer.restart()

        } else {

            root.slaveTestRequested(
                slaveAddress
            )
        }
    }


    Timer {
        id: diagnosticSimulationTimer

        property int targetRow: -1
        property int targetSlave: -1

        interval: 450
        repeat: false

        onTriggered: {

            if (
                targetRow < 0
                || targetRow >= slaveConfigModel.count
            ) {
                return
            }

            // Development-only identifier. In production this field
            // will contain the actual identifier returned by the slave.
            var suffix =
                targetSlave < 10
                ? "0" + targetSlave
                : targetSlave.toString()

            slaveConfigModel.setProperty(
                targetRow,
                "communicationState",
                "online"
            )

            slaveConfigModel.setProperty(
                targetRow,
                "deviceIdentifier",
                "SIM-SLAVE-" + suffix
            )
        }
    }


    function setTotalLockerCount(
        requestedTotal
    ) {

        var total =
            parseInt(
                requestedTotal
            )

        if (isNaN(total))
            total = 1

        total =
            Math.max(
                1,
                Math.min(
                    384,
                    total
                )
            )

        var neededSlaves =
            Math.ceil(
                total / 12
            )

        syncSlaveConfigModel(
            neededSlaves
        )

        var remaining =
            total

        for (
            var i = 0;
            i < slaveConfigModel.count;
            i++
        ) {

            var channels =
                Math.min(
                    12,
                    remaining
                )

            slaveConfigModel.setProperty(
                i,
                "activeChannels",
                channels
            )

            remaining -=
                channels
        }

        recalculateTotalLockers()
    }


    function applyLockerConfiguration() {

        var channelCounts = []

        for (
            var i = 0;
            i < slaveConfigModel.count;
            i++
        ) {

            channelCounts.push(
                slaveConfigModel.get(
                    i
                ).activeChannels
            )
        }

        var success =
            lockerManager.configureLockersCsv(
                channelCounts.join(",")
            )

        if (!success) {

            console.log(
                "SETTINGS | LOCKER CONFIG | REJECTED"
            )

            return
        }

        root.totalLockerCount =
            lockerModel.totalCount

        root.slaveCount =
            slaveConfigModel.count.toString()

        console.log(
            "SETTINGS | LOCKER CONFIG | APPLIED | "
            + "Total="
            + lockerModel.totalCount
        )

        root.slaveConfigVisible =
            false
    }


    function idleTimeoutText(
        seconds
    ) {

        if (seconds < 60) {

            return (
                seconds
                + qsTr(" ثانیه")
            )
        }

        var minutes =
            Math.floor(
                seconds / 60
            )

        var remaining =
            seconds % 60

        if (remaining === 0) {

            return (
                minutes
                + qsTr(" دقیقه")
            )
        }

        return (
            minutes
            + qsTr(" دقیقه و ")
            + remaining
            + qsTr(" ثانیه")
        )
    }


    // =========================================================
    // PATTERN CHANGE
    // =========================================================

    function patternRoleName() {

        return (
            root.patternChangeRole === "admin"
            ? qsTr("مدیر")
            : qsTr("اپراتور")
        )
    }


    function openPatternChanger(
        roleName
    ) {

        root.patternChangeRole =
            roleName

        root.patternChangeStep = 0
        root.firstPatternValue = ""

        root.patternSelectedNodes = []
        root.patternDrawing = false
        root.patternPointerX = 0
        root.patternPointerY = 0
        root.patternVerificationState = 0

        root.patternMessage =
            qsTr("ابتدا پترن فعلی ")
            + root.patternRoleName()
            + qsTr(" را وارد کنید")

        root.patternChangeVisible =
            true

        patternChangeCanvas.requestPaint()
    }


    function closePatternChanger() {

        patternChangeErrorTimer.stop()
        patternChangeSuccessTimer.stop()

        root.patternChangeVisible =
            false

        root.patternDrawing =
            false
    }


    function resetPatternDrawing() {

        root.patternSelectedNodes = []
        root.patternDrawing = false
        root.patternPointerX = 0
        root.patternPointerY = 0
        root.patternVerificationState = 0

        patternChangeCanvas.requestPaint()
    }


    function addPatternNode(
        nodeNumber
    ) {

        if (
            root.patternSelectedNodes.indexOf(
                nodeNumber
            ) !== -1
        ) {
            return
        }

        var updated =
            root.patternSelectedNodes.slice()

        updated.push(
            nodeNumber
        )

        root.patternSelectedNodes =
            updated

        patternChangeCanvas.requestPaint()
    }


    function checkPatternNodeAt(
        x,
        y
    ) {

        for (
            var i = 0;
            i < 9;
            i++
        ) {

            var dx =
                x
                - patternChangeBoard.nodeCenterX(
                    i
                )

            var dy =
                y
                - patternChangeBoard.nodeCenterY(
                    i
                )

            var distance =
                Math.sqrt(
                    dx * dx
                    + dy * dy
                )

            if (distance <= 27) {

                root.addPatternNode(
                    i + 1
                )

                return
            }
        }
    }


    function submitNewPattern() {

        if (
            root.patternSelectedNodes.length
            < 4
        ) {

            root.patternVerificationState =
                -1

            root.patternMessage =
                qsTr(
                    "پترن باید حداقل ۴ نقطه داشته باشد"
                )

            patternChangeCanvas.requestPaint()
            patternChangeErrorTimer.restart()

            return
        }

        var currentPattern =
            root.patternSelectedNodes.join(
                "-"
            )

        // -----------------------------------------------------
        // STEP 0: verify the CURRENT pattern of the exact role.
        // Operator must enter the current operator pattern.
        // Admin must enter the current admin pattern.
        // -----------------------------------------------------

        if (
            root.patternChangeStep === 0
        ) {

            var currentIsValid =
                authManager.verifyRolePattern(
                    root.patternChangeRole,
                    currentPattern
                )

            if (!currentIsValid) {

                root.patternVerificationState =
                    -1

                root.patternMessage =
                    qsTr("پترن فعلی ")
                    + root.patternRoleName()
                    + qsTr(" اشتباه است")

                patternChangeCanvas.requestPaint()
                patternChangeErrorTimer.restart()

                return
            }

            root.patternVerificationState =
                1

            root.patternMessage =
                qsTr("پترن فعلی صحیح است")

            patternChangeCanvas.requestPaint()
            patternCurrentSuccessTimer.restart()

            return
        }

        // -----------------------------------------------------
        // STEP 1: capture the NEW pattern.
        // -----------------------------------------------------

        if (
            root.patternChangeStep === 1
        ) {

            root.firstPatternValue =
                currentPattern

            root.patternChangeStep = 2

            root.resetPatternDrawing()

            root.patternMessage =
                qsTr(
                    "برای تأیید، پترن جدید را دوباره رسم کنید"
                )

            return
        }

        // -----------------------------------------------------
        // STEP 2: confirmation of the NEW pattern.
        // -----------------------------------------------------

        if (
            currentPattern
            !== root.firstPatternValue
        ) {

            root.patternVerificationState =
                -1

            root.patternMessage =
                qsTr(
                    "دو پترن جدید یکسان نیستند؛ دوباره تلاش کنید"
                )

            patternChangeCanvas.requestPaint()
            patternChangeErrorTimer.restart()

            return
        }

        var result =
            authManager.changePattern(
                root.patternChangeRole,
                currentPattern
            )

        if (result === false) {

            root.patternVerificationState =
                -1

            root.patternMessage =
                qsTr(
                    "تغییر پترن انجام نشد"
                )

            patternChangeCanvas.requestPaint()
            patternChangeErrorTimer.restart()

            return
        }

        root.patternVerificationState =
            1

        root.patternMessage =
            qsTr("پترن ")
            + root.patternRoleName()
            + qsTr(" با موفقیت تغییر کرد")

        patternChangeCanvas.requestPaint()
        patternChangeSuccessTimer.restart()
    }



    Timer {
        id: patternChangeErrorTimer

        interval: 850
        repeat: false

        onTriggered: {

            root.resetPatternDrawing()

            if (
                root.patternChangeStep === 0
            ) {

                root.patternMessage =
                    qsTr("ابتدا پترن فعلی ")
                    + root.patternRoleName()
                    + qsTr(" را وارد کنید")

            } else if (
                root.patternChangeStep === 1
            ) {

                root.patternMessage =
                    qsTr("پترن جدید ")
                    + root.patternRoleName()
                    + qsTr(" را رسم کنید")

            } else {

                root.patternMessage =
                    qsTr(
                        "برای تأیید، پترن جدید را دوباره رسم کنید"
                    )
            }
        }
    }


    Timer {
        id: patternCurrentSuccessTimer

        interval: 450
        repeat: false

        onTriggered: {

            root.patternChangeStep = 1
            root.resetPatternDrawing()

            root.patternMessage =
                qsTr("پترن جدید ")
                + root.patternRoleName()
                + qsTr(" را رسم کنید")
        }
    }


    Timer {
        id: patternChangeSuccessTimer

        interval: 900
        repeat: false

        onTriggered:
            root.closePatternChanger()
    }


    // =========================================================
    // KEYPAD STATE
    // =========================================================

    property string keypadTarget: ""
    property string keypadTitle: ""
    property string keypadValue: ""
    property bool keypadAllowDot: false


    function openKeypad(
        target,
        title,
        value,
        allowDot
    ) {
        keypadTarget = target
        keypadTitle = title
        keypadValue = value
        keypadAllowDot = allowDot

        numericKeypad.open()
    }


    function applyKeypadValue() {

        if (keypadTarget === "ip")
            deviceIp = keypadValue

        else if (keypadTarget === "subnet")
            subnetMask = keypadValue

        else if (keypadTarget === "gateway")
            gatewayIp = keypadValue

        else if (keypadTarget === "port")
            tcpPort = keypadValue

        else if (keypadTarget === "slave_count")
            syncSlaveConfigModel(
                keypadValue
            )

        else if (keypadTarget === "total_lockers")
            setTotalLockerCount(
                keypadValue
            )

        numericKeypad.close()
    }


    function keypadAppend(
        value
    ) {

        if (value === ".") {

            if (!keypadAllowDot)
                return
        }

        keypadValue += value
    }


    function keypadBackspace() {

        if (keypadValue.length > 0) {

            keypadValue =
                keypadValue.substring(
                    0,
                    keypadValue.length - 1
                )
        }
    }


    // =========================================================
    // HEADER
    // =========================================================

    Text {
        id: pageTitle

        anchors.top: parent.top
        anchors.topMargin: 64

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("تنظیمات")

        color: root.textColor

        font.pixelSize: 27
        font.bold: true
    }


    Button {
        id: backButton

        width: 135
        height: 38

        anchors.left: parent.left
        anchors.leftMargin: 18

        anchors.top: parent.top
        anchors.topMargin: 70

        text:
            qsTr("بازگشت به منو")

        onClicked:
            root.backRequested()

        background: Rectangle {
            radius: 10

            color:
                backButton.pressed
                ? "#3B4A61"
                : "#253247"

            border.width: 1
            border.color: "#52637D"
        }

        contentItem: Text {
            text: backButton.text
            color: root.textColor
            font.pixelSize: 14
            font.bold: true

            horizontalAlignment:
                Text.AlignHCenter

            verticalAlignment:
                Text.AlignVCenter
        }
    }


    // =========================================================
    // SIDE MENU
    // =========================================================

    Rectangle {
        id: menuPanel

        width: 180

        anchors.top: parent.top
        anchors.topMargin: 125

        anchors.right: parent.right
        anchors.rightMargin: 18

        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18

        radius: 16

        color: root.panelColor

        border.width: 1
        border.color: "#26364D"


        Column {
            anchors.fill: parent
            anchors.margins: 10

            spacing: 8


            Button {
                id: networkButton

                width: parent.width
                height: 58

                text:
                    qsTr("شبکه و TCP")

                onClicked:
                    root.currentSection = "network"

                background: Rectangle {
                    radius: 10

                    color:
                        root.currentSection === "network"
                        ? root.accentSoftColor
                        : root.cardColor

                    border.width: 1

                    border.color:
                        root.currentSection === "network"
                        ? root.accentColor
                        : root.borderColor
                }

                contentItem: Text {
                    text: networkButton.text

                    color:
                        root.currentSection === "network"
                        ? root.textColor
                        : "#CBD5E1"

                    font.pixelSize: 13

                    font.bold:
                        root.currentSection === "network"

                    horizontalAlignment:
                        Text.AlignHCenter

                    verticalAlignment:
                        Text.AlignVCenter
                }
            }


            Button {
                id: hardwareButton

                width: parent.width
                height: 58

                text:
                    qsTr("ارتباط سخت‌افزار")

                onClicked:
                    root.currentSection = "hardware"

                background: Rectangle {
                    radius: 10

                    color:
                        root.currentSection === "hardware"
                        ? root.accentSoftColor
                        : root.cardColor

                    border.width: 1

                    border.color:
                        root.currentSection === "hardware"
                        ? root.accentColor
                        : root.borderColor
                }

                contentItem: Text {
                    text: hardwareButton.text

                    color:
                        root.currentSection === "hardware"
                        ? root.textColor
                        : "#CBD5E1"

                    font.pixelSize: 13

                    font.bold:
                        root.currentSection === "hardware"

                    horizontalAlignment:
                        Text.AlignHCenter

                    verticalAlignment:
                        Text.AlignVCenter
                }
            }


            Button {
                id: systemButton

                width: parent.width
                height: 58

                text:
                    qsTr("سیستم")

                onClicked:
                    root.currentSection = "system"

                background: Rectangle {
                    radius: 10

                    color:
                        root.currentSection === "system"
                        ? root.accentSoftColor
                        : root.cardColor

                    border.width: 1

                    border.color:
                        root.currentSection === "system"
                        ? root.accentColor
                        : root.borderColor
                }

                contentItem: Text {
                    text: systemButton.text

                    color:
                        root.currentSection === "system"
                        ? root.textColor
                        : "#CBD5E1"

                    font.pixelSize: 13

                    font.bold:
                        root.currentSection === "system"

                    horizontalAlignment:
                        Text.AlignHCenter

                    verticalAlignment:
                        Text.AlignVCenter
                }
            }


            Button {
                id: maintenanceButton

                width: parent.width
                height: 58

                text:
                    qsTr("عیب‌یابی و نگهداری")

                onClicked:
                    root.currentSection = "maintenance"

                background: Rectangle {
                    radius: 10

                    color:
                        root.currentSection === "maintenance"
                        ? root.accentSoftColor
                        : root.cardColor

                    border.width: 1

                    border.color:
                        root.currentSection === "maintenance"
                        ? root.accentColor
                        : root.borderColor
                }

                contentItem: Text {
                    text: maintenanceButton.text

                    color:
                        root.currentSection === "maintenance"
                        ? root.textColor
                        : "#CBD5E1"

                    font.pixelSize: 12

                    font.bold:
                        root.currentSection === "maintenance"

                    horizontalAlignment:
                        Text.AlignHCenter

                    verticalAlignment:
                        Text.AlignVCenter
                }
            }
        }
    }


    // =========================================================
    // CONTENT PANEL
    // =========================================================

    Rectangle {
        id: contentPanel

        anchors.left: parent.left
        anchors.leftMargin: 18

        anchors.right: menuPanel.left
        anchors.rightMargin: 12

        anchors.top: parent.top
        anchors.topMargin: 125

        anchors.bottom: parent.bottom
        anchors.bottomMargin: 18

        radius: 16

        color: root.panelColor

        border.width: 1
        border.color: "#26364D"


        // =====================================================
        // NETWORK
        // =====================================================

        Item {
            anchors.fill: parent

            visible:
                root.currentSection === "network"


            Column {
                anchors.fill: parent
                anchors.margins: 16

                spacing: 9


                Text {
                    width: parent.width

                    text:
                        qsTr("شبکه و TCP")

                    color: root.textColor

                    font.pixelSize: 19
                    font.bold: true

                    horizontalAlignment:
                        Text.AlignRight
                }


                Row {
                    width: parent.width
                    spacing: 10


                    Rectangle {
                        width: 245
                        height: 48

                        radius: 10

                        color: root.cardColor

                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                appState.ethernetConnected
                                ? qsTr("Ethernet: متصل")
                                : qsTr("Ethernet: قطع")

                            color:
                                appState.ethernetConnected
                                ? root.greenColor
                                : root.redColor

                            font.pixelSize: 13
                            font.bold: true
                        }
                    }


                    Rectangle {
                        width: 245
                        height: 48

                        radius: 10

                        color: root.cardColor

                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                qsTr("TCP: در انتظار Backend")

                            color: root.subTextColor

                            font.pixelSize: 13
                            font.bold: true
                        }
                    }
                }


                Row {
                    width: parent.width
                    spacing: 10


                    Column {
                        width: 245
                        spacing: 3

                        Text {
                            width: parent.width
                            text: qsTr("IP دستگاه")
                            color: root.subTextColor
                            font.pixelSize: 10

                            horizontalAlignment:
                                Text.AlignHCenter
                        }

                        Rectangle {
                            width: parent.width
                            height: 38

                            radius: 8

                            color: "#0E1828"

                            border.width: 1
                            border.color: root.borderColor

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12

                                text: root.deviceIp
                                color: root.textColor

                                font.pixelSize: 15

                                horizontalAlignment:
                                    Text.AlignHCenter

                                verticalAlignment:
                                    Text.AlignVCenter
                            }

                            MouseArea {
                                anchors.fill: parent

                                onClicked:
                                    root.openKeypad(
                                        "ip",
                                        qsTr("IP دستگاه"),
                                        root.deviceIp,
                                        true
                                    )
                            }
                        }
                    }


                    Column {
                        width: 245
                        spacing: 3

                        Text {
                            width: parent.width
                            text: qsTr("Subnet")
                            color: root.subTextColor
                            font.pixelSize: 10

                            horizontalAlignment:
                                Text.AlignHCenter
                        }

                        Rectangle {
                            width: parent.width
                            height: 38

                            radius: 8

                            color: "#0E1828"

                            border.width: 1
                            border.color: root.borderColor

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12

                                text: root.subnetMask
                                color: root.textColor

                                font.pixelSize: 15

                                horizontalAlignment:
                                    Text.AlignHCenter

                                verticalAlignment:
                                    Text.AlignVCenter
                            }

                            MouseArea {
                                anchors.fill: parent

                                onClicked:
                                    root.openKeypad(
                                        "subnet",
                                        qsTr("Subnet"),
                                        root.subnetMask,
                                        true
                                    )
                            }
                        }
                    }
                }


                Row {
                    width: parent.width
                    spacing: 10


                    Column {
                        width: 245
                        spacing: 3

                        Text {
                            width: parent.width
                            text: qsTr("Gateway")
                            color: root.subTextColor
                            font.pixelSize: 10

                            horizontalAlignment:
                                Text.AlignHCenter
                        }

                        Rectangle {
                            width: parent.width
                            height: 38

                            radius: 8

                            color: "#0E1828"

                            border.width: 1
                            border.color: root.borderColor

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12

                                text: root.gatewayIp
                                color: root.textColor

                                font.pixelSize: 15

                                horizontalAlignment:
                                    Text.AlignHCenter

                                verticalAlignment:
                                    Text.AlignVCenter
                            }

                            MouseArea {
                                anchors.fill: parent

                                onClicked:
                                    root.openKeypad(
                                        "gateway",
                                        qsTr("Gateway"),
                                        root.gatewayIp,
                                        true
                                    )
                            }
                        }
                    }


                    Column {
                        width: 245
                        spacing: 3

                        Text {
                            width: parent.width
                            text: qsTr("TCP Port")
                            color: root.subTextColor
                            font.pixelSize: 10

                            horizontalAlignment:
                                Text.AlignHCenter
                        }

                        Rectangle {
                            width: parent.width
                            height: 38

                            radius: 8

                            color: "#0E1828"

                            border.width: 1
                            border.color: root.borderColor

                            Text {
                                anchors.fill: parent
                                anchors.leftMargin: 12
                                anchors.rightMargin: 12

                                text: root.tcpPort
                                color: root.textColor

                                font.pixelSize: 15

                                horizontalAlignment:
                                    Text.AlignHCenter

                                verticalAlignment:
                                    Text.AlignVCenter
                            }

                            MouseArea {
                                anchors.fill: parent

                                onClicked:
                                    root.openKeypad(
                                        "port",
                                        qsTr("TCP Port"),
                                        root.tcpPort,
                                        false
                                    )
                            }
                        }
                    }
                }


                Item {
                    width: 1
                    height: 10
                }


                Button {
                    id: applyNetworkButton

                    width: 185
                    height: 42

                    anchors.horizontalCenter:
                        parent.horizontalCenter

                    text:
                        qsTr("اعمال تنظیمات")

                    background: Rectangle {
                        radius: 10

                        color:
                            applyNetworkButton.pressed
                            ? "#167DA5"
                            : "#0EA5E9"

                        border.width: 1
                        border.color: "#38BDF8"
                    }

                    contentItem: Text {
                        text: applyNetworkButton.text
                        color: "#FFFFFF"
                        font.pixelSize: 14
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }

                    onClicked:
                        console.log(
                            "SETTINGS | NETWORK APPLY | "
                            + root.deviceIp
                            + " | "
                            + root.subnetMask
                            + " | "
                            + root.gatewayIp
                            + " | "
                            + root.tcpPort
                        )
                }
            }
        }


        // =====================================================
        // HARDWARE
        // =====================================================

        Item {
            anchors.fill: parent

            visible:
                root.currentSection === "hardware"


            Flickable {
                id: hardwareFlick

                anchors.fill: parent

                clip: true

                contentWidth:
                    width

                contentHeight:
                    hardwareColumn.height + 32

                boundsBehavior:
                    Flickable.StopAtBounds


                ScrollBar.vertical:
                    ScrollBar {

                        policy:
                            hardwareFlick.contentHeight
                            > hardwareFlick.height
                            ? ScrollBar.AsNeeded
                            : ScrollBar.AlwaysOff
                    }


                Column {
                    id: hardwareColumn

                    x: 16
                    y: 14

                    width:
                        hardwareFlick.width - 32

                    spacing: 10


                    Text {
                        width: parent.width

                        text:
                            qsTr("ارتباط سخت‌افزار")

                        color: root.textColor

                        font.pixelSize: 19
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter
                    }


                    Text {
                        width: parent.width

                        text:
                            qsTr(
                                "تنظیم رابط، Baud Rate و ساختار Slaveها"
                            )

                        color: root.subTextColor

                        font.pixelSize: 11

                        horizontalAlignment:
                            Text.AlignHCenter
                    }


                    // =========================================
                    // TRANSPORT + BAUD RATE
                    // =========================================

                    Row {
                        width: parent.width

                        spacing: 10

                        anchors.horizontalCenter:
                            parent.horizontalCenter


                        Column {
                            width: 245
                            spacing: 4


                            Text {
                                width: parent.width

                                text:
                                    qsTr("نوع ارتباط")

                                color: root.subTextColor

                                font.pixelSize: 10

                                horizontalAlignment:
                                    Text.AlignHCenter
                            }


                            Rectangle {
                                id: transportSelector

                                width: parent.width
                                height: 40

                                radius: 8

                                color: "#0E1828"

                                border.width: 1

                                border.color:
                                    root.openHardwareDropdown
                                    === "transport"
                                    ? root.accentColor
                                    : root.borderColor


                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12


                                    Text {
                                        width: parent.width - 28
                                        height: parent.height

                                        text:
                                            root.transportType

                                        color: root.textColor

                                        font.pixelSize: 14
                                        font.bold: true

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }


                                    Text {
                                        width: 28
                                        height: parent.height

                                        text:
                                            root.openHardwareDropdown
                                            === "transport"
                                            ? "▲"
                                            : "▼"

                                        color: root.accentColor

                                        font.pixelSize: 10

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }
                                }


                                MouseArea {
                                    anchors.fill: parent

                                    onClicked: {

                                        root.openHardwareDropdown =
                                            root.openHardwareDropdown
                                            === "transport"
                                            ? ""
                                            : "transport"
                                    }
                                }
                            }


                            Rectangle {
                                width: parent.width

                                height:
                                    visible
                                    ? 86
                                    : 0

                                visible:
                                    root.openHardwareDropdown
                                    === "transport"

                                radius: 9

                                color: "#0E1828"

                                border.width: 1
                                border.color: "#3B4B63"

                                clip: true


                                ListView {
                                    anchors.fill: parent
                                    anchors.margins: 5

                                    clip: true

                                    spacing: 4

                                    model: [
                                        "RS485",
                                        "UART"
                                    ]


                                    delegate:
                                        Button {
                                            id: transportOption

                                            width: 225
                                            height: 34

                                            x: 5

                                            text:
                                                modelData

                                            onClicked: {

                                                root.transportType =
                                                    modelData

                                                root.openHardwareDropdown =
                                                    ""
                                            }


                                            background: Rectangle {
                                                radius: 7

                                                color:
                                                    root.transportType
                                                    === modelData
                                                    ? root.accentSoftColor
                                                    : root.cardColor

                                                border.width: 1

                                                border.color:
                                                    root.transportType
                                                    === modelData
                                                    ? root.accentColor
                                                    : root.borderColor
                                            }


                                            contentItem: Text {
                                                text:
                                                    transportOption.text

                                                color: root.textColor

                                                font.pixelSize: 12
                                                font.bold: true

                                                horizontalAlignment:
                                                    Text.AlignHCenter

                                                verticalAlignment:
                                                    Text.AlignVCenter
                                            }
                                        }
                                }
                            }
                        }


                        Column {
                            width: 245
                            spacing: 4


                            Text {
                                width: parent.width

                                text:
                                    qsTr("Baud Rate")

                                color: root.subTextColor

                                font.pixelSize: 10

                                horizontalAlignment:
                                    Text.AlignHCenter
                            }


                            Rectangle {
                                id: baudSelector

                                width: parent.width
                                height: 40

                                radius: 8

                                color: "#0E1828"

                                border.width: 1

                                border.color:
                                    root.openHardwareDropdown
                                    === "baud"
                                    ? root.accentColor
                                    : root.borderColor


                                Row {
                                    anchors.fill: parent
                                    anchors.leftMargin: 12
                                    anchors.rightMargin: 12


                                    Text {
                                        width: parent.width - 28
                                        height: parent.height

                                        text:
                                            root.baudRate

                                        color: root.textColor

                                        font.pixelSize: 14
                                        font.bold: true

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }


                                    Text {
                                        width: 28
                                        height: parent.height

                                        text:
                                            root.openHardwareDropdown
                                            === "baud"
                                            ? "▲"
                                            : "▼"

                                        color: root.accentColor

                                        font.pixelSize: 10

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }
                                }


                                MouseArea {
                                    anchors.fill: parent

                                    onClicked: {

                                        root.openHardwareDropdown =
                                            root.openHardwareDropdown
                                            === "baud"
                                            ? ""
                                            : "baud"
                                    }
                                }
                            }


                            Rectangle {
                                width: parent.width

                                height:
                                    visible
                                    ? 145
                                    : 0

                                visible:
                                    root.openHardwareDropdown
                                    === "baud"

                                radius: 9

                                color: "#0E1828"

                                border.width: 1
                                border.color: "#3B4B63"

                                clip: true


                                ListView {
                                    id: baudList

                                    anchors.fill: parent
                                    anchors.margins: 5

                                    clip: true

                                    spacing: 4

                                    boundsBehavior:
                                        Flickable.StopAtBounds

                                    model: [
                                        "9600",
                                        "19200",
                                        "38400",
                                        "57600",
                                        "115200"
                                    ]


                                    ScrollBar.vertical:
                                        ScrollBar {

                                            policy:
                                                ScrollBar.AsNeeded
                                        }


                                    delegate:
                                        Button {
                                            id: baudOption

                                            width: 225
                                            height: 34

                                            x: 5

                                            text:
                                                modelData

                                            onClicked: {

                                                root.baudRate =
                                                    modelData

                                                root.openHardwareDropdown =
                                                    ""
                                            }


                                            background: Rectangle {
                                                radius: 7

                                                color:
                                                    root.baudRate
                                                    === modelData
                                                    ? root.accentSoftColor
                                                    : root.cardColor

                                                border.width: 1

                                                border.color:
                                                    root.baudRate
                                                    === modelData
                                                    ? root.accentColor
                                                    : root.borderColor
                                            }


                                            contentItem: Text {
                                                text:
                                                    baudOption.text

                                                color: root.textColor

                                                font.pixelSize: 12
                                                font.bold: true

                                                horizontalAlignment:
                                                    Text.AlignHCenter

                                                verticalAlignment:
                                                    Text.AlignVCenter
                                            }
                                        }
                                }
                            }
                        }
                    }


                    // =========================================
                    // SLAVE COUNT + TOTAL LOCKERS
                    // =========================================

                    Row {
                        width: parent.width

                        spacing: 10

                        anchors.horizontalCenter:
                            parent.horizontalCenter


                        Column {
                            width: 245
                            spacing: 4


                            Text {
                                width: parent.width

                                text:
                                    qsTr("تعداد Slave")

                                color: root.subTextColor

                                font.pixelSize: 10

                                horizontalAlignment:
                                    Text.AlignHCenter
                            }


                            Rectangle {
                                width: parent.width
                                height: 38

                                radius: 8

                                color: "#0E1828"

                                border.width: 1
                                border.color: root.borderColor


                                Text {
                                    anchors.fill: parent

                                    text:
                                        root.slaveCount

                                    color: root.textColor

                                    font.pixelSize: 15
                                    font.bold: true

                                    horizontalAlignment:
                                        Text.AlignHCenter

                                    verticalAlignment:
                                        Text.AlignVCenter
                                }


                                MouseArea {
                                    anchors.fill: parent

                                    onClicked:
                                        root.openKeypad(
                                            "slave_count",
                                            qsTr("تعداد Slave"),
                                            root.slaveCount,
                                            false
                                        )
                                }
                            }
                        }


                        Column {
                            width: 245
                            spacing: 4


                            Text {
                                width: parent.width

                                text:
                                    qsTr("تعداد کل کمدها")

                                color: root.subTextColor

                                font.pixelSize: 10

                                horizontalAlignment:
                                    Text.AlignHCenter
                            }


                            Rectangle {
                                width: parent.width
                                height: 38

                                radius: 8

                                color: "#0E1828"

                                border.width: 1
                                border.color: root.borderColor


                                Text {
                                    anchors.fill: parent

                                    text:
                                        root.totalLockerCount

                                    color: root.textColor

                                    font.pixelSize: 15
                                    font.bold: true

                                    horizontalAlignment:
                                        Text.AlignHCenter

                                    verticalAlignment:
                                        Text.AlignVCenter
                                }


                                MouseArea {
                                    anchors.fill: parent

                                    onClicked:
                                        root.openKeypad(
                                            "total_lockers",
                                            qsTr("تعداد کل کمدها"),
                                            root.totalLockerCount.toString(),
                                            false
                                        )
                                }
                            }
                        }
                    }


                    Item {
                        width: 1
                        height: 8
                    }


                    Button {
                        id: hardwareContinueButton

                        width: 190
                        height: 40

                        anchors.horizontalCenter:
                            parent.horizontalCenter

                        text:
                            qsTr("پیکربندی Slaveها")

                        onClicked: {

                            root.openHardwareDropdown =
                                ""

                            root.syncSlaveConfigModel(
                                root.slaveCount
                            )

                            root.slaveConfigVisible =
                                true
                        }


                        background: Rectangle {
                            radius: 10

                            color:
                                hardwareContinueButton.pressed
                                ? "#167DA5"
                                : "#0EA5E9"

                            border.width: 1
                            border.color: "#38BDF8"
                        }


                        contentItem: Text {
                            text:
                                hardwareContinueButton.text

                            color: "#FFFFFF"

                            font.pixelSize: 13
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }


                    Item {
                        width: 1
                        height: 6
                    }
                }
            }
        }



        // =====================================================
        // SYSTEM
        // =====================================================

        Item {
            anchors.fill: parent

            visible:
                root.currentSection === "system"


            Column {
                anchors.fill: parent
                anchors.margins: 14

                spacing: 7


                Text {
                    width: parent.width

                    text:
                        qsTr("سیستم")

                    color: root.textColor

                    font.pixelSize: 19
                    font.bold: true

                    horizontalAlignment:
                        Text.AlignHCenter
                }


                Rectangle {
                    width: parent.width
                    height: 96

                    radius: 12

                    color: root.cardColor

                    border.width: 1
                    border.color: root.borderColor


                    Column {
                        anchors.fill: parent
                        anchors.margins: 9

                        spacing: 3


                        Text {
                            width: parent.width

                            text:
                                qsTr(
                                    "زمان بازگشت خودکار به صفحه اول"
                                )

                            color: root.textColor

                            font.pixelSize: 13
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Text {
                            width: parent.width

                            text:
                                root.idleTimeoutText(
                                    root.idleTimeoutSeconds
                                )

                            color: root.accentColor

                            font.pixelSize: 14
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter
                        }


                        Slider {
                            id: idleTimeoutSlider

                            width:
                                parent.width - 34

                            height: 34

                            anchors.horizontalCenter:
                                parent.horizontalCenter

                            from: 10
                            to: 300

                            stepSize: 5

                            value:
                                root.idleTimeoutSeconds

                            // Keep the slider physically LTR:
                            // moving right means a LONGER timeout.
                            LayoutMirroring.enabled:
                                false

                            LayoutMirroring.childrenInherit:
                                false

                            onMoved: {

                                root.idleTimeoutRequested(
                                    Math.round(
                                        value / 5
                                    ) * 5
                                )
                            }


                            background: Rectangle {
                                x:
                                    idleTimeoutSlider.leftPadding

                                y:
                                    idleTimeoutSlider.topPadding
                                    + idleTimeoutSlider.availableHeight / 2
                                    - height / 2

                                width:
                                    idleTimeoutSlider.availableWidth

                                height: 6

                                radius: 3

                                color: "#2A3A52"


                                Rectangle {
                                    width:
                                        idleTimeoutSlider.visualPosition
                                        * parent.width

                                    height: parent.height

                                    radius: 3

                                    color:
                                        root.accentColor
                                }
                            }


                            handle: Rectangle {
                                x:
                                    idleTimeoutSlider.leftPadding
                                    + idleTimeoutSlider.visualPosition
                                    * (
                                        idleTimeoutSlider.availableWidth
                                        - width
                                    )

                                y:
                                    idleTimeoutSlider.topPadding
                                    + idleTimeoutSlider.availableHeight / 2
                                    - height / 2

                                width: 24
                                height: 24

                                radius: 12

                                color: "#FFFFFF"

                                border.width: 3
                                border.color: root.accentColor
                            }
                        }
                    }
                }


                Row {
                    width: parent.width

                    spacing: 10

                    anchors.horizontalCenter:
                        parent.horizontalCenter


                    Rectangle {
                        width: 245
                        height: 50

                        radius: 10

                        color: root.cardColor

                        border.width: 1
                        border.color: root.borderColor


                        Text {
                            anchors.fill: parent
                            anchors.margins: 8

                            text:
                                qsTr(
                                    "دستگاه: KardanSoft Controller"
                                )

                            color: "#CBD5E1"

                            font.pixelSize: 11
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }


                    Rectangle {
                        width: 245
                        height: 50

                        radius: 10

                        color: root.cardColor

                        border.width: 1
                        border.color: root.borderColor


                        Text {
                            anchors.fill: parent
                            anchors.margins: 8

                            text:
                                qsTr("نسخه نرم‌افزار: 0.1.0")

                            color: "#CBD5E1"

                            font.pixelSize: 11
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }
                }


                Text {
                    width: parent.width
                    height: 18

                    text:
                        qsTr("مدیریت پترن‌های دسترسی")

                    color: root.subTextColor

                    font.pixelSize: 11
                    font.bold: true

                    horizontalAlignment:
                        Text.AlignHCenter

                    verticalAlignment:
                        Text.AlignVCenter
                }


                // Fixed-width row instead of parent-width row.
                // This keeps both buttons geometrically centered.
                Row {
                    width: 400
                    height: 38

                    anchors.horizontalCenter:
                        parent.horizontalCenter

                    spacing: 10


                    Button {
                        id: operatorPatternButton

                        width: 195
                        height: 38

                        text:
                            qsTr("تغییر پترن اپراتور")

                        onClicked:
                            root.openPatternChanger(
                                "operator"
                            )


                        background: Rectangle {
                            radius: 10

                            color:
                                operatorPatternButton.pressed
                                ? "#2C3B52"
                                : root.cardColor

                            border.width: 1
                            border.color: root.borderColor
                        }


                        contentItem: Text {
                            text:
                                operatorPatternButton.text

                            color: root.textColor

                            font.pixelSize: 13
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }


                    Button {
                        id: adminPatternButton

                        width: 195
                        height: 38

                        text:
                            qsTr("تغییر پترن مدیر")

                        onClicked:
                            root.openPatternChanger(
                                "admin"
                            )


                        background: Rectangle {
                            radius: 10

                            color:
                                adminPatternButton.pressed
                                ? "#2C3B52"
                                : root.cardColor

                            border.width: 1
                            border.color: root.borderColor
                        }


                        contentItem: Text {
                            text:
                                adminPatternButton.text

                            color: root.textColor

                            font.pixelSize: 13
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }
                }
            }
        }



        // =====================================================
        // MAINTENANCE
        // =====================================================

        Item {
            anchors.fill: parent

            visible:
                root.currentSection === "maintenance"


            Column {
                anchors.fill: parent
                anchors.margins: 16

                spacing: 9


                Text {
                    width: parent.width

                    text:
                        qsTr("عیب‌یابی و نگهداری")

                    color: root.textColor

                    font.pixelSize: 19
                    font.bold: true

                    horizontalAlignment:
                        Text.AlignRight
                }


                Row {
                    spacing: 10


                    Rectangle {
                        width: 245
                        height: 52
                        radius: 10
                        color: root.cardColor
                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                qsTr(
                                    "KardanSoft: در حال اجرا"
                                )

                            color: root.greenColor
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }


                    Rectangle {
                        width: 245
                        height: 52
                        radius: 10
                        color: root.cardColor
                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                qsTr(
                                    "TCP: در انتظار Backend"
                                )

                            color: root.subTextColor
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }


                Row {
                    spacing: 10


                    Rectangle {
                        width: 245
                        height: 52
                        radius: 10
                        color: root.cardColor
                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                developmentMode
                                ? qsTr("Slave: Simulator")
                                : qsTr(
                                    "Slave: در انتظار بررسی"
                                )

                            color: root.accentColor

                            font.pixelSize: 11
                            font.bold: true
                        }
                    }


                    Rectangle {
                        width: 245
                        height: 52
                        radius: 10
                        color: root.cardColor
                        border.width: 1
                        border.color: root.borderColor

                        Text {
                            anchors.centerIn: parent

                            text:
                                qsTr("SQLite: فعال")

                            color: root.greenColor
                            font.pixelSize: 11
                            font.bold: true
                        }
                    }
                }


                Row {
                    spacing: 10


                    Button {
                        id: logsButton

                        width: 160
                        height: 40

                        text:
                            qsTr("مشاهده Logها")

                        background: Rectangle {
                            radius: 10

                            color:
                                logsButton.pressed
                                ? "#2C3B52"
                                : root.cardColor

                            border.width: 1
                            border.color: root.borderColor
                        }

                        contentItem: Text {
                            text: logsButton.text
                            color: root.textColor
                            font.pixelSize: 12
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }


                    Button {
                        id: restartButton

                        width: 160
                        height: 40

                        text:
                            qsTr("Restart نرم‌افزار")

                        background: Rectangle {
                            radius: 10

                            color:
                                restartButton.pressed
                                ? "#59313A"
                                : "#3C2430"

                            border.width: 1
                            border.color: "#B45364"
                        }

                        contentItem: Text {
                            text:
                                restartButton.text

                            color: "#FDA4AF"
                            font.pixelSize: 12
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }


                    Button {
                        id: updateButton

                        width: 160
                        height: 40

                        enabled: false

                        text:
                            qsTr("Software Update")

                        background: Rectangle {
                            radius: 10
                            color: "#202A3A"

                            border.width: 1
                            border.color: "#334155"

                            opacity:
                                updateButton.enabled
                                ? 1.0
                                : 0.55
                        }

                        contentItem: Text {
                            text:
                                updateButton.text

                            color: "#64748B"
                            font.pixelSize: 12
                            font.bold: true

                            horizontalAlignment:
                                Text.AlignHCenter

                            verticalAlignment:
                                Text.AlignVCenter
                        }
                    }
                }


                Rectangle {
                    width: parent.width
                    height: 92

                    radius: 10

                    color: root.cardColor

                    border.width: 1
                    border.color: root.borderColor


                    Text {
                        anchors.centerIn: parent

                        width:
                            parent.width - 24

                        text:
                            qsTr(
                                "تست مستقیم ارتباط با تک‌تک Slaveها در مرحله اتصال Backend سخت‌افزار فعال می‌شود."
                            )

                        color: root.subTextColor

                        font.pixelSize: 11

                        wrapMode:
                            Text.WordWrap

                        horizontalAlignment:
                            Text.AlignHCenter
                    }
                }
            }
        }
    }


    // =========================================================
    // PATTERN CHANGE OVERLAY
    // =========================================================

    Rectangle {
        id: patternChangeOverlay

        anchors.fill: parent

        visible:
            root.patternChangeVisible

        enabled:
            visible

        z: 7200

        color: "#B8070D18"


        MouseArea {
            anchors.fill: parent
        }


        Rectangle {
            width: 520
            height: 340

            anchors.centerIn: parent

            radius: 18

            color: "#111C2F"

            border.width: 1
            border.color: "#40516A"


            Text {
                id: patternChangeTitle

                anchors.top: parent.top
                anchors.topMargin: 12

                anchors.horizontalCenter:
                    parent.horizontalCenter

                text:
                    qsTr("تغییر پترن ")
                    + root.patternRoleName()

                color: root.textColor

                font.pixelSize: 18
                font.bold: true

                horizontalAlignment:
                    Text.AlignHCenter
            }


            Text {
                id: patternChangeInstruction

                width:
                    parent.width - 30

                anchors.top:
                    patternChangeTitle.bottom

                anchors.topMargin: 2

                anchors.horizontalCenter:
                    parent.horizontalCenter

                text:
                    root.patternMessage

                color: {

                    if (
                        root.patternVerificationState
                        === 1
                    ) {
                        return root.greenColor
                    }

                    if (
                        root.patternVerificationState
                        === -1
                    ) {
                        return root.redColor
                    }

                    return root.subTextColor
                }

                font.pixelSize: 12

                horizontalAlignment:
                    Text.AlignHCenter
            }


            Item {
                id: patternChangeBoard

                width: 240
                height: 205

                anchors.top:
                    patternChangeInstruction.bottom

                anchors.topMargin: 5

                anchors.horizontalCenter:
                    parent.horizontalCenter


                function nodeCenterX(
                    index
                ) {

                    var column =
                        index % 3

                    return (
                        42
                        + column * 78
                    )
                }


                function nodeCenterY(
                    index
                ) {

                    var row =
                        Math.floor(
                            index / 3
                        )

                    return (
                        28
                        + row * 74
                    )
                }


                function isSelected(
                    nodeNumber
                ) {

                    return (
                        root.patternSelectedNodes.indexOf(
                            nodeNumber
                        ) !== -1
                    )
                }


                Canvas {
                    id: patternChangeCanvas

                    anchors.fill: parent


                    onPaint: {

                        var ctx =
                            getContext("2d")

                        ctx.reset()

                        if (
                            root.patternSelectedNodes.length
                            === 0
                        ) {
                            return
                        }

                        var lineColor =
                            root.accentColor

                        if (
                            root.patternVerificationState
                            === 1
                        ) {
                            lineColor =
                                root.greenColor

                        } else if (
                            root.patternVerificationState
                            === -1
                        ) {
                            lineColor =
                                root.redColor
                        }

                        ctx.strokeStyle =
                            lineColor

                        ctx.lineWidth = 5
                        ctx.lineCap = "round"
                        ctx.lineJoin = "round"

                        ctx.beginPath()

                        for (
                            var i = 0;
                            i
                            < root.patternSelectedNodes.length;
                            i++
                        ) {

                            var nodeNumber =
                                root.patternSelectedNodes[i]

                            var nodeIndex =
                                nodeNumber - 1

                            var x =
                                patternChangeBoard.nodeCenterX(
                                    nodeIndex
                                )

                            var y =
                                patternChangeBoard.nodeCenterY(
                                    nodeIndex
                                )

                            if (i === 0) {

                                ctx.moveTo(
                                    x,
                                    y
                                )

                            } else {

                                ctx.lineTo(
                                    x,
                                    y
                                )
                            }
                        }

                        if (
                            root.patternDrawing
                            && root.patternVerificationState
                            === 0
                        ) {

                            ctx.lineTo(
                                root.patternPointerX,
                                root.patternPointerY
                            )
                        }

                        ctx.stroke()
                    }
                }


                Repeater {
                    model: 9


                    delegate:
                        Rectangle {

                            width: 36
                            height: 36

                            radius: 18

                            x:
                                patternChangeBoard.nodeCenterX(
                                    index
                                )
                                - width / 2

                            y:
                                patternChangeBoard.nodeCenterY(
                                    index
                                )
                                - height / 2

                            property bool selected:
                                patternChangeBoard.isSelected(
                                    index + 1
                                )

                            color:
                                selected
                                ? "#164E63"
                                : "#1E293B"

                            border.width:
                                selected
                                ? 4
                                : 3

                            border.color: {

                                if (!selected)
                                    return "#64748B"

                                if (
                                    root.patternVerificationState
                                    === 1
                                ) {
                                    return root.greenColor
                                }

                                if (
                                    root.patternVerificationState
                                    === -1
                                ) {
                                    return root.redColor
                                }

                                return root.accentColor
                            }


                            Rectangle {
                                width: 9
                                height: 9

                                radius: 5

                                anchors.centerIn:
                                    parent

                                color:
                                    parent.selected
                                    ? parent.border.color
                                    : "#94A3B8"
                            }
                        }
                }


                MouseArea {
                    anchors.fill: parent


                    onPressed: {

                        root.resetPatternDrawing()

                        root.patternDrawing =
                            true

                        root.patternPointerX =
                            mouse.x

                        root.patternPointerY =
                            mouse.y

                        root.checkPatternNodeAt(
                            mouse.x,
                            mouse.y
                        )

                        patternChangeCanvas.requestPaint()
                    }


                    onPositionChanged: {

                        if (
                            !root.patternDrawing
                        ) {
                            return
                        }

                        root.patternPointerX =
                            mouse.x

                        root.patternPointerY =
                            mouse.y

                        root.checkPatternNodeAt(
                            mouse.x,
                            mouse.y
                        )

                        patternChangeCanvas.requestPaint()
                    }


                    onReleased: {

                        if (
                            !root.patternDrawing
                        ) {
                            return
                        }

                        root.patternDrawing =
                            false

                        patternChangeCanvas.requestPaint()

                        root.submitNewPattern()
                    }


                    onCanceled:
                        root.resetPatternDrawing()
                }
            }


            Text {
                anchors.top:
                    patternChangeBoard.bottom

                anchors.topMargin: -1

                anchors.horizontalCenter:
                    parent.horizontalCenter

                text: {

                    if (
                        root.patternChangeStep === 0
                    ) {
                        return qsTr(
                            "مرحله ۱ از ۳ — تأیید پترن فعلی"
                        )
                    }

                    if (
                        root.patternChangeStep === 1
                    ) {
                        return qsTr(
                            "مرحله ۲ از ۳ — پترن جدید"
                        )
                    }

                    return qsTr(
                        "مرحله ۳ از ۳ — تأیید پترن جدید"
                    )
                }

                color: "#64748B"

                font.pixelSize: 10
            }


            Row {
                anchors.bottom:
                    parent.bottom

                anchors.bottomMargin: 10

                anchors.horizontalCenter:
                    parent.horizontalCenter

                spacing: 10


                Button {
                    id: patternResetButton

                    width: 125
                    height: 36

                    text:
                        qsTr("شروع دوباره")

                    onClicked: {

                        root.patternChangeStep = 0
                        root.firstPatternValue = ""

                        root.resetPatternDrawing()

                        root.patternMessage =
                            qsTr("ابتدا پترن فعلی ")
                            + root.patternRoleName()
                            + qsTr(" را وارد کنید")
                    }


                    background: Rectangle {
                        radius: 9
                        color: root.cardColor

                        border.width: 1
                        border.color: root.borderColor
                    }


                    contentItem: Text {
                        text:
                            patternResetButton.text

                        color: root.textColor

                        font.pixelSize: 11
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }


                Button {
                    id: patternCancelButton

                    width: 125
                    height: 36

                    text:
                        qsTr("انصراف")

                    onClicked:
                        root.closePatternChanger()


                    background: Rectangle {
                        radius: 9
                        color: "#3C2430"

                        border.width: 1
                        border.color: "#B45364"
                    }


                    contentItem: Text {
                        text:
                            patternCancelButton.text

                        color: "#FDA4AF"

                        font.pixelSize: 11
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }
            }
        }
    }


    // =========================================================
    // SLAVE CONFIGURATION OVERLAY
    // =========================================================

    Rectangle {
        id: slaveConfigOverlay

        anchors.fill: parent

        visible:
            root.slaveConfigVisible

        z: 7000

        color: "#B3000000"


        MouseArea {
            anchors.fill: parent
        }


        Rectangle {
            width: 748
            height: 398

            anchors.centerIn: parent

            radius: 18

            color: "#111C2F"

            border.width: 1
            border.color: "#40516A"


            Text {
                id: slaveConfigTitle

                anchors.top: parent.top
                anchors.topMargin: 13

                anchors.horizontalCenter:
                    parent.horizontalCenter

                text:
                    qsTr("پیکربندی Slaveها")

                color: root.textColor

                font.pixelSize: 19
                font.bold: true

                horizontalAlignment:
                    Text.AlignHCenter
            }


            Row {
                id: slaveManagementRow

                anchors.top:
                    slaveConfigTitle.bottom

                anchors.topMargin: 8

                anchors.horizontalCenter:
                    parent.horizontalCenter

                spacing: 10


                Button {
                    id: addSlaveButton

                    width: 155
                    height: 36

                    text:
                        qsTr("+ افزودن Slave")

                    enabled:
                        slaveConfigModel.count < 32

                    onClicked:
                        root.addSlave()


                    background: Rectangle {
                        radius: 9

                        color:
                            addSlaveButton.pressed
                            ? "#167DA5"
                            : "#0EA5E9"

                        border.width: 1
                        border.color: root.accentColor

                        opacity:
                            addSlaveButton.enabled
                            ? 1.0
                            : 0.35
                    }


                    contentItem: Text {
                        text:
                            addSlaveButton.text

                        color: "#FFFFFF"

                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }


                Button {
                    id: removeSlaveButton

                    width: 155
                    height: 36

                    text:
                        qsTr("حذف آخرین Slave")

                    enabled:
                        slaveConfigModel.count > 1

                    onClicked:
                        root.removeLastSlave()


                    background: Rectangle {
                        radius: 9

                        color:
                            removeSlaveButton.pressed
                            ? "#59313A"
                            : "#3C2430"

                        border.width: 1
                        border.color: "#B45364"

                        opacity:
                            removeSlaveButton.enabled
                            ? 1.0
                            : 0.35
                    }


                    contentItem: Text {
                        text:
                            removeSlaveButton.text

                        color: "#FDA4AF"

                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }
            }


            Rectangle {
                id: slaveListPanel

                width: 716
                height: 246

                anchors.top:
                    slaveManagementRow.bottom

                anchors.topMargin: 9

                anchors.horizontalCenter:
                    parent.horizontalCenter

                radius: 12

                color: "#0E1828"

                border.width: 1
                border.color: "#26364D"


                ListView {
                    id: slaveConfigList

                    anchors.fill: parent
                    anchors.margins: 7

                    clip: true

                    spacing: 7

                    boundsBehavior:
                        Flickable.StopAtBounds

                    model:
                        slaveConfigModel


                    ScrollBar.vertical:
                        ScrollBar {

                            policy:
                                ScrollBar.AsNeeded
                        }


                    delegate:
                        Rectangle {

                            width:
                                slaveConfigList.width
                                - 10

                            height: 94

                            radius: 11

                            color: root.cardColor

                            border.width: 1

                            border.color:
                                communicationState
                                === "online"
                                ? root.greenColor
                                : (
                                    communicationState
                                    === "offline"
                                    ? root.redColor
                                    : root.borderColor
                                )


                            Column {
                                anchors.fill: parent
                                anchors.margins: 8

                                spacing: 5


                                Row {
                                    width: parent.width
                                    height: 34

                                    spacing: 8


                                    Text {
                                        width: 112
                                        height: parent.height

                                        text:
                                            qsTr("Slave ")
                                            + slaveAddress
                                            + qsTr("  •  DIP ")
                                            + slaveAddress

                                        color: root.textColor

                                        font.pixelSize: 12
                                        font.bold: true

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }


                                    Text {
                                        width: 100
                                        height: parent.height

                                        text:
                                            root.slaveStateText(
                                                communicationState
                                            )

                                        color:
                                            root.slaveStateColor(
                                                communicationState
                                            )

                                        font.pixelSize: 11
                                        font.bold: true

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }


                                    Rectangle {
                                        width: 205
                                        height: 32

                                        anchors.verticalCenter:
                                            parent.verticalCenter

                                        radius: 8

                                        color: "#0E1828"

                                        border.width: 1
                                        border.color: root.borderColor


                                        Text {
                                            anchors.fill: parent
                                            anchors.leftMargin: 7
                                            anchors.rightMargin: 7

                                            text:
                                                deviceIdentifier.length > 0
                                                ? deviceIdentifier
                                                : qsTr("شناسه / MAC: —")

                                            color:
                                                deviceIdentifier.length > 0
                                                ? "#CBD5E1"
                                                : "#64748B"

                                            font.pixelSize: 10

                                            horizontalAlignment:
                                                Text.AlignHCenter

                                            verticalAlignment:
                                                Text.AlignVCenter

                                            elide:
                                                Text.ElideMiddle
                                        }
                                    }


                                    Button {
                                        id: testSlaveButton

                                        width: 122
                                        height: 34

                                        enabled:
                                            communicationState
                                            !== "checking"

                                        text:
                                            communicationState
                                            === "checking"
                                            ? qsTr("در حال بررسی...")
                                            : qsTr("بررسی ارتباط")

                                        onClicked:
                                            root.requestSlaveDiagnostic(
                                                index,
                                                slaveAddress
                                            )


                                        background: Rectangle {
                                            radius: 9

                                            color:
                                                testSlaveButton.pressed
                                                ? "#167DA5"
                                                : "#0EA5E9"

                                            border.width: 1
                                            border.color: root.accentColor

                                            opacity:
                                                testSlaveButton.enabled
                                                ? 1.0
                                                : 0.55
                                        }


                                        contentItem: Text {
                                            text:
                                                testSlaveButton.text

                                            color: "#FFFFFF"

                                            font.pixelSize: 10
                                            font.bold: true

                                            horizontalAlignment:
                                                Text.AlignHCenter

                                            verticalAlignment:
                                                Text.AlignVCenter
                                        }
                                    }
                                }


                                Row {
                                    width: parent.width
                                    height: 36

                                    anchors.horizontalCenter:
                                        parent.horizontalCenter

                                    spacing: 10


                                    Text {
                                        width: 170
                                        height: parent.height

                                        text:
                                            root.activeChannelRange(
                                                activeChannels
                                            )

                                        color:
                                            activeChannels > 0
                                            ? "#C4B5FD"
                                            : root.subTextColor

                                        font.pixelSize: 11
                                        font.bold: true

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }


                                    Button {
                                        id: minusChannelButton

                                        width: 42
                                        height: 34

                                        text: "−"

                                        enabled:
                                            activeChannels > 0

                                        onClicked:
                                            root.changeActiveChannels(
                                                index,
                                                -1
                                            )


                                        background: Rectangle {
                                            radius: 9

                                            color:
                                                minusChannelButton.pressed
                                                ? "#3B4A61"
                                                : "#253247"

                                            border.width: 1
                                            border.color: root.borderColor

                                            opacity:
                                                minusChannelButton.enabled
                                                ? 1.0
                                                : 0.35
                                        }


                                        contentItem: Text {
                                            text:
                                                minusChannelButton.text

                                            color: root.textColor

                                            font.pixelSize: 20
                                            font.bold: true

                                            horizontalAlignment:
                                                Text.AlignHCenter

                                            verticalAlignment:
                                                Text.AlignVCenter
                                        }
                                    }


                                    Rectangle {
                                        width: 58
                                        height: 34

                                        radius: 9

                                        color: "#0E1828"

                                        border.width: 1
                                        border.color: root.accentColor


                                        Text {
                                            anchors.centerIn: parent

                                            text:
                                                activeChannels

                                            color: root.textColor

                                            font.pixelSize: 15
                                            font.bold: true
                                        }
                                    }


                                    Button {
                                        id: plusChannelButton

                                        width: 42
                                        height: 34

                                        text: "+"

                                        enabled:
                                            activeChannels < 12

                                        onClicked:
                                            root.changeActiveChannels(
                                                index,
                                                1
                                            )


                                        background: Rectangle {
                                            radius: 9

                                            color:
                                                plusChannelButton.pressed
                                                ? "#167DA5"
                                                : "#0EA5E9"

                                            border.width: 1
                                            border.color: root.accentColor

                                            opacity:
                                                plusChannelButton.enabled
                                                ? 1.0
                                                : 0.35
                                        }


                                        contentItem: Text {
                                            text:
                                                plusChannelButton.text

                                            color: "#FFFFFF"

                                            font.pixelSize: 18
                                            font.bold: true

                                            horizontalAlignment:
                                                Text.AlignHCenter

                                            verticalAlignment:
                                                Text.AlignVCenter
                                        }
                                    }


                                    Text {
                                        width: 185
                                        height: parent.height

                                        text:
                                            qsTr("کانال فعال: ")
                                            + activeChannels
                                            + qsTr(" از 12")

                                        color: root.subTextColor

                                        font.pixelSize: 10

                                        horizontalAlignment:
                                            Text.AlignHCenter

                                        verticalAlignment:
                                            Text.AlignVCenter
                                    }
                                }
                            }
                        }
                }
            }


            Row {
                anchors.top:
                    slaveListPanel.bottom

                anchors.topMargin: 8

                anchors.horizontalCenter:
                    parent.horizontalCenter

                spacing: 18


                Text {
                    height: 40

                    text:
                        qsTr("Slaveها: ")
                        + slaveConfigModel.count

                    color: root.subTextColor

                    font.pixelSize: 12
                    font.bold: true

                    verticalAlignment:
                        Text.AlignVCenter

                    horizontalAlignment:
                        Text.AlignHCenter
                }


                Text {
                    height: 40

                    text:
                        qsTr("تعداد کل کمدها: ")
                        + root.totalLockerCount

                    color: "#C4B5FD"

                    font.pixelSize: 12
                    font.bold: true

                    verticalAlignment:
                        Text.AlignVCenter

                    horizontalAlignment:
                        Text.AlignHCenter
                }


                Button {
                    id: closeSlaveConfigButton

                    width: 135
                    height: 40

                    text:
                        qsTr("تأیید و بستن")

                    onClicked:
                        root.applyLockerConfiguration()


                    background: Rectangle {
                        radius: 10

                        color:
                            closeSlaveConfigButton.pressed
                            ? "#167DA5"
                            : "#0EA5E9"

                        border.width: 1
                        border.color: root.accentColor
                    }


                    contentItem: Text {
                        text:
                            closeSlaveConfigButton.text

                        color: "#FFFFFF"

                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }
            }
        }
    }


    // =========================================================
    // NUMERIC KEYPAD
    // =========================================================

    Popup {
        id: numericKeypad

        modal: true

        focus: true

        closePolicy:
            Popup.NoAutoClose

        width: 390
        height: 395

        x:
            (root.width - width) / 2

        y:
            (root.height - height) / 2


        background: Rectangle {
            radius: 18

            color: "#111C2F"

            border.width: 1
            border.color: "#3B4B63"
        }


        contentItem: Column {
            anchors.fill: parent
            anchors.margins: 14

            spacing: 8


            Text {
                width: parent.width

                text:
                    root.keypadTitle

                color: root.textColor

                font.pixelSize: 17
                font.bold: true

                horizontalAlignment:
                    Text.AlignHCenter
            }


            Rectangle {
                width: parent.width
                height: 48

                radius: 10

                color: "#0E1828"

                border.width: 1
                border.color: root.accentColor


                Text {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12

                    text:
                        root.keypadValue

                    color: root.textColor

                    font.pixelSize: 18
                    font.bold: true

                    horizontalAlignment:
                        Text.AlignLeft

                    verticalAlignment:
                        Text.AlignVCenter

                    elide:
                        Text.ElideLeft
                }
            }


            Grid {
                columns: 3

                spacing: 7


                Repeater {
                    model: [
                        "1",
                        "2",
                        "3",
                        "4",
                        "5",
                        "6",
                        "7",
                        "8",
                        "9",
                        ".",
                        "0",
                        "⌫"
                    ]


                    delegate:
                        Button {

                            width: 115
                            height: 48

                            enabled:
                                modelData !== "."
                                || root.keypadAllowDot

                            text:
                                modelData

                            onClicked: {

                                if (
                                    modelData === "⌫"
                                ) {

                                    root.keypadBackspace()

                                } else {

                                    root.keypadAppend(
                                        modelData
                                    )
                                }
                            }

                            background: Rectangle {
                                radius: 10

                                color:
                                    parent.pressed
                                    ? "#2F405A"
                                    : "#1B2A40"

                                border.width: 1

                                border.color:
                                    parent.enabled
                                    ? "#40516A"
                                    : "#283548"

                                opacity:
                                    parent.enabled
                                    ? 1.0
                                    : 0.35
                            }

                            contentItem: Text {
                                text: parent.text

                                color:
                                    parent.enabled
                                    ? root.textColor
                                    : "#64748B"

                                font.pixelSize: 18
                                font.bold: true

                                horizontalAlignment:
                                    Text.AlignHCenter

                                verticalAlignment:
                                    Text.AlignVCenter
                            }
                        }
                }
            }


            Row {
                width: parent.width
                spacing: 8


                Button {
                    id: clearKeyButton

                    width: 112
                    height: 42

                    text:
                        qsTr("پاک کردن")

                    onClicked:
                        root.keypadValue = ""

                    background: Rectangle {
                        radius: 10
                        color: "#3A2530"
                        border.width: 1
                        border.color: "#7F3F50"
                    }

                    contentItem: Text {
                        text:
                            clearKeyButton.text

                        color: "#FDA4AF"
                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }


                Button {
                    id: cancelKeyButton

                    width: 112
                    height: 42

                    text:
                        qsTr("انصراف")

                    onClicked:
                        numericKeypad.close()

                    background: Rectangle {
                        radius: 10
                        color: root.cardColor
                        border.width: 1
                        border.color: root.borderColor
                    }

                    contentItem: Text {
                        text:
                            cancelKeyButton.text

                        color: root.textColor
                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }


                Button {
                    id: acceptKeyButton

                    width: 112
                    height: 42

                    text:
                        qsTr("تأیید")

                    onClicked:
                        root.applyKeypadValue()

                    background: Rectangle {
                        radius: 10
                        color: "#0EA5E9"
                        border.width: 1
                        border.color: root.accentColor
                    }

                    contentItem: Text {
                        text:
                            acceptKeyButton.text

                        color: "#FFFFFF"
                        font.pixelSize: 12
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter

                        verticalAlignment:
                            Text.AlignVCenter
                    }
                }
            }
        }
    }
}
