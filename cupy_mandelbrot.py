from mandel_funcs import *
import cupy as cp
import numpy as np
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk




#sets up the GPUs as sets of tuples with (GPU_ID, MEMLIMIT)
#For example: setup_gpus((0, 4*1024**3), (1, 4*1024**3)) to set both GPU0 and GPU1 to 4GB
def setup_gpus(mempool,*args): 
    for arg in args:
        with cp.cuda.Device(arg[0]):
            mempool.set_limit(size=arg[1])

#Class for the frame that contains the canvas that the mandelbrot is rendered in and the mouse/key bindings
class MandelbrotFrame(tk.Frame):
    def __init__(self,parent,mempool,z,mag,res,n_iter,pad,colormap,zoom):
        super().__init__(parent)

        global tkimg

        self.mempool = mempool
        self.parent = parent
        self.z = z
        self.mag = mag
        self.res = res
        self.n_iter = n_iter
        self.pad = pad
        self.colormap = colormap
        self.zoom = zoom

        self.canvas_width = res + 2 * pad
        self.canvas_height = res + 2 * pad

        self.canvas = tk.Canvas(self,width=self.canvas_width,height=self.canvas_height)

        self.mandel = Mandelbrot.fromCenter(mempool,z,mag,res,iterations=n_iter)

        self.canvas_bindings()

        self.img = self.mandel.make_mandel_img(colormap)
        tkimg = ImageTk.PhotoImage(self.img)
        self.canvas_imgID = self.canvas.create_image(self.pad,self.pad,anchor=tk.NW,image=tkimg)
        self.canvas.pack()

    def canvas_bindings(self):
        self.canvas.bind("<Button-1>", lambda event:self.zoomMandel(event))
        self.canvas.bind("<MouseWheel>", lambda event:self.zoomMandel(event,wheel=True))
        self.canvas.bind("<Button-4>", lambda event:self.zoomMandel(event,wheel=True))
        self.canvas.bind("<Button-5>", lambda event:self.zoomMandel(event,wheel=True))
        self.canvas.bind("<Motion>",lambda event:self.crosshairs(event))

    def updateMandel(self):
        global tkimg
        self.img = self.mandel.make_mandel_img(self.colormap)
        tkimg = ImageTk.PhotoImage(self.img)
        self.canvas.itemconfig(self.canvas_imgID,image=tkimg)

    def zoomMandel(self,event,wheel=False):
        cx = event.x
        cy = event.y

        if( not (cx <= self.pad or cy <= self.pad or cx > self.res + self.pad or cy > self.mandel.pixels + self.pad)):
            if(wheel):
                if event.delta < 0:
                    self.mag = self.mandel.mag / self.zoom
                else:
                    self.mag = self.mandel.mag * self.zoom
            else:
                self.mag = self.mandel.mag * self.zoom

            self.z = getCoordFromPixel(cx-self.pad,cy-self.pad,self.res-1,self.mandel.reRange,self.mandel.imRange)
            self.mandel.mag = self.mag
            self.mandel.reRange, self.mandel.imRange = getFrameFromCenter(self.z,self.mag)
            self.updateMandel()

    def crosshairs(self,event):
        global crosshairtoggle

        cx = event.x
        cy = event.y

        if( not (cx <= self.pad or cy <= self.pad or cx > self.res + self.pad or cy > self.mandel.pixels + self.pad)):

            self.canvas.delete('linex')
            self.canvas.delete('liney')

            if crosshairtoggle:
                self.canvas.create_line(self.pad,cy,self.pad+self.res,cy,tags='linex')
                self.canvas.create_line(cx,self.pad,cx,self.pad+self.res,tags='liney')




class MenuBar(tk.Menu):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        fileMenu = tk.Menu(self,tearoff=False)
        fileMenu.add_command(label='Settings',command=None)
        fileMenu.add_command(label='Exit',command=self.quit)
        self.add_cascade(label='File',menu=fileMenu)

    def quit(self):
        self.parent.destroy()

class ToolBar(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent,bd=1,relief=tk.RAISED)
        self.parent = parent
        self.button1 = tk.Button(self, text=u'\u2316',font=('Arial',15),command = self.crosshair_button_toggle)
        self.button1.pack(side=tk.LEFT, padx=2,pady=2)

    def crosshair_button_toggle(self):
        global crosshairtoggle
        if self.button1.config('relief')[-1] == 'sunken':
            self.button1.config(relief=tk.RAISED)
            crosshairtoggle = False
        else:
            self.button1.config(relief=tk.SUNKEN)
            crosshairtoggle = True

class MainGUI(tk.Frame):

    def __init__(self,parent=None,**kwargs):
        super().__init__(parent)
        self.parent = parent
        for key, value in kwargs.items():
            self.__setattr__(key + '_',value)
        self.setupUI()

    def setupUI(self):
        self.parent.title('CuPy Mandelbrot')
        
        menubar = MenuBar(self.parent)
        self.parent.config(menu=menubar)

        toolbar = ToolBar(self.parent)
        toolbar.pack(side=tk.TOP,fill=tk.X)

        mandelframe =  MandelbrotFrame(self.parent,**self.mandelsettings_)
        mandelframe.pack()



def main():

    mempool = cp.get_default_memory_pool()
    memlimit = 4*1024**3
    setup_gpus(mempool,(0,memlimit))

    root = tk.Tk()

    z0, mag0 = (-0.75 + 0.0j, 0.8)
    resolution = 1024
    num_iter = 1024
    padding = 10
    colormap = 'HSV1'
    zoom_multiplier = 1.5
    mandelsettings = {'mempool':mempool,'z':z0,'mag':mag0,'res':resolution,'n_iter':num_iter,'pad':padding,'colormap':colormap,'zoom':zoom_multiplier}


    MainGUI(parent=root,mandelsettings=mandelsettings)


    root.mainloop()

if __name__ == "__main__":
    main()