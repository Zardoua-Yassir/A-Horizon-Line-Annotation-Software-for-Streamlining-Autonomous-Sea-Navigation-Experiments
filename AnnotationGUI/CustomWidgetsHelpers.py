
def check_img_size(im_as_pil, wmax, hmax):
    """
    Check if the width and height of the image im_as_pil exceeds the maximum dimensions (width and height) given in wmax
    and hmax, resize the image with the same aspect ratio to the maximum exceeded dimension.

    For instance, if wmax = 1000 and hmax = 500 and the width and height of im_as_pil are w = 1200, h = 300, respectively,
    then, the scaling factor used to change w and h is : scaling_factor = 1000/1200. Thus, the returned image has a width
    and height equal to w * scaling_factor and h * scaling_factor, respectively.

    :param im_as_pil: input image as a PIL class
    :param wmax: maximum width the input image should not exceed
    :param hmax: maximum height the input image should not exceed
    :return: a tkinter image with the same size as im_as_pil if thresholds wmax and hmax are not exceeded, or resized
    if aforementioned thresholds are exceeded.
    """
    # Getting the original width and height of the image to display
    org_w, org_h = im_as_pil.size

    if org_w >= wmax or org_h >= hmax:  # True if the image dimensions exceed the thresholds wmax,hmax
        # to resize the image to fit wmax and hmax, we take the manimum scaling factor.
        # to keep aspect ratio of rescaled image, both width and height are rescaled with the same factor.
        scaling_factor = min(wmax / org_w, hmax / org_h)
        w_scaled = int(org_w * scaling_factor)
        h_scaled = int(org_h * scaling_factor)
        im_as_pil = im_as_pil.resize((w_scaled, h_scaled))
    else:  # True if the image is not rescaled.
        # scaled dimensions are the same as original dimensions.
        w_scaled, h_scaled = org_w, org_h
        # also, im_as_pil is not processed. It shall be returned as provided in the input
    return im_as_pil, w_scaled, h_scaled


def compensate_xy_padding(x, y, w, h):
    """
    Solves the innacurate x,y coordinates of the mouse position on 'image label' widget.
    ------------------------------------------------------------------------------------
    Description of the solved issue:
    -------------------------
    The coordinates of the mouse position on the image label has error of 2 pixels.
    This error is explained by the observation that Tkinter pads any given image with 2 pixels from all sides (top, bottom, right, left)
    This function compensates this padding.
    I developed this simple correction because I want to be as accurate as possible when annotating my dataset.
    :param x: x coordinate on the label (obtained as the event attribute x.event)
    :param y: y coordinate on the label (obtained as the event attribute y.event)
    :param w: the width of the image displayed on the label image (the latter may have been rescaled before displaying it)
    :param h: the height of the image displayed on the label image
    :return: the tuple x_comp, y_comp, representing the compensated coordinates x, y.
    """
    # compensate the two pixels error
    x = x - 2
    y = y - 2

    # making sure that the smallest value of x and y is 0
    if x < 0:
        x = 0
    if y < 0:
        y = 0

    # making sure x and y are smaller than width and height (e.g., if w = 500 pixels, x should not exceed (w - 1) since it starts from 0)
    if x >= w:
        x = w - 1
    if y >= h:
        y = h - 1

    return x, y


def rescale_to_org_xy(x, y, org_w, org_h, w_scaled, h_scaled):
    """
    Rescale x,y coordinates of a down-sized image to x,y coordinates of the original image. This function is useful when
    a developer, for example, wants to display the real x,y coordinates of the mouse on an image when the latter is rescaled.
    :param x: x coordiante to rescale (if necessary)
    :param y: y coordiante to rescale (if necessary)
    :param org_w: width of the original image (i.e., width before rescaling)
    :param org_h: height of the original image (i.e., height before rescaling)
    :param w_scaled: the width of the scaled image
    :param h_scaled: the height of the scaled image
    :return: a tuple (x, y) of the rescaled coordinates
    """
    if w_scaled != 1 and h_scaled != 1:  # True if the image is scaled
        x = int(x * (org_w / w_scaled))
        y = int(y * (org_h / h_scaled))
        return x, y
    else:  # True if the image isn't scaled
        return x, y


def is_gray(img):
    """
    Checks if img is grayscale
    :param img: input image
    :return: True if img is grayscale (1 channel), False otherways
    """
    img_type = type(img).__name__
    if img_type == 'ndarray':
        if len(img.shape) == 2:  # True if the number of dimensions is only 2: width and height. This is assumed to imply there is no dimension for channels because it's assumed to have only one channel)
            return True
        else:
            return False
    else:
        raise TypeError("Class of input argument img must be 'numpy.ndarray' not {}".format(img_type))



# ImageShow.show(impil, "title")
# ImageShow.show(impilg, "title")
# cv.imshow("title", imnp)
# cv.waitKey()
# cv.imshow("title", imnpg)
# cv.waitKey()
# cv.destroyAllWindows()
