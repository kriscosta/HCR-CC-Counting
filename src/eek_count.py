from colour_generator import ColourGenerator
from preprocessor import Preprocessor
from segmenter import Segmenter
import numpy as np
import scipy.misc
import time
import os
import matplotlib.pyplot as plt

class EekCounter:

    __saved_folder_name = None

    median_window_size = 8
    segmenter_type = "WS"
    filter_type = "M"
    aggregate_shape = np.ones((20, 20, 20))
    arcfile = "resources/C6M1A_arc_test.tif"
    filename = "resources/C6M1A_sytox_test.tif"

    enable_debugging = True

    def __init__(self, user_filename=None):
        if user_filename:
            self.filename = user_filename

    def run(self):

      #  arc_preprocessor = Preprocessor(self.arcfile)
      #  arc_preprocessor.apply_silly_filter()
      #  arc_stack = arc_preprocessor.get_image_stack()
      #  z_size, _, _ = arc_stack.shape
      #  self.debug_plot(z_size, arc_stack, "Preprocessed")
      #  return
        self.aggregate_shape = self.create_np_ellipsoid(14, 14, 14)
        preprocessor = Preprocessor(self.filename, self.median_window_size, self.filter_type)

        preprocessed_image_stack = preprocessor.run_preprocessor()
        if self.enable_debugging:
            z_size, _, _ = preprocessed_image_stack.shape
            self.debug_plot(z_size, preprocessed_image_stack, "Preprocessed")

        segmenter = Segmenter(preprocessed_image_stack, self.aggregate_shape, self.segmenter_type,
                              generate_debugging=self.enable_debugging)
        segmented_image_stack = segmenter.run_segmentation()
        if self.enable_debugging:
            self.generate_segment_debug(segmenter)

        colorized_image_stack = self.colorize_image_stack(segmented_image_stack)
        self.save_image_stack(colorized_image_stack)

        arc_preprocessor = Preprocessor(self.arcfile)
        arc_preprocessor.apply_silly_filter()
        arc_stack = arc_preprocessor.get_image_stack()
        z_size, x_size, y_size = arc_stack.shape
        arc_segment_map = {}
        for z in range(0,z_size):
            for x in range(0,x_size):
                for y in range(0,y_size):
                    if arc_stack[z][x][y] == 2:
                        #found a cell
                        if segmented_image_stack[z][x][y] == 0:
                            print "Found a cell that the segmenter didn't find! Layer z: %s x: %s y: %s" %(z, x, y)
                        else:
                            print "Found a cell %s at z: %s x: %s y: %s" %(segmented_image_stack[z][x][y],z, x, y)
                            key = segmented_image_stack[z][x][y]
                            arc_segment_map[key] = 1
        print arc_segment_map

        segment_color_correct = np.zeros((z_size, x_size, y_size))
        for z in range(0, z_size):
            for x in range(0, x_size):
                for y in range(0, y_size):
                    segnum = -1
                    if (segmented_image_stack[z][x][y] in arc_segment_map) or (segmented_image_stack[z][x][y] == 0):
                        segment_color_correct[z][x][y] = segmented_image_stack[z][x][y]
                    else:
                        segment_color_correct[z][x][y] = -1
        colorized_image_stack = self.colorize_image_stack(segment_color_correct)
        self.save_image_stack(colorized_image_stack)
        self.generate_report(segmented_image_stack, arc_segment_map)

    def generate_segment_debug(self, segmenter):
        debug_list = segmenter.get_debug_list()
        for step in debug_list:
            stack = segmenter.get_debug_stack(step)
            z_size, _, _= stack.shape
            self.debug_plot(z_size, stack, step)

    def generate_report(self, segmented_image_stack, arc_segment_map):
        print "\033[1m >>>>>>>>>> Final Report <<<<<<<<<< \033[0m"
        cell_count = self.count_cells(segmented_image_stack)
        print ">>> Folder name: " + self.__saved_folder_name
        print ">>> Total number of unique cells found: " + str(cell_count)
        print ">>> Total number of arc cells found: " + str(len(arc_segment_map.keys()))

    def colorize_image_stack(self, segmented_image_stack):
        print "\033[1m >>>>>>>>>> Colourizing Stack <<<<<<<<<< \033[0m"
        color_generator = ColourGenerator()
        z_size, x_size, y_size = segmented_image_stack.shape
        colorized = np.ndarray(shape=(z_size, x_size, y_size, 4), dtype=int)
        for x in range(0, x_size):
            for y in range(0, y_size):
                for z in range(0, z_size):
                    colorized[z][x][y] = color_generator.get_colour_for_segment(segmented_image_stack[z][x][y])
        return colorized

    def save_image_stack(self, image_stack):
        print "\033[1m >>>>>>>>>> Saving Stack <<<<<<<<<< \033[0m"
        z_size, _, _, _ = image_stack.shape
        base_name = "resources"
        folder_name = "%s/stack" % base_name
        if not os.path.exists(folder_name):
            os.makedirs(folder_name)
        for i in range(0, z_size):
            name = "%s/stack%s.tif" % (folder_name, i)
            slice_of_stack = image_stack[i, ...]
            scipy.misc.toimage(slice_of_stack).save(name)
        self.__saved_folder_name = "%s_%d" % (self.filename.split(".")[0], int(time.time()))
        os.rename(folder_name, self.__saved_folder_name)

    def count_cells(self, segmented_image_stack):
        return len(np.unique(segmented_image_stack))-1

    def debug_plot(self, z_size, ar, user_title):
        plt.figure(figsize=(16, 16))
        for i in range(0, z_size):
            plt.subplot(5, 5, i + 1)
            plt.imshow(ar[i, ...])
        plt.suptitle(user_title)
        plt.show()

    def create_np_ellipsoid(selfs, width, length, height):
        np_elipse = np.zeros((height*2+1, length*2+1, width*2+1))
        a_2 = float(length * length)
        b_2 = float(width * width)
        c_2 = float(height * height)
        for x in range(-length, length+1):
            for y in range(-width,width+1):
                for z in range(-height, height+1):
                    np_elipse[z + height][x + length][y + width] = ((x*x)/a_2 + (y*y/b_2) + (z*z/c_2) <= 1)
        return np_elipse


if __name__ == "__main__":
    eek_counter = EekCounter()
    eek_counter.run()