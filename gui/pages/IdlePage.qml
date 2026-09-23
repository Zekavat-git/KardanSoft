import QtQuick 2.15
import QtQuick.Controls 2.15

Rectangle {
    id: root

    objectName: "idlePage"

    color: "#0F172A"


    Image {
        anchors.fill: parent

        source: "../../resources/images/gym_idle.png"

        fillMode: Image.PreserveAspectCrop

        asynchronous: true
        cache: true
        smooth: true
    }


    // لایه‌ی تیره برای خوانایی بهتر
    Rectangle {
        anchors.fill: parent
        color: "#22000000"
    }

    // هیچ متن اضافه‌ای اینجا نمی‌گذاریم
    // چون خود تصویر عبارت «برای شروع صفحه را لمس کنید» را دارد
}