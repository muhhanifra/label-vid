import tkinter
import tkinter as tk
import numpy as np
from PIL import ImageTk, Image
import cv2
import os
import json

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

        self.current_dir = self.file_paths[0]
        #root init----
        self.root = tk.Tk()

        #important var init----
        self.annotation_outputs = {}
        try:
            self.load_existing_output()
        except:
            pass
        self.slider_val = 0
        self.video_state = True
        self.frame = 0
        self.file_index = 0
        
        #image--------------
        
        self.frame_delay = 30
        self.cap = cv2.VideoCapture(self.current_dir)
        self.vid_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        self.preprocess_image()
        self.image_label = tk.Label(image = self.image_tk)

        #user inputs------
        self.anno_entry = tk.Entry(self.root, width = 50, borderwidth = 5)
        self.anno_entry.bind("<Return>",self.add_annotation)
        self.anno_entry.bind("<Control-space>",self.play_button)
        self.anno_entry.bind("<Control-Up>", self.move_to_prev_vid) 
        self.anno_entry.bind("<Control-Down>", self.move_to_next_vid) 
        self.anno_entry.bind("<Control-d>", self.delete_1_output)
        self.anno_entry.bind("<Control-f>", self.delete_all_output)
        self.anno_entry.bind("<Up>", self.jump_frame_left)
        self.anno_entry.bind("<Down>", self.jump_frame_right)

        self.annotate = tk.Button(self.root, text = 'annotate', command = self.add_annotation)
        self.play = tk.Button(self.root, text = 'play/pause',command = self.play_button)
    
        self.vid_slider = tk.Scale(self.root, from_ = 0, 
                                    to = self.vid_length,orient ='horizontal',
                                    command = self.slider_frame,
                                    width = 20, length = 500)
        #delete buttons-----------------
        self.delete_1_output = tk.Button(self.root, text = 'Delete annotation', command = self.delete_1_output)
        self.delete_output = tk.Button(self.root, text = 'Delete all annonations', command = self.delete_all_output)

        #listbox and scrollbars-------
        self.listbox_frame = tk.Frame(self.root)
        self.list_scrollbar = tk.Scrollbar(self.listbox_frame, orient = tk.VERTICAL)
        self.vid_list_box = tk.Listbox(self.listbox_frame, width = 40, yscrollcommand = self.list_scrollbar)
        self.list_scrollbar.config(command=self.vid_list_box.yview)
        for file_path in self.file_paths:
            self.vid_list_box.insert('end', file_path)
        self.vid_list_box.bind("<Double-Button-1>", self.select_vid)
        #self.vid_list_box.selection_set(self.file_index) #----------------------------------------------EDIT

        #text labels-------
        self.iterator = tk.Label(self.root, text = '')
        self.iterator.after(1, self.increment_frame)
        self.annotation_cat = 'none'
        self.annotation_label_var = tk.StringVar()
        self.annotation_label_var.set(self.annotation_outputs)
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
        self.delete_1_output.grid(row = 7, column = 0)
        self.delete_output.grid(row =8, column = 0)
        self.listbox_frame.grid(row=0, column = 1, columnspan=2)
        self.list_scrollbar.pack(side=tk.RIGHT, fill =tk.Y)
        self.vid_list_box.pack()
        

        self.root.mainloop()

    def reset_var(self):
        '''reset important variables to initial state'''
        self.vid_length = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)) - 1
        #important var init----
        self.annotation_outputs = {}
        try:
            self.load_existing_output()
        except:
            pass
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

    def move_to_next_vid(self, event = None):
        try:
            self.vid_list_box.selection_clear(self.vid_list_box.curselection()[0])
        except:
            pass
        self.file_index+=1
        if self.file_index >= len(self.file_paths) - 1:
            self.file_index = len(self.file_paths) - 1
        self.vid_list_box.selection_set(self.file_index)

        self.current_dir = self.file_paths[self.file_index]
        self.cap.release()
        self.cap = cv2.VideoCapture(self.current_dir)
        self.reset_var()

    def move_to_prev_vid(self, event = None):
        try:
            self.vid_list_box.selection_clear(self.vid_list_box.curselection()[0])
        except:
            pass

        self.file_index-=1
        if self.file_index<=0:
            self.file_index = 0  
        self.vid_list_box.selection_set(self.file_index)

        self.current_dir = self.file_paths[self.file_index]
        self.cap.release()
        self.cap = cv2.VideoCapture(self.current_dir)
        self.reset_var()

    def load_existing_output(self):
        current_dir_name = self.current_dir.split('.')[0]
        with open('{}.json'.format(current_dir_name)) as json_file:
            data = json.load(json_file)
        for frame_i in list(data['annotations'][0].keys()):
            self.annotation_outputs[int(frame_i)] = data['annotations'][0][frame_i]

    def delete_all_output(self, event = None):
        self.annotation_outputs = {}
        self.annotation_label_var.set(self.annotation_outputs)
        self.dump_to_json()
    
    def delete_1_output(self, event = None):
        self.annotation_outputs.pop(list(self.annotation_outputs.keys())[-1])
        self.annotation_label_var.set(self.annotation_outputs)
        self.dump_to_json()
    
    def jump_frame_right(self, event = None):
        self.frame = self.frame + 20
        self.vid_slider.set(self.frame)
        if self.frame >=self.vid_length:
            self.frame = self.vid_length
        self.preprocess_and_update_image()

    def jump_frame_left(self, event = None):
        self.frame = self.frame - 20
        self.vid_slider.set(self.frame)
        if self.frame <=0:
            self.frame = 0
        self.preprocess_and_update_image()
    
if __name__ == "__main__":
    app = video_annotator()