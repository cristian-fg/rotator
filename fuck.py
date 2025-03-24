import dxcam
import tkinter as tk
from PIL import Image, ImageTk
import win32gui
import win32api
import win32con
from ctypes import windll

# Make app DPI-aware
windll.user32.SetProcessDPIAware()
full_width = win32api.GetSystemMetrics(0)
full_height = win32api.GetSystemMetrics(1)

class InteractiveMagnifier:
    def __init__(self, target_window_title, 
                 initial_zoom=2.0, initial_size=400,
                 pos_x=0, pos_y=0):
        self.target_hwnd = win32gui.FindWindow(None, target_window_title)
        if self.target_hwnd == 0:
            raise Exception("Target window not found")
        
        # Capture parameters
        self.zoom = initial_zoom
        self.src_w = initial_size
        self.src_h = initial_size
        self.src_x = 0
        self.src_y = 0
        
        # Mouse drag tracking
        self.drag_start = None
        self.drag_offset = (0, 0)
        
        # Window setup
        self.root = tk.Tk()
        self.root.title("Interactive Magnifier")
        self.root.geometry(f"{int(initial_size*self.zoom)}x{int(initial_size*self.zoom)}+{pos_x}+{pos_y}")
        self.root.configure(bg='black')
        
        # Canvas setup with mouse bindings
        self.canvas = tk.Canvas(self.root, bg='black', highlightthickness=0)
        self.canvas.pack(fill=tk.BOTH, expand=True)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.do_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)
        
        # DXCAM setup
        self.cam = dxcam.create(output_idx=0, output_color="RGB")
        self.cam.start(target_fps=60)
        
        self.tk_image = None
        self.update()

        self.status_var = tk.StringVar()
        self.status_label = tk.Label(
            self.root, 
            textvariable=self.status_var,
            fg="white",
            bg="black"
        )
        self.status_label.pack(side=tk.BOTTOM, fill=tk.X)
        
        # Add keyboard binding
        self.root.bind("<p>", self.print_position)

    def print_position(self, event=None):
        """Print current capture position to console and status"""
        status_text = f"Capture Position: X={self.src_x}, Y={self.src_y}"
        print(status_text)
        self.status_var.set(status_text)

    def get_target_position(self):
        self.print_position
        """Returns (left, top) of target window's client area in screen coords"""
        try:
            return win32gui.ClientToScreen(self.target_hwnd, (0, 0))
        except:
            return (0, 0)

    def update_capture_region(self, dx, dy):
        """Adjust capture coordinates based on mouse drag"""
        target_left, target_top = self.get_target_position()
        
        # Convert screen drag to target window coordinates
        self.src_x = max(0, min(
            self.src_x + dx/self.zoom,
            win32gui.GetClientRect(self.target_hwnd)[2] - self.src_w
        ))
        self.src_y = max(0, min(
            self.src_y + dy/self.zoom,
            win32gui.GetClientRect(self.target_hwnd)[3] - self.src_h
        ))

    def start_drag(self, event):
        """Begin mouse drag operation"""
        self.drag_start = (event.x_root, event.y_root)
        self.drag_offset = (self.src_x, self.src_y)

    def do_drag(self, event):
        """Handle mouse dragging"""
        if self.drag_start:
            # Calculate drag delta in screen coordinates
            dx = event.x_root - self.drag_start[0]
            dy = event.y_root - self.drag_start[1]
            
            # Convert to target window space
            self.update_capture_region(-dx, -dy)
            self.drag_start = (event.x_root, event.y_root)

    def end_drag(self, event):
        self.drag_start = None
        self.print_position()
        """Finish drag operation"""
        self.drag_start = None

    def get_capture_region(self):
        """Calculate current capture bounds"""
        try:
            target_left, target_top = self.get_target_position()
            return (
                target_left + int(self.src_x),
                target_top + int(self.src_y),
                target_left + int(self.src_x) + self.src_w,
                target_top + int(self.src_y) + self.src_h
            )
        except:
            return None

    def capture_and_process(self):
        region = self.get_capture_region()
        if not region:
            return None
            
        frame = self.cam.grab(region=region)
        if frame is None:
            return None
            
        img = Image.fromarray(frame)
        rotated = img.rotate(90, expand=True)
        scaled = rotated.resize(
            (int(rotated.width * self.zoom), 
             int(rotated.height * self.zoom)),
            Image.Resampling.NEAREST
        )
        return scaled

    def update(self):
        try:
            if win32gui.IsWindowVisible(self.target_hwnd):
                processed = self.capture_and_process()
                if processed:
                    self.tk_image = ImageTk.PhotoImage(processed)
                    self.canvas.delete("all")
                    self.canvas.create_image(0, 0, anchor=tk.NW, image=self.tk_image)
            
            self.root.after(10, self.update)
        except Exception as e:
            print(f"Update error: {e}")
            self.cam.stop()
            self.root.destroy()

def move_resize_window(window_title, new_x, new_y, new_width, new_height):
    hwnd = win32gui.FindWindow(None, window_title)
    if hwnd == 0:
        print("Window not found")
        return

    win32gui.SetWindowPos(
        hwnd,
        win32con.HWND_TOP,
        new_x,
        new_y,
        new_width,
        new_height,
        win32con.SWP_SHOWWINDOW
    )

if __name__ == "__main__":
    # Configure AdvantageScope window
    move_resize_window("AdvantageScope",
                      int(full_width/2.84),
                      int(full_height/4),
                      int(full_width/1.42),
                      int(full_height/1.33))

    # Create interactive magnifier
    magnifier = InteractiveMagnifier(
        "AdvantageScope",
        initial_zoom=2.0,
        initial_size=400,
        pos_x=int(full_width / 1690),
        pos_y=int(full_height / 700)
    )
    
    magnifier.root.mainloop()