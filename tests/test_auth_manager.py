from core.auth_manager import AuthManager


auth = AuthManager()


# ============================================================
# SIGNAL MONITORING
# ============================================================

auth.accessGranted.connect(
    lambda target:
    print(
        f"SIGNAL -> ACCESS GRANTED | "
        f"Target={target}"
    )
)


auth.accessDenied.connect(
    lambda target, remaining:
    print(
        f"SIGNAL -> ACCESS DENIED | "
        f"Target={target} | "
        f"Remaining={remaining}"
    )
)


auth.authLocked.connect(
    lambda seconds:
    print(
        f"SIGNAL -> AUTH LOCKED | "
        f"{seconds} seconds"
    )
)


auth.sessionChanged.connect(
    lambda:
    print(
        f"SIGNAL -> SESSION | "
        f"Operator={auth.operatorAuthenticated} | "
        f"Admin={auth.adminAuthenticated}"
    )
)


# ============================================================
# TEST 1
# WRONG OPERATOR PATTERN
# ============================================================

print()
print("=" * 60)
print("TEST 1 - WRONG OPERATOR PATTERN")
print("=" * 60)

result = auth.verifyPattern(
    "open_locker",
    "1-2-3-4"
)

print(
    f"Result = {result}"
)


# ============================================================
# TEST 2
# CORRECT OPERATOR PATTERN
# ============================================================

print()
print("=" * 60)
print("TEST 2 - CORRECT OPERATOR PATTERN")
print("=" * 60)

result = auth.verifyPattern(
    "open_locker",
    "1-2-5-8"
)

print(
    f"Result = {result}"
)

print(
    "Open locker authorized =",
    auth.isAuthorized("open_locker")
)

print(
    "Settings authorized =",
    auth.isAuthorized("settings")
)


# ============================================================
# TEST 3
# OPERATOR CANNOT ENTER SETTINGS
# ============================================================

print()
print("=" * 60)
print("TEST 3 - OPERATOR PATTERN FOR SETTINGS")
print("=" * 60)

result = auth.verifyPattern(
    "settings",
    "1-2-5-8"
)

print(
    f"Result = {result}"
)


# ============================================================
# TEST 4
# CORRECT ADMIN PATTERN
# ============================================================

print()
print("=" * 60)
print("TEST 4 - ADMIN PATTERN")
print("=" * 60)

result = auth.verifyPattern(
    "settings",
    "3-2-1-4-7"
)

print(
    f"Result = {result}"
)

print(
    "Open locker authorized =",
    auth.isAuthorized("open_locker")
)

print(
    "Settings authorized =",
    auth.isAuthorized("settings")
)


# ============================================================
# TEST 5
# LOGOUT
# ============================================================

print()
print("=" * 60)
print("TEST 5 - LOGOUT")
print("=" * 60)

auth.logoutAll()

print(
    "Open locker authorized =",
    auth.isAuthorized("open_locker")
)

print(
    "Settings authorized =",
    auth.isAuthorized("settings")
)


print()
print("=" * 60)
print("AUTH TEST FINISHED")
print("=" * 60)