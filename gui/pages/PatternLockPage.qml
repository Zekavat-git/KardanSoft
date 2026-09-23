import QtQuick 2.15
import QtQuick.Controls 2.15


Rectangle {
    id: root

    objectName: "patternLockPage"

    // Main.qml owns all navigation.
    signal authorized(string target)

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    // =========================================================
    // TARGET
    // =========================================================

    property string target: "open_locker"


    // =========================================================
    // PATTERN STATE
    // =========================================================

    property var selectedNodes: []

    property bool drawing: false

    property real pointerX: 0
    property real pointerY: 0

    // 0 = normal
    // 1 = success
    // -1 = error
    property int verificationState: 0

    property int remainingAttempts: 5
    property int lockedSeconds: 0

    // Prevent duplicate navigation while a page change is queued.
    property bool navigationPending: false


    readonly property string targetName:
        target === "settings"
        ? qsTr("تنظیمات")
        : qsTr("باز کردن کمدها")


    // =========================================================
    // SAFE NAVIGATION
    // =========================================================

    function requestAuthorizedNavigation() {

        if (navigationPending)
            return

        navigationPending = true
        drawing = false

        clearPatternTimer.stop()
        successTimer.stop()
        lockCountdownTimer.stop()

        console.log(
            "NAVIGATION REQUEST -> "
            + root.target
        )

        // The page is never destroyed during navigation.
        // Main.qml only changes which persistent page is visible.
        root.authorized(root.target)
    }


    function prepareForTarget(newTarget) {

        clearPatternTimer.stop()
        successTimer.stop()
        lockCountdownTimer.stop()

        navigationPending = false
        target = newTarget

        selectedNodes = []
        drawing = false
        pointerX = 0
        pointerY = 0
        verificationState = 0

        lockedSeconds =
            authManager.remainingLockSeconds()

        messageText.text =
            lockedSeconds > 0
            ? qsTr("ورود موقتاً قفل شده است")
            : qsTr("انگشت خود را روی نقاط بکشید")

        if (lockedSeconds > 0)
            lockCountdownTimer.start()

        patternCanvas.requestPaint()
    }


    function deactivate() {

        drawing = false

        clearPatternTimer.stop()
        successTimer.stop()
        lockCountdownTimer.stop()

        patternCanvas.requestPaint()
    }


    // =========================================================
    // RESET
    // =========================================================

    function resetPattern() {

        selectedNodes = []

        drawing = false

        pointerX = 0
        pointerY = 0

        verificationState = 0

        patternCanvas.requestPaint()
    }


    // =========================================================
    // ADD NODE
    // =========================================================

    function addNode(nodeNumber) {

        if (
            selectedNodes.indexOf(
                nodeNumber
            ) !== -1
        ) {
            return
        }


        var updated =
            selectedNodes.slice()

        updated.push(
            nodeNumber
        )

        selectedNodes = updated

        patternCanvas.requestPaint()
    }


    // =========================================================
    // DETECT NODE
    // =========================================================

    function checkNodeAt(x, y) {

        for (
            var i = 0;
            i < 9;
            i++
        ) {

            var cx =
                patternBoard.nodeCenterX(i)

            var cy =
                patternBoard.nodeCenterY(i)

            var dx = x - cx
            var dy = y - cy

            var distance =
                Math.sqrt(
                    dx * dx
                    + dy * dy
                )


            if (distance <= 28) {

                addNode(
                    i + 1
                )

                return
            }
        }
    }


    // =========================================================
    // SUBMIT PATTERN
    // =========================================================

    function submitPattern() {

        if (navigationPending)
            return

        if (selectedNodes.length < 4) {

            verificationState = -1

            messageText.text =
                qsTr(
                    "الگو باید حداقل ۴ نقطه داشته باشد"
                )

            patternCanvas.requestPaint()

            clearPatternTimer.restart()

            return
        }


        var pattern =
            selectedNodes.join("-")


        console.log(
            "PATTERN SUBMIT -> "
            + pattern
            + " | Target="
            + target
        )


        var result =
            authManager.verifyPattern(
                target,
                pattern
            )


        if (result) {

            verificationState = 1

            messageText.text =
                qsTr("دسترسی تأیید شد")

            patternCanvas.requestPaint()

            successTimer.restart()

        } else {

            verificationState = -1

            patternCanvas.requestPaint()

            clearPatternTimer.restart()
        }
    }


    // =========================================================
    // TITLE
    // =========================================================

    Text {
        id: titleText

        anchors.top: parent.top
        anchors.topMargin: 72

        anchors.horizontalCenter:
            parent.horizontalCenter

        text: qsTr("احراز هویت")

        color: "#F8FAFC"

        font.pixelSize: 28
        font.bold: true
    }


    Text {
        id: instructionText

        anchors.top:
            titleText.bottom

        anchors.topMargin: 3

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("الگوی دسترسی برای ")
            + root.targetName
            + qsTr(" را رسم کنید")

        color: "#94A3B8"

        font.pixelSize: 16
    }


    // =========================================================
    // PATTERN BOARD
    // =========================================================

    Item {
        id: patternBoard

        width: 300
        height: 270

        anchors.top:
            instructionText.bottom

        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter


        function nodeCenterX(index) {

            var column =
                index % 3

            return (
                55
                + column * 95
            )
        }


        function nodeCenterY(index) {

            var row =
                Math.floor(
                    index / 3
                )

            return (
                42
                + row * 92
            )
        }


        function isSelected(nodeNumber) {

            return (
                root.selectedNodes.indexOf(
                    nodeNumber
                ) !== -1
            )
        }


        // =====================================================
        // CONNECTION LINES
        // =====================================================

        Canvas {
            id: patternCanvas

            anchors.fill: parent


            onPaint: {

                var ctx =
                    getContext("2d")

                ctx.reset()


                if (
                    root.selectedNodes.length
                    === 0
                ) {
                    return
                }


                var lineColor =
                    "#38BDF8"


                if (
                    root.verificationState
                    === 1
                ) {

                    lineColor =
                        "#22C55E"

                } else if (
                    root.verificationState
                    === -1
                ) {

                    lineColor =
                        "#EF4444"
                }


                ctx.strokeStyle =
                    lineColor

                ctx.lineWidth = 6

                ctx.lineCap =
                    "round"

                ctx.lineJoin =
                    "round"


                ctx.beginPath()


                for (
                    var i = 0;
                    i <
                    root.selectedNodes.length;
                    i++
                ) {

                    var nodeNumber =
                        root.selectedNodes[i]

                    var index =
                        nodeNumber - 1

                    var x =
                        patternBoard.nodeCenterX(
                            index
                        )

                    var y =
                        patternBoard.nodeCenterY(
                            index
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
                    root.drawing
                    && root.verificationState === 0
                ) {

                    ctx.lineTo(
                        root.pointerX,
                        root.pointerY
                    )
                }


                ctx.stroke()
            }
        }


        // =====================================================
        // NODES
        // =====================================================

        Repeater {
            model: 9


            delegate: Rectangle {

                width: 40
                height: 40

                radius: 20


                x:
                    patternBoard.nodeCenterX(
                        index
                    )
                    - width / 2


                y:
                    patternBoard.nodeCenterY(
                        index
                    )
                    - height / 2


                property bool selected:
                    patternBoard.isSelected(
                        index + 1
                    )


                color: {

                    if (!selected)
                        return "#1E293B"


                    if (
                        root.verificationState
                        === 1
                    )
                        return "#14532D"


                    if (
                        root.verificationState
                        === -1
                    )
                        return "#7F1D1D"


                    return "#164E63"
                }


                border.width:
                    selected ? 4 : 3


                border.color: {

                    if (!selected)
                        return "#64748B"


                    if (
                        root.verificationState
                        === 1
                    )
                        return "#22C55E"


                    if (
                        root.verificationState
                        === -1
                    )
                        return "#EF4444"


                    return "#38BDF8"
                }


                Behavior on scale {

                    NumberAnimation {
                        duration: 100
                    }
                }


                scale:
                    selected
                    ? 1.15
                    : 1.0


                Rectangle {

                    width: 10
                    height: 10

                    radius: 5

                    anchors.centerIn:
                        parent

                    color:
                        selected
                        ? parent.border.color
                        : "#94A3B8"
                }
            }
        }


        // =====================================================
        // TOUCH AREA
        // =====================================================

        MouseArea {
            id: touchArea

            anchors.fill: parent

            enabled:
                root.lockedSeconds <= 0
                && !root.navigationPending


            onPressed: {

                root.resetPattern()

                root.drawing = true

                root.pointerX =
                    mouse.x

                root.pointerY =
                    mouse.y

                root.checkNodeAt(
                    mouse.x,
                    mouse.y
                )

                patternCanvas.requestPaint()
            }


            onPositionChanged: {

                if (!root.drawing)
                    return


                root.pointerX =
                    mouse.x

                root.pointerY =
                    mouse.y


                root.checkNodeAt(
                    mouse.x,
                    mouse.y
                )


                patternCanvas.requestPaint()
            }


            onReleased: {

                if (!root.drawing)
                    return


                root.drawing = false

                patternCanvas.requestPaint()

                root.submitPattern()
            }


            onCanceled: {

                root.resetPattern()
            }
        }
    }


    // =========================================================
    // MESSAGE
    // =========================================================

    Text {
        id: messageText

        anchors.top:
            patternBoard.bottom

        anchors.topMargin: -5

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            root.lockedSeconds > 0
            ? qsTr("ورود موقتاً قفل شده است")
            : qsTr(
                "انگشت خود را روی نقاط بکشید"
            )

        color: {

            if (
                root.verificationState
                === 1
            )
                return "#22C55E"


            if (
                root.verificationState
                === -1
            )
                return "#EF4444"


            if (
                root.lockedSeconds > 0
            )
                return "#F59E0B"


            return "#94A3B8"
        }

        font.pixelSize: 16

        font.bold:
            root.verificationState !== 0
    }


    // =========================================================
    // LOCKOUT TEXT
    // =========================================================

    Text {

        visible:
            root.lockedSeconds > 0

        anchors.top:
            messageText.bottom

        anchors.topMargin: 2

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("زمان باقی‌مانده: ")
            + root.lockedSeconds
            + qsTr(" ثانیه")

        color: "#F59E0B"

        font.pixelSize: 14
    }


    // =========================================================
    // AUTH SIGNALS
    // =========================================================

    Connections {
        target: authManager


        function onAccessDenied(
            eventTarget,
            attempts
        ) {

            if (
                eventTarget !== root.target
            )
                return


            root.remainingAttempts =
                attempts


            messageText.text =
                qsTr(
                    "الگوی وارد شده اشتباه است — "
                )
                + attempts
                + qsTr(
                    " تلاش باقی مانده"
                )
        }


        function onAuthLocked(seconds) {

            root.lockedSeconds =
                seconds

            root.verificationState = 0

            root.selectedNodes = []

            root.drawing = false

            patternCanvas.requestPaint()

            messageText.text =
                qsTr(
                    "تعداد تلاش‌های ناموفق بیش از حد مجاز است"
                )

            lockCountdownTimer.restart()
        }
    }


    // =========================================================
    // CLEAR WRONG PATTERN
    // =========================================================

    Timer {
        id: clearPatternTimer

        interval: 900
        repeat: false


        onTriggered: {

            if (
                root.lockedSeconds <= 0
            ) {

                root.resetPattern()

                messageText.text =
                    qsTr(
                        "انگشت خود را روی نقاط بکشید"
                    )
            }
        }
    }


    // =========================================================
    // SUCCESS
    // =========================================================

    Timer {
        id: successTimer

        interval: 450
        repeat: false


        onTriggered: {

            // Do not destroy this page from inside its own Timer
            // callback. Ask Main.qml to perform the navigation on
            // the next event-loop turn instead.
            root.requestAuthorizedNavigation()
        }
    }


    // =========================================================
    // LOCKOUT COUNTDOWN
    // =========================================================

    Timer {
        id: lockCountdownTimer

        interval: 1000
        repeat: true


        onTriggered: {

            root.lockedSeconds =
                authManager.remainingLockSeconds()


            if (
                root.lockedSeconds <= 0
            ) {

                stop()

                root.resetPattern()

                messageText.text =
                    qsTr(
                        "می‌توانید دوباره تلاش کنید"
                    )
            }
        }
    }
}
