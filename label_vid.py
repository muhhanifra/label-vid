import tkinter
import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
import cv2
import os
import json
import pandas as pd

class video_annotator():
    def __init__(self):

        dir_input = input('type in directory name (you can just press enter for default dir name -dataset-):')
        if dir_input == '':
            self.main_dir = 'dataset'
        else:
            self.main_dir = dir_input
        #------
        self.include_formats = ['.mkv', '.mp4', '.avi']
        self.filenames = os.listdir(self.main_dir)
        self.file_paths = []
        for fn in self.filenames:
            for include_format in self.include_formats:
                if fn.endswith(include_format):
                    self.file_paths.append(os.path.join(self.main_dir,fn))
        print(self.file_paths)

        #root init----
        self.root = tk.Tk()

        #important var init----
        self.annotation_outputs = {}
        self.slider_val = 0
        self.video_state = True
        self.frame = 0
        
        #image--------------
        self.current_dir = self.file_paths[0]
        self.frame_delay = 30
        self.cap = cv2.VideoCapture(self.current_dir)
        self.vid_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.preprocess_image()
        self.image_label = tk.Label(image = self.image_tk)

        #user inputs------
        self.anno_entry = tk.Entry(self.root, width = 50, borderwidth = 5)
        self.anno_entry.bind("<Return>",self.add_annotation)
        self.anno_entry.bind("<Shift_R>",self.play_button)
        #another key 

        self.annotate = tk.Button(self.root, text = 'annotate', command = self.add_annotation)
        self.play = tk.Button(self.root, text = 'play/pause',command = self.play_button)
    
        self.vid_slider = tk.Scale(self.root, from_ = 0, 
                                    to = self.vid_length,orient ='horizontal',
                                    command = self.slider_frame,
                                    width = 20, length = 500)

        self.reset = tk.Button(self.root, text = 'reset', command = self.reset_var)
        self.vid_list_box = tk.Listbox(self.root)
        for file_path in self.file_paths:
            self.vid_list_box.insert('end', file_path)
        self.vid_list_box.bind("<Double-Button-1>", self.select_vid)
        #text labels-------
        self.iterator = tk.Label(self.root, text = '')
        self.iterator.after(1, self.increment_frame)
        self.annotation_cat = 'none'
        self.annotation_label_var = tk.StringVar()
        self.annotation_label_var.set({})
        self.annotation_label = tk.Label(self.root, textvariable = self.annotation_label_var)
        self.slider_var = tk.StringVar()
        self.slider_var.set(str(self.slider_val))
        self.slider_label = tk.Label(self.root, textvariable= self.slider_var)

        #packing---------
        self.image_label.grid(row=0, column =0, columnspan=1)
        self.play.grid(row=1, column =0)
        self.vid_slider.grid(row=2, column =0)
        self.slider_label.grid(row=3, column =0)
        self.anno_entry.grid(row=4, column =0)
        self.annotate.grid(row=5, column =0)
        self.annotation_label.grid(row=6, column =0)
        self.reset.grid(row =7, column = 0)
        self.vid_list_box.grid(row=0, column =2)

        self.root.mainloop()

    def reset_var(self):
        '''reset important variables to initial state'''
        self.vid_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        #important var init----
        self.annotation_outputs = {}
        self.slider_val = 0
        self.video_state = True
        self.frame = 0
        self.vid_slider.set(self.frame)
        self.vid_slider.config(to = self.vid_length)
        self.annotation_label_var.set(self.annotation_outputs)
        self.preprocess_and_update_image()

    def play_button(self, event = None):
        self.iterator.after(1, self.increment_frame)
        if self.video_state == False:
            self.video_state = True
        else:
            self.video_state = False

    def increment_frame(self):
        if self.video_state == True:
            self.frame = self.frame + 1
            self.vid_slider.set(self.frame)
            if self.frame >=self.vid_length:
                self.frame = 0
            self.preprocess_and_update_image()
            self.iterator.after(self.frame_delay, self.increment_frame)

    def add_annotation(self, event = None):
        self.annotation_outputs[self.frame] = self.anno_entry.get()
        self.annotation_label_var.set(self.annotation_outputs)
        self.dump_to_json()
        
    def slider_frame(self, frame):
        self.frame = int(frame)
        slider_updated_val = self.vid_slider.get()
        self.slider_var.set(str(slider_updated_val))
        self.preprocess_and_update_image()
        
    def preprocess_image(self):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, self.frame)
        self.ret, self.image = self.cap.read()
        self.image = cv2.cvtColor(self.image, cv2.COLOR_BGR2RGB)
        self.image = Image.fromarray(self.image)
        self.image_tk = ImageTk.PhotoImage(self.image)

    def preprocess_and_update_image(self):
        self.image_label.grid_forget()
        self.preprocess_image()
        self.image_label = tk.Label(image = self.image_tk)
        self.image_label.grid(row=0, column=0, columnspan=1)

    def select_vid(self, event = None):
        self.current_dir =self.vid_list_box.get(self.vid_list_box.curselection())
        #self.vid_list_box.selection_set(0)
        self.cap.release()
        self.cap = cv2.VideoCapture(self.current_dir)
        self.reset_var()

    def dump_to_json(self):
        self.json_output = {'n_frame': self.vid_length + 1, 'annotations':[self.annotation_outputs]}
        current_dir_name = self.current_dir.split('.')[0]
        with open('{}.json'.format(current_dir_name), 'w') as json_file:
            json.dump(self.json_output, json_file)
    

if __name__ == "__main__":
    app = video_annotator()