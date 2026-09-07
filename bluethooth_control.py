import ctypes
import ctypes.wintypes as wintypes

def gen_single_touch_input():
    """
    Listens for a single earbud media-key tap.
    Returns 'yes' (right double-tap / next track),
            'no'  (left double-tap / previous track),
            or None if Esc was pressed before any tap.
    """
    result = [None]

    WH_KEYBOARD_LL = 13
    WM_KEYDOWN = 0x0100

    VK_MEDIA_NEXT_TRACK = 0xB0   # commonly: RIGHT earbud double-tap
    VK_MEDIA_PREV_TRACK = 0xB1   # commonly: LEFT earbud double-tap
    VK_ESCAPE = 0x1B

    user32 = ctypes.windll.user32

    user32.SetWindowsHookExA.restype = wintypes.HHOOK
    user32.SetWindowsHookExA.argtypes = (
        ctypes.c_int,
        ctypes.c_void_p,
        wintypes.HINSTANCE,
        wintypes.DWORD
    )

    user32.CallNextHookEx.restype = ctypes.c_long
    user32.CallNextHookEx.argtypes = (
        wintypes.HHOOK,
        ctypes.c_int,
        wintypes.WPARAM,
        wintypes.LPARAM
    )

    user32.GetMessageA.argtypes = (
        ctypes.POINTER(wintypes.MSG),
        wintypes.HWND,
        ctypes.c_uint,
        ctypes.c_uint
    )

    class KBDLLHOOKSTRUCT(ctypes.Structure):
        _fields_ = [
            ("vkCode", wintypes.DWORD),
            ("scanCode", wintypes.DWORD),
            ("flags", wintypes.DWORD),
            ("time", wintypes.DWORD),
            ("dwExtraInfo", ctypes.c_void_p),
        ]

    def gen_touch_control(nCode, wParam, lParam):
        if nCode == 0 and wParam == WM_KEYDOWN:
            kb = ctypes.cast(lParam, ctypes.POINTER(KBDLLHOOKSTRUCT)).contents
            vk_code = kb.vkCode

            if vk_code == VK_MEDIA_NEXT_TRACK:
                result[0] = "yes"
                print("Right double-tap detected -> yes")
                user32.PostQuitMessage(0)   # exit immediately after one input
            elif vk_code == VK_MEDIA_PREV_TRACK:
                result[0] = "no"
                print("Left double-tap detected -> no")
                user32.PostQuitMessage(0)
            elif vk_code == VK_ESCAPE:
                print("Esc pressed. Exiting without input.")
                user32.PostQuitMessage(0)

        return user32.CallNextHookEx(hook_id, nCode, wParam, lParam)

    HOOKPROC = ctypes.WINFUNCTYPE(ctypes.c_int, ctypes.c_int, wintypes.WPARAM, wintypes.LPARAM)
    pointer = HOOKPROC(gen_touch_control)

    hook_id = user32.SetWindowsHookExA(WH_KEYBOARD_LL, pointer, None, 0)

    if not hook_id:
        raise ctypes.WinError(ctypes.get_last_error())

    print("touch control loaded")

    msg = wintypes.MSG()
    try:
        while user32.GetMessageA(ctypes.byref(msg), None, 0, 0) != 0:
            user32.TranslateMessage(ctypes.byref(msg))
            user32.DispatchMessageA(ctypes.byref(msg))
    except KeyboardInterrupt:
        pass
    finally:
        user32.UnhookWindowsHookEx(hook_id)

    return result[0]