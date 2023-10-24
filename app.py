from tkinter import Tk, Canvas, Button, filedialog, messagebox, simpledialog
from tkinterdnd2 import DND_FILES, TkinterDnD
from PIL import Image, ImageTk
import os
from rembg_processor import batch_remove_background, processed_images

class BatchBackgroundRemoverApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Batch Background Remover")
        self.images = []
        self.current_image_index = 0
        self.arrow_images = {
            "left": self.load_and_resize_arrow("Arrows-Back.512.png", (24, 24)),
            "right": self.load_and_resize_arrow("Arrows-Forward.512.png", (24, 24))
        }

        self.canvas_width = 800
        self.canvas_height = 600
        self.pil_image = None
        self.photo_image = None
        self.image_obj_id = None
        self.zoom_factor = 1.0
        self.original_pil_image = None

        self.canvas = Canvas(self.root, width=self.canvas_width, height=self.canvas_height)
        self.canvas.pack(fill="both", expand=True)
        self.canvas.bind("<Configure>", self.on_canvas_resize)
        self.canvas.bind("<MouseWheel>", self.zoom)
        self.canvas.bind("<ButtonPress-1>", self.start_drag)
        self.canvas.bind("<B1-Motion>", self.on_drag)
        self.canvas.bind("<ButtonRelease-1>", self.end_drag)

        self.upload_button = Button(self.root, text="Upload Images", command=self.upload_images)
        self.process_button = Button(self.root, text="Process Images", command=self.process_images)
        self.show_processed_button = Button(self.root, text="Show Processed Images", command=self.show_processed_images)
        self.prev_image_button = Button(self.root, image=self.arrow_images["left"], command=self.show_previous_image)
        self.next_image_button = Button(self.root, image=self.arrow_images["right"], command=self.show_next_image)
        self.output_directory = None

        self.upload_button.pack()
        self.process_button.pack()
        self.show_processed_button.pack()
        self.prev_image_button.pack(side="left")
        self.next_image_button.pack(side="right")

        self.show_image_buttons()

        self.canvas.drop_target_register(DND_FILES)
        self.canvas.dnd_bind('<<Drop>>', self.handle_drop)

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

    def show_current_image(self):
        if self.images:
            self.canvas.delete("all")
            image_path = self.images[self.current_image_index]
            try:
                pil_image = Image.open(image_path)
                self.original_pil_image = pil_image.copy()
                self.pil_image = pil_image
                self.pil_image = self.zoom_image(self.pil_image, self.zoom_factor)
                self.photo_image = ImageTk.PhotoImage(self.pil_image)

                x = (self.canvas.winfo_width() - self.photo_image.width()) / 2
                y = (self.canvas.winfo_height() - self.photo_image.height()) / 2

                self.image_obj_id = self.canvas.create_image(x, y, anchor="nw", image=self.photo_image)

                self.show_image_buttons()
            except Exception as e:
                messagebox.showerror("Error", f"Failed to open image: {e}")

    def on_canvas_resize(self, event):
        self.show_current_image()

    def zoom_image(self, image, factor):
        width, height = image.size
        new_width = int(width * factor)
        new_height = int(height * factor)
        return image.resize((new_width, new_height), Image.ANTIALIAS)

    def zoom(self, event):
        if self.pil_image:
            factor = 1.2 if event.delta > 0 else 0.8

            # Limit the zoom to a minimum and maximum scale
            self.zoom_factor *= factor
            if self.zoom_factor < 0.1:
                self.zoom_factor = 0.1
            if self.zoom_factor > 5.0:
                self.zoom_factor = 5.0

            self.pil_image = self.zoom_image(self.original_pil_image.copy(), self.zoom_factor)
            x = (self.canvas.winfo_width() - self.pil_image.width) / 2
            y = (self.canvas.winfo_height() - self.pil_image.height) / 2

            self.canvas.delete(self.image_obj_id)
            self.photo_image = ImageTk.PhotoImage(self.pil_image)
            self.image_obj_id = self.canvas.create_image(x, y, anchor="nw", image=self.photo_image)

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
            self.show_current_image()

    def show_next_image(self):
        if self.images:
            self.current_image_index = (self.current_image_index + 1) % len(self.images)
            self.show_current_image()

    def start_drag(self, event):
        self.canvas.scan_mark(event.x, event.y)

    def on_drag(self, event):
        self.canvas.scan_dragto(event.x, event.y, gain=1)

    def end_drag(self, event):
        pass  # No need to do anything here

    def process_images(self):
        if not self.images:
            messagebox.showinfo("Info", "Please upload images before processing.")
            return
        self.output_directory = filedialog.askdirectory(title="Select Output Directory")
        if not self.output_directory:
            messagebox.showinfo("Info", "Processing canceled. No output directory specified.")
            return

        # Check if the output directory exists and create it if necessary
        if not os.path.exists(self.output_directory):
            os.makedirs(self.output_directory)

        if len(self.images) > 1:
            # Clear the processed images list
            processed_images.clear()

            for image_path in self.images:
                with open(image_path, 'rb') as image_file:
                    image_data = image_file.read()
                    batch_remove_background(image_data, self.output_directory)

            messagebox.showinfo("Info", "Images processed and saved to the specified directory.")
            self.show_processed_images()
            processed_images.clear()
        else:
            image_path = self.images[0]
            with open(image_path, 'rb') as image_file:
                image_data = image_file.read()
                batch_remove_background(image_data, self.output_directory)

            messagebox.showinfo("Info", "Image processed and saved to the specified directory.")
            self.show_processed_images()
            processed_images.clear()

    def show_processed_images(self):
        if processed_images:
            self.images = processed_images.copy()
            self.current_image_index = 0
            self.show_current_image()
            self.show_image_buttons()

if __name__ == "__main__":
    root = TkinterDnD.Tk()
    app = BatchBackgroundRemoverApp(root)
    root.mainloop()