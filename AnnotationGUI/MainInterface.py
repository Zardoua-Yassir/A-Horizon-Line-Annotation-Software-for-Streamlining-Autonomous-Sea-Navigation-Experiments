import tkinter as tk
from tkinter import ttk
from tkinter import filedialog
from tkinter import messagebox
from PIL import ImageDraw
import numpy as np
import cv2 as cv
import os
from AnnotationGUI.CustomWidgets import ImageDisplay

class MainInterface(tk.Frame):
    def __init__(self, master):
        super().__init__(master)  # inherit attributes and methods of class widget
        # # # # # # # # # # # # # # # # # # # # #  Attributes of this class # # # # # # # # # # # # # # # # # # # # # # #
        # Non-classified attributes
        self.video_file_path = os.getcwd()  # directory or directories of the data source chosen by the user. It can be: dirs of PNG images, or dir of PNG, AVI or MAT file.
        self.gt_file_path = os.getcwd()
        self.frame_index = 0  # the index of the image to display or the current displayed image in the list self.src_img_files (Browsing status is: (self.frame_index+1)/self.frames_nbr)
        self.frames_nbr = 0  # the order of the current browsed image (Browsing status is: self.frame_index/self.frames_nbr)
        self.browsing_offset = 1
        self.gt_Y_alpha = None  # a numpy array that'll hold the gt annotations (Y,alpha)
        self.gt_xy_ends = None  # xy coordinates corresponding to horizon lines in self.gt_Y_alpha
        self.gt_Y_alpha_xy_ends = None
        self.gt_dir = os.getcwd()
        self.Y_hl = np.nan
        self.alpha_hl = np.nan

        self.frame_as_np = None  # frame read as numpy type
        self.frame_as_pil = None  # frame reas as PIL type
        self.video_reader = None  # a VideoCapture Object
        self.in_rects_inds = []  # contains indexes of in-frame edges' x,y coordinates of the i^th user-drawn rectangle (ROI)
        self.in_rects_inds_list = []  # a list of one or more lists. The i^th list contains indexes of in-frame edges' xy coordinates of the i^th user-drawn rectangle (ROI)

        # Flags attributes
        self.no_error_flag = None  # a boolean flag. If True, the frame self.frame_as_np is correctly read. False otherwise
        self.drawings_shown_flag = True  # a boolean flag. If True, user-defined drawings on the current original image are shown, False otherwise.
        # a flag to indicate which version of the image is currently shown on the display
        self.shown_version_flag = None  # one of 'org', 'jeong_edge_pixs', 'in_frame_edges_on_edge_map', 'in_frame_edges_on_org', 'in_rect_edges_on_org', 'collected_patches_pixs_on_org'
        self.shapes_shown_flag = False  # if True, drawn shapes are currently shown on the image display, False otherwise.
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # # # # # # # # # Creating MainInterface's Widgets # # # # # # # #
        self.frame1 = tk.Frame(master)  # a frame for the ImageDisplay object

        self.max_img_width = master.winfo_screenwidth() - 200  # master of ImageDisplay self: refers to an instance of MainInterface class
        self.max_img_height = master.winfo_screenheight() - 120
        self.img_display = ImageDisplay(master=self.frame1, wmax=self.max_img_width, hmax=self.max_img_height)

        self.frame2 = tk.Frame(master)  # a frame for remaining widgets (LabelFrames, buttons, etc)
        # Data Directories frame widgets (source and destination dirs)
        self.data_dirs_frame = tk.LabelFrame(self.frame2, text="Load directories")
        self.src_dir_button = ttk.Button(self.data_dirs_frame, text="Load video file", width=20)
        self.save_gt_button = ttk.Button(self.data_dirs_frame, text="Save annotated file", width=20)
        self.load_existing_gt_button = ttk.Button(self.data_dirs_frame, text="Load existing gt file", width=20)

        # Browse frame widgets
        self.browsing_frame = tk.LabelFrame(self.frame2, text="Browse")
        self.browsing_status = ttk.Label(self.browsing_frame,
                                         text=str(self.frame_index) + "/" + str(self.frames_nbr))
        self.back_button = ttk.Button(self.browsing_frame, text="<<", state="disabled", width=9)
        self.next_button = ttk.Button(self.browsing_frame, text=">>", state="disabled", width=9)
        self.browsing_offset_label = tk.Label(self.browsing_frame, text='Enter a browsing offset:')
        self.browsing_offset_entry = ttk.Entry(self.browsing_frame)

        # Annotation frame widgets
        # Collect patches frame widgets
        self.annotation_frame = tk.LabelFrame(self.frame2, text="Annotation")
        self.validate_annotation_button = ttk.Button(self.annotation_frame, text="Validate (v)", state="disabled", width=20)
        self.delete_annotation_button = ttk.Button(self.annotation_frame, text="Delete (d)", state="disabled", width=20)
        self.show_annotation_button = ttk.Button(self.annotation_frame, text="Show (s)", state="disabled", width=20)
        self.shown_hl_thickness_label = tk.Label(self.annotation_frame, text='Annotated line thickness:')
        self.shown_hl_thickness_entry = ttk.Entry(self.annotation_frame)
        self.shown_hl_thickness_entry.insert(index=0, string="2")
        self.hide_annotation_button = ttk.Button(self.annotation_frame, text="Hide (h)", state="disabled", width=20)
        text = "Current annotation:\n---------------------\nY = {} pixs\nAlpha = {} °".format("???", "???")
        self.current_annotation_label = tk.Label(self.annotation_frame, justify='left')
        self.current_annotation_label.config(text=text)

        # # # # # # # # # Geometry Management # # # # # # # #
        # NOTE on Sturcture of Geometry Management code section:
        # Geometry is managed from top-level to lower-level widgets (Not imperative, just for code readability)
        # Geometry of master window's Top-level widgets
        self.frame1.grid(row=0, column=0, padx=5, sticky='N')
        self.frame2.grid(row=0, column=1, sticky='N')

        # geometry of self.frame1 (attached to root window (master))
        self.img_display.grid(row=0, column=0, sticky='NW')
        # geometry of self.frame2 (attached to root window (master))
        pady = 10
        self.data_dirs_frame.grid(row=0, column=0, sticky='NW')
        self.browsing_frame.grid(row=1, column=0, sticky='NW', pady=pady)
        self.annotation_frame.grid(row=2, column=0, sticky='NW', pady=pady)

        # geometry of self.images_dirs_frame (attached to self.frame2)
        self.src_dir_button.grid(row=0, column=0)
        self.save_gt_button.grid(row=1, column=0)
        self.load_existing_gt_button.grid(row=2, column=0)

        # geometry of self.browsing_frame (attached to self.frame2)
        self.back_button.grid(row=0, column=0)
        self.next_button.grid(row=0, column=1)
        self.browsing_status.grid(row=1, column=0, columnspan=2)
        self.browsing_offset_label.grid(row=2, column=0, columnspan=2)
        self.browsing_offset_entry.grid(row=3, column=0, columnspan=2)

        # geometry of self.annotation_frame (attached to self.frame2)
        self.validate_annotation_button.grid(row=0, column=0, sticky="NW")
        self.delete_annotation_button.grid(row=1, column=0, sticky="NW")
        self.show_annotation_button.grid(row=2, column=0, sticky="NW")
        self.hide_annotation_button.grid(row=3, column=0, sticky="NW")
        self.shown_hl_thickness_label.grid(row=4, column=0, sticky="NW")
        self.shown_hl_thickness_entry.grid(row=5, column=0, sticky="NW")
        self.current_annotation_label.grid(row=6, column=0, sticky="NW")
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # # # # # # Binding custom events of ImageDisplay # # # # # # # # #
        self.img_display.bind_to("<New-Line>", self.new_line)
        self.img_display.bind_to("<New-Rect>", self.new_rect)
        self.img_display.bind_to("<New-Org-Img>", self.new_org_im)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # # # # # # Binding events of MainInterface class widgets # # # # # # # # #
        # # Note on execution flow:
        # even though the method set_img is called only once (when instanciating this class), it creates
        # events that watch over specific GUI actions and executes a code if this action occurs.
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # self.data_dirs_frame bound events
        self.src_dir_button.bind("<Button-1>", self.load_src_imgs)
        self.save_gt_button.bind("<Button-1>", self.set_gt_file)
        self.load_existing_gt_button.bind("<Button-1>", self.load_gt_file)

        # self.browsing_frame bound events
        self.next_button.bind("<Button-1>", self.browse_next)
        self.back_button.bind("<Button-1>", self.browse_back)
        self.master.bind("<MouseWheel>", self.browse_next, add='+')
        self.master.bind("<Right>", self.browse_next, add='+')
        self.master.bind("<MouseWheel>", self.browse_back, add='+')
        self.master.bind("<Left>", self.browse_back, add='+')

        self.browsing_offset_entry.bind("<Return>", self.set_offset)
        self.shown_hl_thickness_entry.bind("<Return>", self.set_hl_thickness)

        # self.annotation_frame bound events
        self.validate_annotation_button.bind("<Button-1>", self.validate_annotation)
        self.show_annotation_button.bind("<Button-1>", self.show_annotation)
        self.hide_annotation_button.bind("<Button-1>", self.hide_annotation)
        self.delete_annotation_button.bind("<Button-1>", self.delete_annotation)
        
        # self.master events
        self.master.bind("<KeyPress-v>", self.validate_annotation)
        self.master.bind("<Button-3>", self.validate_annotation)
        self.master.bind("<KeyPress-s>", self.show_annotation)
        self.master.bind("<KeyPress-h>", self.hide_annotation)
        self.master.bind("<KeyPress-d>", self.delete_annotation)
        self.master.bind("<KeyPress-w>", self.annotate_previous_with_current)


        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

        # # # # # # # # other things # # # # # # # # # # # # # # # #

        # # # # # # # # # # # # # # # # # # # #

    # # # # # # # # # # # Callbacks of ImageDisplay custom events # # # # # # # # # # # # # # #
    def new_line(self):
        self.shapes_shown_flag = True
        self.show_drawings()

    def new_rect(self):
        self.shapes_shown_flag = True
        self.show_drawings()

    def new_org_im(self):
        """
        This callback is triggered when when a new image is set as the original image (see self.img_display.im_as_pil_org).
        In this case, two actions are done:
            action1: the current edge map image self.edge_map and edge coordinates self.edges_xy  do not correspond to the
            new image. Thus, we set their attributes to None. This enable the program to recompute these attributes for the
            new image.

            action2: set the flag self.shown_version_flag to 'org', because the image currently shown is the original image
            (scaled if necessary to suit max dimensions specified by self.max_img_width and self.max_img_height)
        """
        # delete all image versions of the original image (e.g., edge map version, etc)
        self.edge_map = None
        self.edge_map_with_in_frame_edges = None
        self.edges_xy = None
        self.in_frame_edges_xy = None
        self.org_with_in_frame_edges = None

        # set flags
        self.shown_version_flag = 'org'
        self.drawings_shown_flag = 'False'

        # delete all drawings
        # self.delete_drawings()

    # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    # # # # # # # # # # # Callbacks of MainInterface events # # # # # # # # # # # # # # #
    def validate_annotation(self, event):
        """
        executes if the user validates the drawn horizon line as a gt annotation; two actions are taken: log parameters
        of annotated horizon into corresponding array and show the horizon with a thicker line.
        """
        self.Y_hl = self.img_display.Y_hl
        self.alpha_hl = self.img_display.alpha_hl
        self.hl_xs = self.img_display.hl_x_s_org
        self.hl_ys = self.img_display.hl_y_s_org
        self.hl_xe = self.img_display.hl_x_e_org
        self.hl_ye = self.img_display.hl_y_e_org

        self.gt_Y_alpha[self.frame_index] = [self.Y_hl, self.alpha_hl]
        self.gt_xy_ends[self.frame_index] = [self.hl_xs, self.hl_ys, self.hl_xe, self.hl_ye]

        self.show_current_annotation()

    def show_annotation(self, event):
        self.show_current_annotation()

    def hide_annotation(self, event):
        self.img_display.show_img(src=np.copy(self.frame_as_np), src_type='numpy', set_as_org=False)

    def delete_annotation(self, event):
        self.gt_xy_ends[self.frame_index] = np.array([0, 0, 0, 0], dtype=np.int32)
        self.gt_Y_alpha[self.frame_index] = np.array([np.nan, np.nan], dtype=np.float32)
        self.show_current_annotation()

    def annotate_previous_with_current(self, event):
        """
        Annotate all previous non-annotated frames with annotation on current frame.
        """
        if self.Y_hl is not np.nan:
            self.all_non_annotated_frames_indexes = np.argwhere(np.isnan(self.gt_Y_alpha[:, 0]))
            self.previous_non_annotated_frames_indexes \
                = self.all_non_annotated_frames_indexes[np.where(self.all_non_annotated_frames_indexes < self.frame_index)]

            self.gt_Y_alpha[self.previous_non_annotated_frames_indexes, 0] = self.Y_hl
            self.gt_Y_alpha[self.previous_non_annotated_frames_indexes, 1] = self.alpha_hl
            self.gt_xy_ends[self.previous_non_annotated_frames_indexes, 0] = self.hl_xs
            self.gt_xy_ends[self.previous_non_annotated_frames_indexes, 1] = self.hl_ys
            self.gt_xy_ends[self.previous_non_annotated_frames_indexes, 2] = self.hl_xe
            self.gt_xy_ends[self.previous_non_annotated_frames_indexes, 3] = self.hl_ye
        else:
            print("validate annotation first")
    # # # # #

    def load_src_imgs(self, event):
        """
        * loads and display the selected video file.
        * creates the array self.gt_Y_alpha with shape = (self.frames_nbr, 2), where self.frames_nbr is the number
        of frames in the selected video file.
        """
        title = "Choose a directory"
        filetypes = (("AVI files", "*.avi"), ("MP4 files", "*.mp4"))
        # data_src_files_dir = tk.filedialog.askopenfilename(initialdir=os.path.dirname(self.video_file_path),
        #                                                    title=title,
        #                                                    filetypes=filetypes)
        idir = r"D:\My Data\All_Maritime_Datasets\CORRECTED SMD\Onshore\Videos"
        data_src_files_dir = tk.filedialog.askopenfilename(initialdir=idir,
                                                           title=title,
                                                           filetypes=filetypes)
        if os.path.exists(data_src_files_dir):
            self.video_file_path = os.path.normpath(data_src_files_dir)
            self.video_reader = cv.VideoCapture(self.video_file_path)
            self.no_error_flag, self.frame_as_np = self.video_reader.read()
            if self.no_error_flag:
                self.img_display.show_img(src=self.frame_as_np, src_type='numpy', set_as_org=True)
                self.frames_nbr = int(self.video_reader.get(cv.CAP_PROP_FRAME_COUNT))
                self.frame_index = 0
                self.browsing_status.config(text=str(self.frame_index + 1) + "/" + str(self.frames_nbr))
                if self.frames_nbr > 1:
                    self.next_button.config(state="normal")
                self.gt_Y_alpha = np.zeros(shape=(self.frames_nbr, 2), dtype=np.float32)
                self.gt_Y_alpha[:] = np.nan  # all non-annotated frames correspond to nan values.
                self.gt_xy_ends = np.zeros(shape=(self.frames_nbr, 4), dtype=np.int32)  # 4 for: xs, ys, xe, ye
                self.validate_annotation_button.config(state='enable')
                self.delete_annotation_button.config(state='enable')
                self.show_annotation_button.config(state='enable')
                self.hide_annotation_button.config(state='enable')

    def set_gt_file(self, event):
        title = "Choose the directory where to save the gt annotation file"
        idir = r"D:\My Data\All_Maritime_Datasets\CORRECTED SMD\Onshore\HorizonGT"
        gt_dir = tk.filedialog.askdirectory(initialdir=idir, title=title)
        # gt_dir = tk.filedialog.askdirectory(initialdir=self.gt_dir, title=title)
        # gt_dir = tk.filedialog.askopenfilename(initialdir=self.gt_dir, title=title)
        if os.path.exists(gt_dir):
            self.gt_dir = os.path.normpath(gt_dir)
            self.save_gt_file_helper()

    def save_gt_file_helper(self):
        self.video_file_name_no_ext = os.path.basename(self.video_file_path).split(".")[0]
        self.gt_filename = self.video_file_name_no_ext + "_LineGT.npy"
        self.gt_abs_path = os.path.join(self.gt_dir, self.gt_filename)
        nan_indexes = np.where(np.isnan(self.gt_Y_alpha))
        if nan_indexes[0].size == 0:  # True if there is no np.nan in the array self.gt_Y_alpha <==> all frames have
            # been annotated
            message_text = "All frames are annotated.\n Confirm the saving at {}".format(self.gt_abs_path)
            option = tk.messagebox.askokcancel(title="COMPLETE ANNOTATION", message=message_text)
            if option:
                self.gt_Y_alpha_xy_ends = np.zeros(shape=(self.frames_nbr, 6), dtype=np.float32)
                self.gt_Y_alpha_xy_ends[:] = np.nan  # all non-annotated frames correspond to nan values.
                self.gt_Y_alpha_xy_ends[:, 0:2] = self.gt_Y_alpha
                self.gt_Y_alpha_xy_ends[:, 2::] = self.gt_xy_ends
                np.save(self.gt_abs_path, self.gt_Y_alpha_xy_ends)
        else:
            message_text = "You did not annotate all the frames.\n" \
                           "Frames with no annotation will correspond to Y = np.nan and alpha = np.nan\n" \
                           "Do you still want to save the gt file?"
            option = tk.messagebox.askokcancel(title="WARNING: INCOMPLETE ANNOTATION", message=message_text)
            if option:
                # np.save(self.gt_abs_path, self.gt_Y_alpha)
                self.gt_Y_alpha_xy_ends = np.zeros(shape=(self.frames_nbr, 6), dtype=np.float32)
                self.gt_Y_alpha_xy_ends[:] = np.nan  # all non-annotated frames correspond to nan values.
                self.gt_Y_alpha_xy_ends[:, 0:2] = self.gt_Y_alpha
                self.gt_Y_alpha_xy_ends[:, 2::] = self.gt_xy_ends
                np.save(self.gt_abs_path, self.gt_Y_alpha_xy_ends)

    def load_gt_file(self, event):
        title = "Choose an npy file to modify"
        filetypes = (("npy file", "*.npy"),)
        idir = r"D:\My Data\All_Maritime_Datasets\CORRECTED SMD\Onshore\HorizonGT"
        data_src_files_dir = tk.filedialog.askopenfilename(initialdir=idir,
                                                           title=title,
                                                           filetypes=filetypes)
        # data_src_files_dir = tk.filedialog.askopenfilename(initialdir=os.path.dirname(self.gt_file_path),
        #                                                    title=title,
        #                                                    filetypes=filetypes)
        if os.path.exists(data_src_files_dir):
            self.gt_file_path = os.path.normpath(data_src_files_dir)
            self.gt_Y_alpha_xy_ends = np.load(self.gt_file_path)
            self.gt_Y_alpha = self.gt_Y_alpha_xy_ends[:, 0:2]
            self.gt_xy_ends = self.gt_Y_alpha_xy_ends[:, 2::]

    def browse_next(self, event):
        event_type = str(event.type)
        if (event_type == 'ButtonPress' or event_type == 'KeyPress') or (
                event_type == 'MouseWheel' and event.delta > 0):
            self.Y_hl = np.nan
            self.alpha_hl = np.nan
            # increment the index of the image or frame to read and display
            self.frame_index = min(self.frame_index + self.browsing_offset,
                                   self.frames_nbr - 1)  # Example to understand why min() is used: if (self.frame_index + self.browsing_offset) = 130 and the total # of frames (or images) = 100, self.frame_index gets updated to 100 - 1 = 99 (because the index starts from 0)
            self.video_reader.set(cv.CAP_PROP_POS_FRAMES, self.frame_index)
            self.no_error_flag, self.frame_as_np = self.video_reader.read()
            if self.no_error_flag:
                self.img_display.show_img(src=self.frame_as_np, src_type='numpy', set_as_org=True)
                self.browsing_status.config(
                    text=str(self.frame_index + 1) + "/" + str(self.frames_nbr))
                self.back_button.config(state='normal')
                if self.frame_index + 1 == self.frames_nbr:
                    self.next_button.config(state='disabled')
                self.show_current_annotation()

    def browse_back(self, event):
        event_type = str(event.type)
        if (event_type == 'ButtonPress' or event_type == 'KeyPress') or (
                event_type == 'MouseWheel' and event.delta < 0):
            self.Y_hl = np.nan
            self.alpha_hl = np.nan
            self.frame_index = max(self.frame_index - self.browsing_offset,
                                   0)  # decrement the index. Example to understand why max() is used: if (self.frame_index - self.browsing_offset) = -3, self.frame_index gets updated to 0
            self.video_reader.set(cv.CAP_PROP_POS_FRAMES, self.frame_index)
            self.no_error_flag, self.frame_as_np = self.video_reader.read()
            if self.no_error_flag:
                self.img_display.show_img(src=self.frame_as_np, src_type='numpy', set_as_org=True)
                self.browsing_status.config(
                    text=str(self.frame_index + 1) + "/" + str(self.frames_nbr))
                self.next_button.config(state='normal')
                if self.frame_index == 0:
                    self.back_button.config(state='disabled')
                self.show_current_annotation()

    def show_current_annotation(self):
        self.hl_xs, self.hl_ys, self.hl_xe, self.hl_ye = self.gt_xy_ends[self.frame_index]
        Y, alpha = np.round(self.gt_Y_alpha[self.frame_index], 2)
        # print(Y, alpha)
        self.line_thickness = self.shown_hl_thickness_entry.get()
        self.line_thickness = min(max(int(self.line_thickness), 1), 10)
        if not isinstance(self.line_thickness, int):
            self.line_thickness = 5
        self.shown_hl_thickness_entry.delete(0, "end")
        self.shown_hl_thickness_entry.insert(index=0, string=str(self.line_thickness))
        if not np.isnan(Y) and not np.isnan(Y):
            text = "Current annotation:\n---------------------\nY = {} pixs\nAlpha = {} °".format(str(Y), str(alpha))
            self.current_annotation_label.config(text=text)
            self.img_with_annotated_hl = np.copy(self.frame_as_np)
            cv.line(self.img_with_annotated_hl, (self.hl_xs, self.hl_ys), (self.hl_xe, self.hl_ye), (0, 0, 255), self.line_thickness)
            self.img_display.show_img(src=self.img_with_annotated_hl, src_type='numpy', set_as_org=False)
        else:
            text = "Current annotation:\n---------------------\nY = {} pixs\nAlpha = {} °".format("???", "???")
            self.current_annotation_label.config(text=text)
            # print("showing and writing original img")
            # cv.imwrite("frame_as_np.png", np.copy(self.frame_as_np))
            self.img_display.show_img(src=np.copy(self.frame_as_np), src_type='numpy', set_as_org=True)

    def set_offset(self, event):
        try:
            offset_str = self.browsing_offset_entry.get()
            self.browsing_offset = max(int(offset_str), 1)  # this enables getting an offset = 0 or smaller.
            self.master.focus()
        except:
            tk.messagebox.showwarning("Warning", message="Invalid browsing offset. It must be positive integer")

    def set_hl_thickness(self, event):
        temp_text = self.shown_hl_thickness_entry.get()
        try:
            temp_text = int(temp_text)
        except:
            temp_text = 5
        self.shown_hl_thickness_entry.delete(0, "end")
        self.shown_hl_thickness_entry.insert(index=0, string=temp_text)
        self.img_display.focus()

    def log_gt_sample(self, event):
        """
        logging parameters Y, alpha of drawn line as a gt horizon
        :param event:
        :return:
        """
        pass

    def show_drawings(self, event=None):
        """
        This method shows non-deleted and non-canceled user-defined shapes. These drawings may be shown on the original
        image (after rescaling it to suite the image display) or on the edge map image. This decision is made thanks to
        the flag self.shown_version_flag.
        """
        if self.img_display.all_lines_scaled != []:
            self.img_display.show_img(src=self.img_display.im_as_pil_org.copy(), src_type='pil', set_as_org=False)
            drawer = ImageDraw.Draw(self.img_display.cur_shown)
            for line in self.img_display.all_lines_scaled:
                drawer.line(xy=line, fill=128, width=1)
            self.img_display.show_img(src=self.img_display.cur_shown, src_type='pil', set_as_org=False)
            self.img_display.cur_with_valid_drawings = self.img_display.cur_shown.copy()
            self.shapes_shown_flag = True

  # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
