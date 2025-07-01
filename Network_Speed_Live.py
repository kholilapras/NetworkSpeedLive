import psutil
import tkinter as tk
import threading
import time
import sys
import os
import ctypes
import winreg
import webbrowser
from pystray import Icon, MenuItem, Menu
from PIL import Image

def resource_path(relative_path):
    try:
        return os.path.join(sys._MEIPASS, relative_path)
    except AttributeError:
        return os.path.join(os.path.abspath("."), relative_path)

def format_speed(speed_kb):
    return f"{speed_kb / 1024:.2f} MB/s" if speed_kb >= 1024 else f"{speed_kb:.1f} KB/s"

def get_speed():
    old = psutil.net_io_counters()
    time.sleep(0.5)
    new = psutil.net_io_counters()
    download = (new.bytes_recv - old.bytes_recv) / 1024
    upload = (new.bytes_sent - old.bytes_sent) / 1024
    return download, upload

def update_speed():
    global current_speed_dl, current_speed_ul
    while True:
        download, upload = get_speed()
        current_speed_dl = format_speed(download)
        current_speed_ul = format_speed(upload)
        download_text.set(f"↙ {current_speed_dl}")
        upload_text.set(f"↗ {current_speed_ul}")
        time.sleep(0.5)

def enforce_always_on_top():
    while True:
        time.sleep(5)
        try:
            overlay.attributes("-topmost", True)
        except:
            break

def add_to_startup():
    exe_path = os.path.realpath(sys.argv[0])
    reg_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, reg_path, 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "NetSpeedOverlay", 0, winreg.REG_SZ, exe_path)
    except:
        pass

def get_taskbar_height():
    class RECT(ctypes.Structure):
        _fields_ = [("left", ctypes.c_long), ("top", ctypes.c_long),
                    ("right", ctypes.c_long), ("bottom", ctypes.c_long)]
    rect = RECT()
    ctypes.windll.user32.SystemParametersInfoW(0x0030, 0, ctypes.byref(rect), 0)
    return root.winfo_screenheight() - rect.bottom

def start_move(event):
    overlay.x = event.x
    overlay.y = event.y

def do_move(event):
    x = overlay.winfo_x() + (event.x - overlay.x)
    y = overlay.winfo_y() + (event.y - overlay.y)
    overlay.geometry(f"+{x}+{y}")

def create_tray_icon():
    def on_quit(icon, item):
        icon.stop()
        root.quit()

    def on_detail(icon, item):
        detail = tk.Toplevel()
        detail.title("Detail")
        detail.geometry("320x160")
        detail.resizable(False, False)
        detail.iconbitmap(resource_path("icon.ico"))

        tk.Label(detail, text="Network Speed Live", font=("Segoe UI", 12, "bold")).pack(pady=(10, 0))
        tk.Label(detail, text="Version 1.0 (01-07-2025)", font=("Segoe UI", 10)).pack()

        speed_label = tk.Label(detail, text="", font=("Segoe UI", 10))
        speed_label.pack(pady=(10, 5))

        def update_detail_speed():
            while True:
                if not speed_label.winfo_exists():
                    break
                speed_label.config(text=f"↙ Download : {current_speed_dl}\n↗ Upload : {current_speed_ul}")
                time.sleep(0.5)

        link = tk.Label(detail, text="https://github.com/kholilapras/NetworkSpeedLive",
                        fg="blue", cursor="hand2", font=("Segoe UI", 9, "underline"))
        link.pack(side="bottom", pady=10)
        link.bind("<Button-1>", lambda e: webbrowser.open(link.cget("text")))

        threading.Thread(target=update_detail_speed, daemon=True).start()
        detail.attributes("-topmost", True)
        detail.grab_set()

    try:
        icon = Image.open(resource_path("icon.ico"))
        tray = Icon("NetSpeedOverlay", icon, "Network Speed Live", menu=Menu(
            MenuItem("Detail", on_detail),
            MenuItem("Exit", on_quit)
        ))
        tray.run()
    except Exception as e:
        print("Tray icon error:", e)

# ===== Main UI =====
root = tk.Tk()
root.withdraw()
root.iconbitmap(resource_path("icon.ico"))

overlay = tk.Toplevel(root)
overlay.overrideredirect(True)
overlay.wm_attributes("-topmost", True)
overlay.wm_attributes("-transparentcolor", "black")
overlay.configure(bg="black")

# Posisi overlay
w, h = 160, 48
x = 0
y = root.winfo_screenheight() - get_taskbar_height() - h + 45
overlay.geometry(f"{w}x{h}+{x}+{y}")

# Minimize button (custom hanya untuk overlay)
btn_min = tk.Button(overlay, text="🗕", font=("Segoe UI", 9), fg="white", bg="black",
                    bd=0, activebackground="#444", command=lambda: overlay.iconify(), cursor="hand2")
btn_min.place(relx=1.0, x=-10, y=0, anchor="ne")

frame = tk.Frame(overlay, bg="black")
frame.pack(fill="both", expand=True)

download_text = tk.StringVar()
upload_text = tk.StringVar()
current_speed_dl = "0 KB/s"
current_speed_ul = "0 KB/s"

label_dl = tk.Label(frame, textvariable=download_text, fg="white", bg="black", font=("Segoe UI", 10), anchor="w")
label_ul = tk.Label(frame, textvariable=upload_text, fg="white", bg="black", font=("Segoe UI", 10), anchor="w")
label_dl.pack(fill="x", padx=10, pady=(6, 0))
label_ul.pack(fill="x", padx=10, pady=(0, 6))

for widget in (overlay, frame, label_dl, label_ul):
    widget.bind("<Button-1>", start_move)
    widget.bind("<B1-Motion>", do_move)

# Jalankan thread
threading.Thread(target=update_speed, daemon=True).start()
threading.Thread(target=enforce_always_on_top, daemon=True).start()
threading.Thread(target=create_tray_icon, daemon=True).start()

add_to_startup()
root.mainloop()
