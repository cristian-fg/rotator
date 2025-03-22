import dxcam
import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32api
from ctypes import windll

# Make app DPI-aware
windll.user32.SetProcessDPIAware()

class DxWindowRotator:
    def __init__(self, target_window_title):
        self.target_hwnd = win32gui.FindWindow(None, target_window_title)
        if self.target_hwnd == 0:
            raise Exception("Target window not found")
        
        # Get screen dimensions using Windows API
        self.screen_width = win32api.GetSystemMetrics(0)
        self.screen_height = win32api.GetSystemMetrics(1)
        
        # Initialize DXCAM
        self.cam = dxcam.create(output_idx=0, output_color="BGR")
        self.cam.start(target_fps=60)
        
        # Create Tkinter window
        self.root = tk.Tk()
        self.root.title("Rotated Window - DX")
        self.root.attributes("-topmost", True)
        self.root.configure(bg='black')
        
        # Set up canvas
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        
        # Start update loop
        self.tk_image = None
        self.update()

    def get_valid_region(self):
        try:
            # Get window client rect
            rect = win32gui.GetClientRect(self.target_hwnd)
            left, top = win32gui.ClientToScreen(self.target_hwnd, (rect[0], rect[1]))
            right = left + (rect[2] - rect[0])
            bottom = top + (rect[3] - rect[1])

            # Clamp coordinates to screen bounds
            left = max(0, min(left, self.screen_width - 1))
            top = max(0, min(top, self.screen_height - 1))
            right = max(left + 1, min(right, self.screen_width))
            bottom = max(top + 1, min(bottom, self.screen_height))

            return (left, top, right, bottom)
        except Exception as e:
            print(f"Region error: {e}")
            return None

    def capture_window(self):
        try:
            region = self.get_valid_region()
            if not region:
                return None
                
            frame = self.cam.grab(region=region)
            return Image.fromarray(frame) if frame is not None else None
        except Exception as e:
            print(f"Capture error: {e}")
            return None

    def update(self):
        try:
            if not win32gui.IsWindowVisible(self.target_hwnd):
                self.root.after(10, self.update)
                return

            img = self.capture_window()
            if img:
                rotated = img.rotate(90, expand=True)
                new_width, new_height = rotated.size
                
                self.root.geometry(f"{new_width}x{new_height}")
                self.tk_image = ImageTk.PhotoImage(rotated)
                self.canvas.delete("all")
                self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            
            self.root.after(10, self.update)
        except Exception as e:
            print(f"Update error: {e}")
            self.cam.stop()
            self.root.destroy()

if __name__ == "__main__":
    rotator = DxWindowRotator("10.66.47.2 AdvantageScope")
    rotator.root.mainloop()