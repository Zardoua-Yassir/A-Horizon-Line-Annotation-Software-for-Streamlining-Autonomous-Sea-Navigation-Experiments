import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk, ImageDraw
import numpy as np
from AnnotationGUI import CustomWidgetsHelpers as cls_h
import cv2 as cv
from warnings import warn
from math import pi, atan


class ImageDisplay(tk.Frame):
    # a dictionary of callbacks.
    # keys correspond to the type of event, values are lists to be appended by callback functions.
    _callbacks = {"<New-Line>": [], "<New-Rect>": [], "<New-Org-Img>": []}

    def __init__(self, master, hmax, wmax, name='Image Display'):
        super().__init__(master)  # inherit attributes and methods of class widget

        # Defining attributes related to images:
        self.hmax = hmax  # maximum height allowed (in pixels) of the image to display
        self.wmax = wmax  # maximum width allowed (in pixels) of the image to display
        self.w_scaled = None  # the scaled width of the displayed image
        self.h_scaled = None  # the scaled height of the displayed image
        self.cur_with_valid_drawings = None  # same as self.cur_shown overlaid with validated (i.e., non-canceled) drawings
        self.cur_shown = None  # the PIL image that appears on the ImageDisplay NOW
        self.im_as_pil_org = None  # the last original (i.e., no pre-processing) image loaded, as a PIL image
        self.drawings_layer = None
        self.Y_hl = -1
        self.alpha_hl = -1

        # Creating a tkinter image "image_as_tk" that can be displayed on a Label widget
        self.im_as_np_org = None  # original numpy version of the image being displayed. If the displayed image is colored, this attribute is a BGR image.
        self.im_as_np_org = np.multiply(np.ones((self.hmax, self.wmax), dtype=np.uint8), 100)  # initilize to a gray image
        self.im_as_pil = Image.fromarray(self.im_as_np_org)
        self.im_as_tk = ImageTk.PhotoImage(self.im_as_pil)

        self.frame = tk.LabelFrame(master=master, text=name)  # master is the master of the custom widget ImageDisplay
        self.imagelabel = tk.Label(self.frame, image=self.im_as_tk)
        self.imagelabel.grid(row=0, column=0)

        # # # # # # # Creating configuring elements/sub-widgets of ImageDisplay as its attributes # # # # # # # # #
        self.coord_label = tk.Label(self.frame,
                                    text="Current position (x,y): Load an image/images and hover the mouse on")
        self.dr_options_frame = tk.Frame(master=self.frame)  # frame holding drawing options
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        self._dr_opt = tk.IntVar()  # drawing option dr_opt, a variable bound to radio buttons choosing the drawing mode
        self._dr_opt.set(0)
        self.line_option = ttk.Radiobutton(master=self.dr_options_frame, text="╲", variable=self._dr_opt,
                                           value=0)  # a chackbutton to choose to draw lines

        # configuring elements/sub-widgets of ImageDisplay as its attributes.

        # # # # # # # # # # # Configuring geometry of ImageDisplay widgets # # # # # # # # # # # # # # # # # # # #
        # geometry inside self.cb_frame
        self.line_option.grid(row=0, column=0, sticky='N')
        # geometry inside self.frame
        self.imagelabel.grid(row=0, column=0)
        self.coord_label.grid(row=1, column=0, sticky='W')
        self.dr_options_frame.grid(row=0, column=1, sticky='N')

        self.frame.grid(row=0, column=0)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        self.cur_org_x = 0  # x coordinate of the current mouse position on the original image (before rescaling)
        self.cur_org_y = 0  # y coordinate of the current mouse position on the original image (before rescaling)

        # Attributes related to drawn shapes # # # # # # # # # # # # # # # # # #
        self.sh_x_s_scaled = 0  # scaled x coordinate of the shape's starting point
        self.sh_y_s_scaled = 0  # scaled y coordinate of the shape's starting point
        self.sh_x_e_scaled = 0  # scaled x coordinate of the shape's end point
        self.sh_y_e_scaled = 0  # scaled y coordinate of the shape's end point
        self.sh_ends_scaled = [self.sh_x_s_scaled, self.sh_y_s_scaled, self.sh_x_e_scaled, self.sh_y_e_scaled]  # a list of currently drawn or last drawn shape end points
        self.all_rects_scaled = []
        self.all_lines_scaled = []
        # NOTE: the below two attributes exclude drawn shapes canceled by the user (by right-clicking the mouse)
        self.sh_x_s_org = 0  # original x coordinate of the shape's starting point
        self.sh_y_s_org = 0  # original scaled y coordinate of the shape's starting point
        self.sh_x_e_org = 0  # original x coordinate of the shape's end point
        self.sh_y_e_org = 0  # original y coordinate of the shape's end point
        self.sh_ends_org = [self.sh_x_s_org, self.sh_y_s_org, self.sh_x_e_org, self.sh_y_e_org]  # a list of currently drawn or last drawn shape end points
        self.all_lines_org = []  # end points of all drawn lines. This attribute is set to empty list if the original image is changed (by loading, or browsing to, another image)
        self.all_rects_org = []  # end points of all drawn rectangles. This attribute is set to empty list if the original image is changed (by loading, or browsing to, another image)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #
        # Flags
        self.in_drawing = False  # Set to True while the user is drawing. Set to False after end of drawing.
        self.drawing_canceled = False  # Set to True if the user cancels current shape being drawn (by right clicking the mouse)
        self.drawings_shown = True  # if True, all user-drawn shape are overlaid on the displayed image
        # Attributes of image parameters
        self.org_w = None  # original width of the image being displayed
        self.org_h = None  # original height of the image being displayed

    def bind_to(self, event_id, callback):
        """
        binds callback functions to specific events.
        :param event_id: identified or type of the event. Possible values are: "<New-Line>", "<type2event>".
        :param callback: a function to be executed if the event 'event_id' takes place
        :return:
        """
        # if there is no callback named 'callback' function bound to the event named 'event_id', bind 'callback' to 'event_id'
        if callback not in self._callbacks[event_id]:
            self._callbacks[event_id].append(callback)

    def show_img(self, src, src_type, set_as_org=True, bgr2rgb=True):
        """
        show the image taken from the source src on the image display
        :param src: the source of the image. Posible options are: PIL image, Numpy image, path of the image
        :param src_type: a string indicating the type (option) of src. src_type is one of the following: 'pil', 'numpy' or 'path'
        :param set_as_org: if True, src is used to update the attributes self.im_as_pil_org and self.im_as_np_org
        :param bgr2rgb: if True and src is a nummpy image (src_type = 'numpy'), src is converted from BGR to RGB.
        :return: None
        """
        opened = None
        src_org_copy = src  # src may be changed. Thus, we save an original copy in src_org_copy
        w_s = 0
        h_s = 0
        src_rgb_pil = 0
        self.imagelabel.grid_forget()  # delete previous image label
        if src_type == 'pil':
            self.cur_shown, w_s, h_s = cls_h.check_img_size(im_as_pil=src,
                                                            wmax=self.wmax,
                                                            hmax=self.hmax)
        elif src_type == 'numpy':
            if bgr2rgb:
                if cls_h.is_gray(src):
                    warn("argument bgr2rgb is set to True, yet the argument src has only one channel")
                else:
                    src = cv.cvtColor(src, cv.COLOR_RGB2BGR)
            self.cur_shown, w_s, h_s = cls_h.check_img_size(im_as_pil=Image.fromarray(src),
                                                            wmax=self.wmax,
                                                            hmax=self.hmax)

        elif src_type == 'path':
            opened = Image.open(src)
            self.cur_shown, w_s, h_s = cls_h.check_img_size(im_as_pil=opened,
                                                            wmax=self.wmax,
                                                            hmax=self.hmax)
        else:
            raise ValueError("Unkown specifier for src_type: must be a string containing 'numpy', 'pil' or 'path'")

        if len(self.cur_shown.mode) == 1:  # True if the src image, currently stored in self.cur_shown.mode has one band (i.e., channel)
            # making sure the mode of self.cur_show is 'L'. This is necessary for merging into 'RGB' mode
            self.cur_shown = self.cur_shown.convert('L')
            # merge the single banded self.cur_shown into an image with 'RGB' mode. Merged images must have 'L' mode.
            self.cur_shown = Image.merge("RGB", (self.cur_shown, self.cur_shown, self.cur_shown))

        self.im_as_tk = ImageTk.PhotoImage(self.cur_shown)
        self.imagelabel = tk.Label(self.frame, image=self.im_as_tk)
        self.imagelabel.grid(row=0, column=0)

        if set_as_org:
            for New_Org_Img_callback in self._callbacks["<New-Org-Img>"]:  # execute callback(s) corresponding to setting src as an original image
                New_Org_Img_callback()
            if src_type == 'numpy':
                self.im_as_np_org = src_org_copy
                self.im_as_pil_org = Image.fromarray(src)
            elif src_type == 'pil':
                self.im_as_pil_org = src
                self.im_as_np_org = np.asarray(self.im_as_pil_org)
            elif src_type == 'path':
                self.im_as_pil_org = opened
                self.im_as_np_org = np.asarray(self.im_as_pil_org)
                if not cls_h.is_gray(self.im_as_np_org):  # True if the image is colored, it must be an RGB (because the pil version is 'RGB').
                    self.im_as_np_org = cv.cvtColor(self.im_as_np_org, cv.COLOR_RGB2BGR)  # convert from RGB to BGR
            else:
                raise ValueError("Unkown specifier for src_type: must be a string containing 'numpy', 'pil' or 'path'")
            self.org_w, self.org_h = self.im_as_pil_org.size
            self.cur_with_valid_drawings = self.cur_shown.copy()  # the image containing previous non-canceled drawings is set to the original image shown on the Image Display
            self.w_scaled = w_s
            self.h_scaled = h_s

            # when a new image is displayed (not processed ones) and set as original, delete all shapes' ends coordinates (because they no longer correspond to the displayed image)
            self.all_rects_scaled = []
            self.all_lines_scaled = []
            self.all_rects_org = []
            self.all_lines_org = []

        # # # # # # # # # # # # # # # # Binding events on the new self.imagelabel # # # # # # # # # # # # # # # # # # #
        self.imagelabel.bind("<Motion>", self._show_xy_coords)
        self.imagelabel.bind("<Button-1>", self._draw_shapes)
        self.imagelabel.bind("<Motion>", self._draw_shapes, add="+")
        self.imagelabel.bind("<ButtonRelease>", self._draw_shapes)
        self.imagelabel.bind("<Button-3>", self._draw_shapes)
        # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # # #

    def _show_xy_coords(self, event):
        # #Scaling the coordinates if the displayed image has been rescaled
        # self.org_w, self.org_h = self.im_as_pil_org.size
        # if self.w_scaled != 1 and self.h_scaled != 1:  # True if the image has been scaled
        #     x = int((event.x) * (self.org_w / self.w_scaled))
        #     y = int((event.y) * (self.org_h / self.h_scaled))
        # else:  # Executed if the image isn't scaled
        #     x = event.x
        #     y = event.y

        x, y = cls_h.rescale_to_org_xy(event.x, event.y, self.org_w, self.org_h, self.w_scaled, self.h_scaled)

        x, y = cls_h.compensate_xy_padding(x, y, self.org_w, self.org_h)

        self.cur_org_x = x
        self.cur_org_y = y

        # update the text label displaying the coordinates of the current mouse
        self.coord_label.config(text="Current position (x,y): " + "(" + str(x) + "," + str(y) + ")              ")

    def _draw_shapes(self, event):
        """
        This method applies user-drawn shapes on the class attribute self.cur_with_valid_drawings
        :param event: a Tkinter event object that's passed automatically by the binding method
        :return: None
        """
        # draw a line on A COPY of the original image
        # display it using set_img

        if str(
                event.type) == "ButtonPress" and event.num == 1:  # True if left mouse button is clicked <=> drawing has been started
            self.sh_x_s_scaled, self.sh_y_s_scaled = cls_h.compensate_xy_padding(event.x, event.y, self.w_scaled,
                                                                                 self.h_scaled)  # self.w_scaled and self.h_scaled because the coordinates correspond to the scaled image
            self.sh_x_s_org, self.sh_y_s_org = self.cur_org_x, self.cur_org_y
            self.in_drawing = True  # drawing has been started
            self.drawing_canceled = False  # False because a the user started a new drawing

        if str(
                event.type) == "ButtonPress" and event.num == 3:  # True if right mouse button is clicked <=> current drawing has been canceled
            self.drawing_canceled = True
            self.in_drawing = False  # the user has finished the drawing
            self.show_img(src=self.cur_with_valid_drawings, src_type='pil',
                          set_as_org=False)  # immediatly display previous drawings, which has the effect to remove canceled drawing

        if str(event.type) == "ButtonRelease":
            self.in_drawing = False  # False means drawing has been finished
            if not self.drawing_canceled:  # True if the finished drawing (i.e., drawing of the last line) hasn't been canceled


                self.sh_x_e_scaled, self.sh_y_e_scaled = cls_h.compensate_xy_padding(event.x, event.y, self.w_scaled, self.h_scaled)
                self.sh_ends_scaled = [self.sh_x_s_scaled, self.sh_y_s_scaled, self.sh_x_e_scaled, self.sh_y_e_scaled]
                self.sh_x_e_org, self.sh_y_e_org = self.cur_org_x, self.cur_org_y
                self.sh_ends_org = [self.sh_x_s_org, self.sh_y_s_org, self.sh_x_e_org, self.sh_y_e_org]

                self.all_lines_scaled = [self.sh_ends_scaled]  # Note: removed .append method because I'm interested in drawing only one line (the horizon)
                self.all_lines_org = [self.sh_ends_org]
                for New_Line_callback in self._callbacks["<New-Line>"]:  # execute callback(s) corresponding to drawing a new line
                    New_Line_callback()

                # we are interested in drawing the line on the entire image
                self.get_horizon_coordinates()
                shape_drawer = ImageDraw.Draw(self.cur_shown)
                shape_drawer.line((self.hl_x_s_scaled,
                                   self.hl_y_s_scaled,
                                   self.hl_x_e_scaled,
                                   self.hl_y_e_scaled),
                                  fill=128,
                                  width=3)
                self.show_img(src=self.cur_shown, src_type='pil', set_as_org=False)
                self.cur_with_valid_drawings = self.cur_shown.copy()  # draw the last line
                del shape_drawer

        if self.in_drawing:
            self.cur_shown = self.cur_with_valid_drawings.copy()
            shape_drawer = ImageDraw.Draw(self.cur_shown)
            self.sh_x_e_scaled, self.sh_y_e_scaled = cls_h.compensate_xy_padding(event.x, event.y, self.w_scaled,
                                                                                 self.h_scaled)  # self.w_scaled and self.h_scaled because the coordinates correspond to the scaled image
            if not ((self.sh_x_s_scaled == self.sh_x_e_scaled) and (
                    self.sh_y_s_scaled == self.sh_y_e_scaled)):  # Drawing is done only if starting and end points of shape are not the same

                shape_drawer.line((self.sh_x_s_scaled,
                                   self.sh_y_s_scaled,
                                   self.sh_x_e_scaled,
                                   self.sh_y_e_scaled),
                                  fill=128,
                                  width=1)

                self.show_img(src=self.cur_shown, src_type='pil', set_as_org=False)
                del shape_drawer

    def get_last_line_pixs(self):
        pass

    def get_horizon_coordinates(self):
        """
        uses self.sh_x_s_scaled, self.sh_y_s_scaled, self.sh_x_e_scaled, self.sh_y_e_scaled to get coordinates of the
        horizon line on scaled image and original image as well.
        :return:
        """
        self.hl_x_s_scaled = 0
        self.hl_x_e_scaled = self.w_scaled - 1
        self.hl_slope_scaled = (self.sh_y_e_scaled - self.sh_y_s_scaled) / (self.sh_x_e_scaled - self.sh_x_s_scaled)
        self.hl_intercept_scaled = self.sh_y_s_scaled - self.hl_slope_scaled * self.sh_x_s_scaled

        self.hl_x_s_scaled = 0
        self.hl_x_e_scaled = self.w_scaled - 1
        self.hl_y_s_scaled = self.hl_intercept_scaled
        self.hl_y_e_scaled = self.hl_slope_scaled * self.hl_x_e_scaled + self.hl_intercept_scaled

        # computing Y and alpha of the horizon
        self.hl_slope_org = (self.sh_y_e_org - self.sh_y_s_org) / (self.sh_x_e_org - self.sh_x_s_org)
        self.hl_intercept_org = self.sh_y_s_org - self.hl_slope_org * self.sh_x_s_org
        self.X_hl = int((self.org_w - 1)/2)  # x coordinate corresponding to self.Y_hl

        self.Y_hl = (self.hl_slope_org * self.X_hl) + self.hl_intercept_org
        self.alpha_hl = (-atan(self.hl_slope_org))*(180/pi)

        self.hl_x_s_org = 0
        self.hl_x_e_org = self.org_w - 1
        self.hl_y_s_org = self.hl_intercept_org
        self.hl_y_e_org = self.hl_slope_org * self.hl_x_e_org + self.hl_intercept_org
