import QtQuick 2.15
import QtQuick.Controls 2.15


Rectangle {
    id: root

    objectName: "homePage"

    // Main.qml owns all navigation.
    signal protectedPageRequested(string target)
    signal lockerStatusRequested()

    color: "#0F172A"

    LayoutMirroring.enabled: true
    LayoutMirroring.childrenInherit: true


    // =========================================================
    // PROTECTED NAVIGATION
    // =========================================================

    function openProtectedPage(target) {

        // Do not create/destroy pages here.
        // Main.qml decides whether authentication is required
        // and selects the already-created destination page.
        root.protectedPageRequested(target)
    }


    // =========================================================
    // TITLE
    // =========================================================

    Text {
        id: title

        anchors.top: parent.top
        anchors.topMargin: 92

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr("سامانه مدیریت کمدها")

        color: "#F8FAFC"

        font.pixelSize: 32
        font.bold: true
    }


    Text {
        id: subtitle

        anchors.top: title.bottom
        anchors.topMargin: 8

        anchors.horizontalCenter:
            parent.horizontalCenter

        text:
            qsTr(
                "لطفاً عملیات مورد نظر را انتخاب کنید"
            )

        color: "#94A3B8"

        font.pixelSize: 17
    }


    // =========================================================
    // MAIN BUTTONS
    // =========================================================

    Row {
        id: mainButtons

        anchors.top: subtitle.bottom
        anchors.topMargin: 38

        anchors.horizontalCenter:
            parent.horizontalCenter

        spacing: 18


        // =====================================================
        // OPEN LOCKER
        // =====================================================

        Button {
            id: openLockerButton

            width: 205
            height: 112


            onClicked: {
                root.openProtectedPage(
                    "open_locker"
                )
            }


            background: Rectangle {

                radius: 16

                color:
                    openLockerButton.pressed
                    ? "#243247"
                    : "#1E293B"

                border.width: 1

                border.color:
                    openLockerButton.pressed
                    ? "#38BDF8"
                    : "#334155"


                Rectangle {

                    width: 5
                    height: parent.height - 24

                    anchors.right:
                        parent.right

                    anchors.rightMargin: 8

                    anchors.verticalCenter:
                        parent.verticalCenter

                    radius: 3

                    color: "#38BDF8"
                }
            }


            contentItem: Item {

                anchors.fill: parent


                Column {

                    anchors.centerIn:
                        parent

                    width:
                        parent.width - 28

                    spacing: 8


                    Text {

                        width: parent.width

                        text:
                            qsTr("باز کردن کمد")

                        color: "#F8FAFC"

                        font.pixelSize: 21
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter
                    }


                    Text {

                        width: parent.width

                        text:
                            qsTr(
                                "انتخاب و باز کردن کمد"
                            )

                        color: "#94A3B8"

                        font.pixelSize: 13

                        horizontalAlignment:
                            Text.AlignHCenter
                    }
                }
            }
        }


        // =====================================================
        // LOCKER STATUS
        // =====================================================

        Button {
            id: lockerStatusButton

            width: 205
            height: 112


            onClicked: {

                root.lockerStatusRequested()
            }


            background: Rectangle {

                radius: 16

                color:
                    lockerStatusButton.pressed
                    ? "#243247"
                    : "#1E293B"

                border.width: 1

                border.color:
                    lockerStatusButton.pressed
                    ? "#22C55E"
                    : "#334155"


                Rectangle {

                    width: 5
                    height: parent.height - 24

                    anchors.right:
                        parent.right

                    anchors.rightMargin: 8

                    anchors.verticalCenter:
                        parent.verticalCenter

                    radius: 3

                    color: "#22C55E"
                }
            }


            contentItem: Item {

                anchors.fill: parent


                Column {

                    anchors.centerIn:
                        parent

                    width:
                        parent.width - 28

                    spacing: 8


                    Text {

                        width: parent.width

                        text:
                            qsTr(
                                "وضعیت کمدها"
                            )

                        color: "#F8FAFC"

                        font.pixelSize: 21
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter
                    }


                    Text {

                        width: parent.width

                        text:
                            qsTr(
                                "مشاهده وضعیت و خطاها"
                            )

                        color: "#94A3B8"

                        font.pixelSize: 13

                        horizontalAlignment:
                            Text.AlignHCenter
                    }
                }
            }
        }


        // =====================================================
        // SETTINGS
        // =====================================================

        Button {
            id: settingsButton

            width: 205
            height: 112


            onClicked: {
                root.openProtectedPage(
                    "settings"
                )
            }


            background: Rectangle {

                radius: 16

                color:
                    settingsButton.pressed
                    ? "#243247"
                    : "#1E293B"

                border.width: 1

                border.color:
                    settingsButton.pressed
                    ? "#F59E0B"
                    : "#334155"


                Rectangle {

                    width: 5
                    height: parent.height - 24

                    anchors.right:
                        parent.right

                    anchors.rightMargin: 8

                    anchors.verticalCenter:
                        parent.verticalCenter

                    radius: 3

                    color: "#F59E0B"
                }
            }


            contentItem: Item {

                anchors.fill: parent


                Column {

                    anchors.centerIn:
                        parent

                    width:
                        parent.width - 28

                    spacing: 8


                    Text {

                        width: parent.width

                        text:
                            qsTr("تنظیمات")

                        color: "#F8FAFC"

                        font.pixelSize: 21
                        font.bold: true

                        horizontalAlignment:
                            Text.AlignHCenter
                    }


                    Text {

                        width: parent.width

                        text:
                            qsTr(
                                "سیستم و وضعیت سخت‌افزار"
                            )

                        color: "#94A3B8"

                        font.pixelSize: 13

                        horizontalAlignment:
                            Text.AlignHCenter
                    }
                }
            }
        }
    }


    // =========================================================
    // STATUS
    // =========================================================

    Rectangle {
        id: statusBox

        width: 300
        height: 38

        anchors.horizontalCenter:
            parent.horizontalCenter

        anchors.bottom:
            parent.bottom

        anchors.bottomMargin: 21

        radius: 12

        color: "#141F31"

        border.width: 1
        border.color: "#25344A"


        Text {
            id: statusText

            anchors.centerIn: parent

            text:
                qsTr("سیستم آماده است")

            color: "#CBD5E1"

            font.pixelSize: 15
        }
    }


    Connections {
        target: backend

        function onStatusChanged(message) {
            statusText.text = message
        }
    }
}