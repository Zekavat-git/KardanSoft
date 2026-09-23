import QtQuick 2.15
import QtQuick.Controls 2.15
import QtQuick.Window 2.15


ApplicationWindow {
    id: root

    visible: true

    width: 410
    height: 650

    title: "KardanSoft - Simulator"

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    ScrollView {
        anchors.fill: parent
        anchors.margins: 16

        clip: true


        Column {
            width: 370

            spacing: 14


            // =================================================
            // TITLE
            // =================================================

            Text {
                width: parent.width

                text: qsTr("شبیه‌ساز توسعه KardanSoft")

                color: "#F8FAFC"

                font.pixelSize: 23
                font.bold: true

                horizontalAlignment: Text.AlignHCenter
            }


            Text {
                width: parent.width

                text: qsTr("کنترل وضعیت سیستم و شبیه‌سازی سخت‌افزار")

                color: "#94A3B8"

                font.pixelSize: 14

                horizontalAlignment: Text.AlignHCenter
            }


            // =================================================
            // POWER / NETWORK
            // =================================================

            Rectangle {
                width: parent.width
                height: 180

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 10


                    Text {
                        width: parent.width

                        text: qsTr("سیستم")

                        color: "#F8FAFC"

                        font.pixelSize: 19
                        font.bold: true

                        horizontalAlignment: Text.AlignRight
                    }


                    Row {
                        width: parent.width

                        spacing: 10


                        Button {
                            width: 160
                            height: 42

                            text: qsTr("تغییر وضعیت برق")

                            onClicked: {
                                simulator.toggleMainsPower()
                            }
                        }


                        Button {
                            width: 160
                            height: 42

                            text: qsTr("تغییر وضعیت شبکه")

                            onClicked: {
                                simulator.toggleEthernet()
                            }
                        }
                    }


                    Row {
                        width: parent.width

                        spacing: 7


                        Button {
                            width: 103
                            height: 40

                            text: qsTr("باتری 86٪")

                            onClicked: {
                                simulator.normalBattery()
                            }
                        }


                        Button {
                            width: 103
                            height: 40

                            text: qsTr("باتری 25٪")

                            onClicked: {
                                simulator.lowBattery()
                            }
                        }


                        Button {
                            width: 103
                            height: 40

                            text: qsTr("باتری 10٪")

                            onClicked: {
                                simulator.criticalBattery()
                            }
                        }
                    }
                }
            }


            // =================================================
            // NORMAL LOCKER OPERATION
            // =================================================

            Rectangle {
                width: parent.width
                height: 125

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 12


                    Text {
                        width: parent.width

                        text: qsTr("تست عملکرد عادی")

                        color: "#22C55E"

                        font.pixelSize: 18
                        font.bold: true

                        horizontalAlignment: Text.AlignRight
                    }


                    Button {
                        width: parent.width
                        height: 45

                        text: qsTr("باز کردن عادی کمد ۱")

                        onClicked: {
                            lockerController.openLocker(1)
                        }
                    }
                }
            }


            // =================================================
            // UNEXPECTED OPEN
            // =================================================

            Rectangle {
                width: parent.width
                height: 125

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 12


                    Text {
                        width: parent.width

                        text: qsTr("تست باز شدن غیرمجاز")

                        color: "#F59E0B"

                        font.pixelSize: 18
                        font.bold: true

                        horizontalAlignment: Text.AlignRight
                    }


                    Button {
                        width: parent.width
                        height: 45

                        text: qsTr("باز کردن غیرمجاز کمد ۲")

                        onClicked: {
                            lockerTransport.forceOpen(2)
                        }
                    }
                }
            }


            // =================================================
            // FAILED TO OPEN
            // =================================================

            Rectangle {
                width: parent.width
                height: 145

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 8


                    Text {
                        width: parent.width

                        text: qsTr("تست خطای باز نشدن")

                        color: "#EF4444"

                        font.pixelSize: 18
                        font.bold: true

                        horizontalAlignment: Text.AlignRight
                    }


                    Text {
                        width: parent.width

                        text: qsTr("فرمان ارسال می‌شود ولی Feedback باز شدن دریافت نمی‌شود.")

                        color: "#94A3B8"

                        font.pixelSize: 13

                        wrapMode: Text.WordWrap

                        horizontalAlignment: Text.AlignRight
                    }


                    Button {
                        width: parent.width
                        height: 44

                        text: qsTr("شبیه‌سازی خطای کمد ۳")

                        onClicked: {

                            lockerTransport.failNextCommand()

                            lockerController.openLocker(3)
                        }
                    }
                }
            }


            // =================================================
            // RESET LOCKER 2
            // =================================================

            Rectangle {
                width: parent.width
                height: 105

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 10


                    Text {
                        width: parent.width

                        text: qsTr("کنترل دستی")

                        color: "#38BDF8"

                        font.pixelSize: 18
                        font.bold: true

                        horizontalAlignment: Text.AlignRight
                    }


                    Button {
                        width: parent.width
                        height: 42

                        text: qsTr("بستن مجدد کمد ۲")

                        onClicked: {
                            lockerTransport.forceClose(2)
                        }
                    }
                }
            }


            // =================================================
            // OCCUPANCY / ASSIGNMENT
            // =================================================

            Rectangle {
                width: parent.width
                height: 245

                radius: 16

                color: "#1E293B"

                border.width: 1
                border.color: "#334155"


                Column {
                    anchors.fill: parent
                    anchors.margins: 15

                    spacing: 10


                    Text {
                        width: parent.width

                        text:
                            qsTr("شبیه‌سازی تخصیص کمد")

                        color: "#A78BFA"

                        font.pixelSize: 18
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignRight
                    }


                    Text {
                        width: parent.width

                        text:
                            qsTr(
                                "شماره کمد و نام فرد را انتخاب کنید."
                            )

                        color: "#94A3B8"

                        font.pixelSize: 12

                        horizontalAlignment:
                            Text.AlignRight
                    }


                    Row {
                        width: parent.width

                        spacing: 10


                        Text {
                            width: 95
                            height: 38

                            text:
                                qsTr("شماره کمد")

                            color: "#CBD5E1"

                            font.pixelSize: 14

                            horizontalAlignment:
                                Text.AlignRight

                            verticalAlignment:
                                Text.AlignVCenter
                        }


                        SpinBox {
                            id: occupancyLockerId

                            width: 210
                            height: 38

                            from: 1
                            to: 12
                            value: 4

                            editable: true
                        }
                    }


                    Row {
                        width: parent.width

                        spacing: 10


                        Text {
                            width: 95
                            height: 38

                            text:
                                qsTr("نام فرد")

                            color: "#CBD5E1"

                            font.pixelSize: 14

                            horizontalAlignment:
                                Text.AlignRight

                            verticalAlignment:
                                Text.AlignVCenter
                        }


                        TextField {
                            id: occupancyOwnerName

                            width: 210
                            height: 38

                            placeholderText:
                                qsTr("مثلاً کاربر تست")

                            text:
                                qsTr("کاربر تست")

                            horizontalAlignment:
                                Text.AlignRight
                        }
                    }


                    Row {
                        width: parent.width

                        spacing: 10


                        Button {
                            width: 160
                            height: 42

                            text:
                                qsTr("پر / تخصیص")

                            onClicked: {

                                var owner =
                                    occupancyOwnerName.text.trim()

                                lockerManager.assignLocker(
                                    occupancyLockerId.value,
                                    owner
                                )
                            }
                        }


                        Button {
                            width: 160
                            height: 42

                            text:
                                qsTr("آزاد کردن")

                            onClicked: {

                                lockerManager.releaseLocker(
                                    occupancyLockerId.value
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}