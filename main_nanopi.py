import sys
from pathlib import Path

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont, QFontDatabase
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

from backend import Backend
from app_state import AppState

from core.auth_manager import AuthManager
from core.locker_manager import LockerManager
from core.locker_list_model import LockerListModel

from locker_controller import LockerController
from storage.database import LockerDatabase


# NanoPi production GUI mode:
# - Full-screen 800x480 through Main.qml
# - No SimulatorWindow
# - No Simulator object
# - No SimulatorTransport / fake locker feedback
DEVELOPMENT_MODE = False
REQUIRED_FONT_FAMILY = "B Nazanin"


def main():
    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # FONT CHECK
    # --------------------------------------------------------
    available_families = set(QFontDatabase().families())

    if REQUIRED_FONT_FAMILY not in available_families:
        print(
            "FONT ERROR | Required font is not installed: "
            f"{REQUIRED_FONT_FAMILY}"
        )
        print(
            "Install B Nazanin on Linux, run fc-cache -f, then "
            "verify with: fc-match 'B Nazanin'"
        )
        return 2

    app.setFont(QFont(REQUIRED_FONT_FAMILY))
    print(f"FONT | OK | {REQUIRED_FONT_FAMILY}")

    engine = QQmlApplicationEngine()

    # --------------------------------------------------------
    # BASIC APPLICATION OBJECTS
    # --------------------------------------------------------
    backend = Backend()
    app_state = AppState()

    # --------------------------------------------------------
    # AUTHENTICATION
    # --------------------------------------------------------
    auth_manager = AuthManager()

    # --------------------------------------------------------
    # SQLITE DATABASE
    # --------------------------------------------------------
    base_dir = Path(__file__).resolve().parent

    database = LockerDatabase(
        base_dir / "data" / "kardansoft.db"
    )

    # --------------------------------------------------------
    # LOCKER CORE
    # --------------------------------------------------------
    locker_manager = LockerManager(database=database)
    locker_controller = LockerController(locker_manager)

    # Until the real Wired/Wireless hardware transport is connected,
    # create the default logical locker structure only. Physical state
    # stays UNKNOWN because no simulated feedback is injected.
    for locker_id in range(1, 13):
        locker_manager.add_locker(
            locker_id=locker_id,
            slave_address=1,
            channel=locker_id,
        )

    locker_model = LockerListModel(locker_manager)

    # --------------------------------------------------------
    # QML CONTEXT
    # --------------------------------------------------------
    context = engine.rootContext()

    context.setContextProperty("developmentMode", DEVELOPMENT_MODE)
    context.setContextProperty("backend", backend)
    context.setContextProperty("appState", app_state)
    context.setContextProperty("authManager", auth_manager)
    context.setContextProperty("lockerManager", locker_manager)
    context.setContextProperty("lockerController", locker_controller)
    context.setContextProperty("lockerModel", locker_model)

    # --------------------------------------------------------
    # LOAD MAIN GUI ONLY
    # --------------------------------------------------------
    main_qml = base_dir / "gui" / "Main.qml"

    print("QML LOAD | MAIN | START")
    engine.load(QUrl.fromLocalFile(str(main_qml)))
    print("QML LOAD | MAIN | DONE")

    if not engine.rootObjects():
        print("ERROR: Main.qml could not be loaded.")
        database.close()
        return -1

    print("MODE | NANOPI PRODUCTION GUI | NO SIMULATOR")
    print("QT EVENT LOOP | START")

    exit_code = app.exec_()

    database.close()
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
