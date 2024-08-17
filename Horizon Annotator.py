import AnnotationGUI.MainInterface as AppGUI
import tkinter as tk
import os
if __name__ == '__main__':
    root = tk.Tk()

    # root.attributes('-fullscreen', True)  # make window full screen (no bar title)
    root.state('zoomed')  # maximize the window
    venvp= os.path.join(os.getcwd(), "venv")
    imgp = os.path.join(venvp, "icone.png")
    print(imgp)
    icone = tk.PhotoImage(file=imgp)
    root.iconphoto(False, icone)
    root.title("Horizon Annotator")
    # A hard way to maximize the window
    # screen_height_resolution = root.winfo_screenheight()
    # screen_width_resolution = root.winfo_screenwidth()
    # root.geometry(str(screen_width_resolution)+"x"+str(screen_height_resolution)+"+0+0")
    mainApp = AppGUI.MainInterface(master=root)
    mainApp.grid(row=0, column=0)
    # root.bind("<ButtonPress>", callback)
    # for thread in threading.enumerate(): print(thread.name)
    # mainApp.temporary_load()
    root.mainloop()
