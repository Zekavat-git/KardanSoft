import os
import sys
from pathlib import Path

# ============================================================
# NANOPI DISPLAY CONFIGURATION
# Must be defined before QApplication is created.
# ============================================================

os.environ.setdefault(
    "QT_QPA_PLATFORM",
    "linuxfb:fb=/dev/fb0"
)

os.environ.setdefault(
    "QT_QUICK_BACKEND",
    "software"
)

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


# ============================================================
# NANOPI PRODUCTION MODE
# ============================================================

DEVELOPMENT_MODE = False

PREFERRED_FONT_FAMILY = "B Nazanin"
FALLBACK_FONT_FAMILY = "Noto Sans"


def select_application_font(app):
    available_families = set(QFontDatabase().families())

    if PREFERRED_FONT_FAMILY in available_families:
        selected_font = PREFERRED_FONT_FAMILY
        print(
            f"FONT | OK | {PREFERRED_FONT_FAMILY}"
        )

    elif FALLBACK_FONT_FAMILY in available_families:
        selected_font = FALLBACK_FONT_FAMILY
        print(
            "FONT | WARNING | "
            "B Nazanin is not installed."
        )
        print(
            f"FONT | TEMPORARY FALLBACK | {selected_font}"
        )

    else:
        selected_font = app.font().family()
        print(
            "FONT | WARNING | "
            "Neither B Nazanin nor Noto Sans was found."
        )
        print(
            f"FONT | SYSTEM FALLBACK | {selected_font}"
        )

    app.setFont(QFont(selected_font))

    return selected_font


def main():
    print(
        "DISPLAY | "
        f"{os.environ.get('QT_QPA_PLATFORM')}"
    )
    print(
        "QT QUICK BACKEND | "
        f"{os.environ.get('QT_QUICK_BACKEND')}"
    )

    app = QApplication(sys.argv)

    # --------------------------------------------------------
    # FONT
    # --------------------------------------------------------

    selected_font = select_application_font(app)

    # --------------------------------------------------------
    # QML ENGINE
    # --------------------------------------------------------

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

    locker_manager = LockerManager(
        database=database
    )

    locker_controller = LockerController(
        locker_manager
    )

    # Real hardware transport has not yet been attached.
    # Therefore:
    #
    # - No Simulator
    # - No SimulatorTransport
    # - No fake physical feedback
    #
    # We create only the logical locker structure.

    for locker_id in range(1, 13):
        locker_manager.add_locker(
            locker_id=locker_id,
            slave_address=1,
            channel=locker_id,
        )

    locker_model = LockerListModel(
        locker_manager
    )

    # --------------------------------------------------------
    # QML CONTEXT
    # --------------------------------------------------------

    context = engine.rootContext()

    context.setContextProperty(
        "developmentMode",
        DEVELOPMENT_MODE
    )

    context.setContextProperty(
        "backend",
        backend
    )

    context.setContextProperty(
        "appState",
        app_state
    )

    context.setContextProperty(
        "authManager",
        auth_manager
    )

    context.setContextProperty(
        "lockerManager",
        locker_manager
    )

    context.setContextProperty(
        "lockerController",
        locker_controller
    )

    context.setContextProperty(
        "lockerModel",
        locker_model
    )

    context.setContextProperty(
        "applicationFontFamily",
        selected_font
    )

    # --------------------------------------------------------
    # LOAD MAIN GUI
    # --------------------------------------------------------

    main_qml = (
        base_dir
        / "gui"
        / "Main.qml"
    )

    print(
        f"QML LOAD | {main_qml}"
    )

    engine.load(
        QUrl.fromLocalFile(
            str(main_qml)
        )
    )

    if not engine.rootObjects():
        print(
            "ERROR | Main.qml could not be loaded."
        )

        database.close()

        return 1

    root = engine.rootObjects()[0]

    # Main.qml is designed for 800x480.
    # Ensure that the top-level window is visible.
    try:
        root.setProperty(
            "width",
            800
        )

        root.setProperty(
            "height",
            480
        )

        root.setProperty(
            "visible",
            True
        )

    except Exception as exc:
        print(
            f"WINDOW | WARNING | {exc}"
        )

    print(
        "MODE | NANOPI PRODUCTION GUI"
    )

    print(
        "SIMULATOR | DISABLED"
    )

    print(
        "FRAMEBUFFER | /dev/fb0 | 800x480"
    )

    print(
        "QT EVENT LOOP | START"
    )

    exit_code = app.exec_()

    database.close()

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
