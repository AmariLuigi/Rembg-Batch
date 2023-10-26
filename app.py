import os
import tempfile
import tkinter as tk
from tkinter import ttk, filedialog, messagebox
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
from rembg import remove
import pyautogui
import pyperclip
import threading

class BatchBackgroundRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Background Remover")
        
        self.images = []
        self.current_image_index = 0
        self.current_image_path = None

        self.initialize_arrows()
        self.canvas_width = 800
        self.canvas_height = 600
        self.pil_image = None
        self.photo_image = None
        self.image_obj_id = None
        self.zoom_factors = [0.1, 0.2, 0.3, 0.5, 0.7, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0]
        self.current_zoom_level = 5
        self.processed_images = {}
        self.output_directory = None
        self.color_picker_cursor_active = False

        self.create_gui_elements()
        self.bind_events()
    

    def toggle_color_picker(self):
        if self.color_picker_cursor_active:
            self.color_picker_cursor_active = False
            self.root.config(cursor="")
        else:
            self.color_picker_cursor_active = True
            self.root.config(cursor="cross")  # Set the cursor to a crosshair cursor
    
    def capture_color(self, event):
        if self.color_picker_cursor_active:
            x, y = pyautogui.position()  # Get the current cursor position on the screen
            color = pyautogui.screenshot().getpixel((x, y))  # Capture the color at the cursor's position

            hex_color = "#{:02x}{:02x}{:02x}".format(color[0], color[1], color[2])
            self.color_label.config(text=f"Picked Color: {hex_color}", bg=hex_color)
            pyperclip.copy(hex_color)
            self.toggle_color_picker()



    def initialize_arrows(self):
        self.arrow_images = {
            "left": self.load_and_resize_arrow("Arrows-Back.512.png", (24, 24)),
            "right": self.load_and_resize_arrow("Arrows-Forward.512.png", (24, 24))
        }

    def create_gui_elements(self):
        self.canvas = tk.Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill="both", expand=True)

        # Create a frame for the arrow buttons and pack them to the top
        arrow_button_frame = tk.Frame(self.root)
        self.prev_image_button = tk.Button(arrow_button_frame, image=self.arrow_images["left"], command=self.show_previous_image)
        self.next_image_button = tk.Button(arrow_button_frame, image=self.arrow_images["right"], command=self.show_next_image)
        self.prev_image_button.pack(side="left")
        self.next_image_button.pack(side="right")

        # Create a frame for the other buttons and use grid to center them
        button_frame = tk.Frame(self.root)
        self.upload_button = tk.Button(button_frame, text="Upload Images", command=self.upload_images)
        self.process_button = tk.Button(button_frame, text="Process Images", command=self.process_images)
        self.save_button = tk.Button(button_frame, text="Save", command=self.save_image)
        self.save_all_button = tk.Button(button_frame, text="Save All", command=self.save_all_images)
        self.color_picker_button = tk.Button(button_frame, text="Pick Color", command=self.toggle_color_picker)
        self.upload_button.grid(row=0, column=0)
        self.process_button.grid(row=0, column=1)
        self.save_button.grid(row=0, column=2)
        self.save_all_button.grid(row=0, column=3)
        self.color_picker_button.grid(row=0, column=4)

        # Add a progress bar and label for image counter
        progress_frame = tk.Frame(self.root)
        self.progress_label = tk.Label(progress_frame, text="Image Progress: ")
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_label.grid(row=0, column=0)
        self.progress_bar.grid(row=0, column=1)

        # Create a label to display the picked color
        self.color_label = tk.Label(progress_frame, text="Picked Color: #000000")
        self.color_label.grid(row=0, column=2)

        # Pack the arrow_button_frame at the top, button_frame in the middle, and progress_frame at the bottom
        arrow_button_frame.pack(side="top")
        button_frame.pack(side="top", pady=5)
        progress_frame.pack(side="bottom", pady=5)

    def bind_events(self):
        self.root.bind("<MouseWheel>", self.zoom)
        self.root.bind("<ButtonPress-1>", self.start_drag)
        self.root.bind("<B1-Motion>", self.on_drag)

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.handle_drop)
        self.canvas.bind("<Button-1>", self.capture_color)

    def load_and_resize_arrow(self, image_path, size):
        img = Image.open(image_path)
        img = img.resize(size, Image.ANTIALIAS)
        img = ImageTk.PhotoImage(img)
        return img

    def upload_images(self):
        file_paths = filedialog.askopenfilenames(filetypes=[("Image Files", "*.png *.jpg *.jpeg *.gif *.bmp")])
        if file_paths:
            self.images = list(file_paths)
            self.current_image_index = 0
            self.show_current_image()

    def handle_drop(self, event):
        files = event.data
        files = files[1:-1]
        files = files.split('} {')
        if files:
            self.images = files
            self.current_image_index = 0
            self.show_current_image()

    def update_progress(self, current, total):
        self.progress_label.config(text=f"Image Progress: {current}/{total}")
        self.progress_bar["value"] = current * 100 / total
        self.root.update_idletasks()


    def show_current_image(self):
        if self.images:
            self.canvas.delete("all")
            image_path = self.images[self.current_image_index]
            self.current_image_path = image_path
            try:
                pil_image = Image.open(image_path)
                self.pil_image = pil_image
                self.pil_image = self.zoom_image(self.pil_image, self.zoom_factors[self.current_zoom_level])
                self.photo_image = ImageTk.PhotoImage(self.pil_image)

                x = (self.canvas_width - self.photo_image.width()) / 2
                y = (self.canvas_height - self.photo_image.height()) / 2

                self.image_obj_id = self.canvas.create_image(x, y, anchor="nw", image=self.photo_image)

                self.show_image_buttons()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {e}")

    def zoom_image(self, image, factor):
        width, height = image.size
        new_width = int(width * factor)
        new_height = int(height * factor)
        return image.resize((new_width, new_height), Image.ANTIALIAS)

    def zoom(self, event):
        if self.images:
            if event.delta > 0:
                self.current_zoom_level = min(self.current_zoom_level + 1, len(self.zoom_factors) - 1)
            else:
                self.current_zoom_level = max(self.current_zoom_level - 1, 0)
            self.show_current_image()

    def show_image_buttons(self):
        if not self.images:
            self.prev_image_button.config(state="disabled")
            self.next_image_button.config(state="disabled")
        elif self.current_image_index == 0:
            self.prev_image_button.config(state="disabled")
            self.next_image_button.config(state="active")
        elif self.current_image_index == len(self.images) - 1:
            self.prev_image_button.config(state="active")
            self.next_image_button.config(state="disabled")
        else:
            self.prev_image_button.config(state="active")
            self.next_image_button.config(state="active")

    def show_previous_image(self):
        if self.images:
            self.current_image_index = (self.current_image_index - 1) % len(self.images)
            self.current_zoom_level = 5
            self.show_current_image()

    def show_next_image(self):
        if self.images:
            self.current_image_index = (self.current_image_index + 1) % len(self.images)
            self.current_zoom_level = 5
            self.show_current_image()

    def start_drag(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def process_images(self):
        if not self.images:
            messagebox.showinfo("Info", "Please upload images before processing.")
            return

        # Check if the output directory exists and create it if necessary
        image_paths = self.images
        total_images = len(image_paths)
        
        # Disable the process button while processing
        self.process_button.config(state="disabled")
        
        # Start image processing in a separate thread
        processing_thread = threading.Thread(target=self.batch_remove_background, args=(image_paths, total_images))
        processing_thread.start()

    def show_processed_images(self):
        if self.processed_images:
            processed_image_paths = list(self.processed_images.keys())
            self.images = processed_image_paths
            self.current_image_index = 0
            self.show_current_image()
            self.show_image_buttons()
            self.save_button.config(state="active")
            print("Processed images loaded.")

    def remove_background(self, image_data):
        output_data = remove(image_data)
        return output_data

    def batch_remove_background(self, image_paths, total_images):
        self.processed_images = {}
        for i, image_path in enumerate(image_paths):
            try:
                with open(image_path, "rb") as image_file:
                    image_data = image_file.read()
                
                # Now, you have the image data, and you can process it as needed
                processed_data = self.remove_background(image_data)

                # Create a temporary file for the processed image
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as temp_file:
                    temp_file.write(processed_data)
                    processed_image_path = temp_file.name

                # Store the path of the temporary processed image
                self.processed_images[processed_image_path] = processed_image_path
                print(f"Processed and stored: {image_path}")

                # Update progress bar and image counter
                self.update_progress(i + 1, total_images)
            except Exception as e:
                print(f"Failed to process {image_path}: {e}")

        # Re-enable the process button after processing is complete
        self.process_button.config(state="active")
        self.show_processed_images()

    def save_image(self):
        if not self.current_image_path:
            messagebox.showinfo("Info", "No processed image to save.")
            return

        selected_file = filedialog.asksaveasfilename(defaultextension=".png", filetypes=[("PNG files", "*.png")])

        if selected_file:
            try:
                # Open the currently displayed image
                pil_image = Image.open(self.current_image_path)

                # You can save the opened image to the selected file
                pil_image.save(selected_file)

                messagebox.showinfo("Info", "Processed image saved successfully.")
            except Exception as e:
                messagebox.showerror("Error", f"Failed to save image: {e}")

    def save_all_images(self):
        if not self.processed_images:
            messagebox.showinfo("Info", "No processed images to save.")
            return

        output_directory = filedialog.askdirectory()

        if output_directory:
            for image_path in self.images:
                selected_file = os.path.join(output_directory, os.path.basename(image_path))
                try:
                    # Open the current image
                    pil_image = Image.open(image_path)

                    # Save the opened image to the selected file
                    pil_image.save(selected_file)
                except Exception as e:
                    messagebox.showerror("Error", f"Failed to save {os.path.basename(image_path)}: {e}")

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = BatchBackgroundRemoverApp(root)
    root.mainloop()