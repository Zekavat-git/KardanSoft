import sys
from pathlib import Path

from PyQt5.QtCore import QUrl
from PyQt5.QtGui import QFont
from PyQt5.QtQml import QQmlApplicationEngine
from PyQt5.QtWidgets import QApplication

from backend import Backend
from app_state import AppState
from simulator import Simulator

from core.auth_manager import AuthManager
from core.locker import LockerState
from core.locker_manager import LockerManager
from core.locker_list_model import LockerListModel

from hardware.simulator_transport import (
    SimulatorTransport,
)

from locker_controller import (
    LockerController,
)

from storage.database import (
    LockerDatabase,
)


DEVELOPMENT_MODE = True


def main():

    app = QApplication(sys.argv)

    app.setFont(
        QFont("B Nazanin")
    )

    engine = QQmlApplicationEngine()

    # ========================================================
    # BASIC APPLICATION OBJECTS
    # ========================================================

    backend = Backend()

    app_state = AppState()

    simulator = Simulator(
        app_state
    )

    # ========================================================
    # AUTHENTICATION
    # ========================================================

    auth_manager = AuthManager()

    # ========================================================
    # SQLITE DATABASE
    # ========================================================

    base_dir = (
        Path(__file__)
        .resolve()
        .parent
    )

    database = LockerDatabase(
        base_dir
        / "data"
        / "kardansoft.db"
    )

    # ========================================================
    # LOCKER CORE
    # ========================================================

    locker_manager = LockerManager(
        database=database
    )

    locker_transport = (
        SimulatorTransport()
    )

    locker_controller = (
        LockerController(
            locker_manager
        )
    )

    # ========================================================
    # CREATE DEVELOPMENT LOCKERS
    # ========================================================

    for locker_id in range(
        1,
        13
    ):

        locker_manager.add_locker(
            locker_id=locker_id,
            slave_address=1,
            channel=locker_id
        )

    # ========================================================
    # MANAGER <-> TRANSPORT
    # ========================================================

    locker_manager.openCommandRequested.connect(
        locker_transport.send_open
    )

    locker_transport.feedbackReceived.connect(
        locker_manager.process_feedback
    )

    # ========================================================
    # INITIAL SIMULATED FEEDBACK
    # ========================================================

    for locker_id in range(
        1,
        13
    ):

        locker_manager.process_feedback(
            locker_id,
            False
        )

    # ========================================================
    # QML LOCKER MODEL
    # ========================================================

    locker_model = LockerListModel(
        locker_manager
    )

    # ========================================================
    # DEVELOPMENT STRUCTURE FEEDBACK
    # ========================================================

    def initialize_new_simulated_lockers():

        if not DEVELOPMENT_MODE:
            return

        for locker in (
            locker_manager.get_all_lockers()
        ):

            if (
                locker.actual_state
                == LockerState.UNKNOWN
            ):

                locker_manager.process_feedback(
                    locker.locker_id,
                    False
                )

    locker_manager.lockerStructureChanged.connect(
        initialize_new_simulated_lockers
    )

    # ========================================================
    # QML CONTEXT
    # ========================================================

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
        "simulator",
        simulator
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
        "lockerTransport",
        locker_transport
    )

    context.setContextProperty(
        "lockerModel",
        locker_model
    )

    # ========================================================
    # LOAD MAIN GUI
    # ========================================================

    main_qml = (
        base_dir
        / "gui"
        / "Main.qml"
    )

    print(
        "QML LOAD | MAIN | START"
    )

    engine.load(
        QUrl.fromLocalFile(
            str(main_qml)
        )
    )

    print(
        "QML LOAD | MAIN | DONE"
    )

    if not engine.rootObjects():

        print(
            "ERROR: Main.qml could not be loaded."
        )

        return -1

    # ========================================================
    # DEVELOPMENT SIMULATOR
    # ========================================================

    if DEVELOPMENT_MODE:

        simulator_qml = (
            base_dir
            / "gui"
            / "SimulatorWindow.qml"
        )

        print(
            "QML LOAD | SIMULATOR | START"
        )

        engine.load(
            QUrl.fromLocalFile(
                str(simulator_qml)
            )
        )

        print(
            "QML LOAD | SIMULATOR | DONE"
        )

    print(
        "QT EVENT LOOP | START"
    )

    exit_code = app.exec_()

    database.close()

    return exit_code


if __name__ == "__main__":

    sys.exit(
        main()
    )
