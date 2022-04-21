
import tkinter as tk
from tkinter import ttk, filedialog
from PIL import Image, ImageTk
from mandel_funcs import *

#Class for the frame that contains the canvas that the mandelbrot is rendered in and the mouse/key bindings
class MandelbrotFrame(tk.Frame):
    def __init__(self,parent,mempool,z,mag,res,n_iter,pad,colormap,zoom):
        super().__init__(parent)

        global tkimg

        self.mempool = mempool
        self.parent = parent

        self.orig_settings = (z,mag,res,n_iter,pad,colormap,zoom)
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

        self.crosshairtoggle = False

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

    def update_mandel(self):
        global tkimg

        self.mandel.mag = self.mag
        self.mandel.pixels = self.res
        self.mandel.iterations = self.n_iter
        self.mandel.colormap = self.colormap
        self.mandel.rerange, self.mandel.imrange = getFrameFromCenter(self.z,self.mag)

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

            self.z = getCoordFromPixel(cx-self.pad,cy-self.pad,self.res-1,self.mandel.rerange,self.mandel.imrange,self.mandel.switchxy)
            self.update_mandel()

    def crosshairs(self,event):

        cx = event.x
        cy = event.y

        if( not (cx <= self.pad or cy <= self.pad or cx > self.res + self.pad or cy > self.mandel.pixels + self.pad)):

            self.canvas.delete('linex')
            self.canvas.delete('liney')

            if self.crosshairtoggle:
                self.canvas.create_line(self.pad,cy,self.pad+self.res,cy,tags='linex')
                self.canvas.create_line(cx,self.pad,cx,self.pad+self.res,tags='liney')




class MenuBar(tk.Menu):
    def __init__(self,parent):
        super().__init__(parent)
        self.parent = parent
        fileMenu = tk.Menu(self,tearoff=False)
        fileMenu.add_command(label='Settings',command=self.settings_window)
        fileMenu.add_command(label='Save Image',command=self.save_img)
        fileMenu.add_command(label='Exit',command=self.quit)
        self.add_cascade(label='File',menu=fileMenu)
        self.mandel_frame = None

    def quit(self):
        self.parent.destroy()

    def save_img(self):
        filename = filedialog.asksaveasfilename(defaultextension=".png",filetypes=[("All Files","*.*"),("PNG","*.png")])
        if filename is None:
            return
        img2 = self.mandel_frame.img.convert('RGB')
        img2.save(filename,"PNG")

    def settings_window(self):
        self.win = tk.Toplevel(self.parent)
        self.settings_win = SettingsWindow(self.win,self.mandel_frame)


class SettingsWindow(tk.Frame):
    def __init__(self,parent,mandel_frame):
        super().__init__(parent)
        self.parent = parent
        self.mandel_frame = mandel_frame
        self.parent.title('Settings')
        self.parent.resizable(0,0)

        self.create_labels()

        self.update_labels()



        applybtn = ttk.Button(self.parent,text = 'Apply',command=self.apply)
        applybtn.grid(row=len(self.labels),column=0)

        okbtn = ttk.Button(self.parent,text= 'OK',command=self.okay)
        okbtn.grid(row=len(self.labels),column=1)

        cancelbtn = ttk.Button(self.parent,text = 'Cancel',command=self.cancel)
        cancelbtn.grid(row=len(self.labels),column=2)

    def create_labels(self):
        self.labels = [
            ['Resolution:','res',tk.IntVar(self.parent,value=self.mandel_frame.res)],
            ['Iterations:','n_iter',tk.IntVar(self.parent,value=self.mandel_frame.n_iter),],
            ['Zoom:','mag',tk.DoubleVar(self.parent,value=self.mandel_frame.mag)],
            ['Zoom rate:','zoom',tk.DoubleVar(self.parent,value=self.mandel_frame.zoom)],
            ['Color pallete:','colormap',None],
            ['Center:','z',None]
        ]



    def update_labels(self):
        for i in range(len(self.labels)):
            label_name = ttk.Label(self.parent,text=self.labels[i][0])
            label_name.grid(row=i,column=0)

            label_value = ttk.Label(self.parent,text=str(getattr(self.mandel_frame,self.labels[i][1])))
            label_value.grid(row=i,column=1)

            if self.labels[i][2]:
                entry = ttk.Entry(self.parent,textvariable=self.labels[i][2])
                entry.grid(row=i,column=2)


    def apply(self):
        for i in range(len(self.labels)):
            if self.labels[i][2]:
                setattr(self.mandel_frame,self.labels[i][1],self.labels[i][2].get())
        self.update_labels()

        self.mandel_frame.update_mandel()

    def cancel(self):
        self.parent.destroy()

    def okay(self):
        self.apply()
        self.parent.destroy()
    



class ToolBar(tk.Frame):
    def __init__(self,parent):
        super().__init__(parent,bd=1,relief=tk.RAISED)
        self.parent = parent
        self.mandel_frame = None

        self.crosshair_button = tk.Button(self, text='\U0001f3af',font=('Arial',15),command = self.crosshair_button_toggle)
        self.crosshair_button.pack(side=tk.LEFT, padx=2,pady=2)

        self.reset_button = tk.Button(self, text='\U0001f504',font=('Arial',15),command=self.reset_button_command)
        self.reset_button.pack(side=tk.LEFT, padx=2,pady=2)

        self.xflip_button = tk.Button(self, text='\U00002194',font=('Arial',15),command=lambda: self.flip_button_command(True))
        self.xflip_button.pack(side=tk.LEFT, padx=2,pady=2)

        self.yflip_button = tk.Button(self, text='\U00002195',font=('Arial',15),command=lambda: self.flip_button_command(False))
        self.yflip_button.pack(side=tk.LEFT, padx=2,pady=2)

        self.xyswap_button = tk.Button(self, text='\U0001F503',font=('Arial',15),command=self.xyswap_button_command)
        self.xyswap_button.pack(side=tk.LEFT, padx=2,pady=2)





    def crosshair_button_toggle(self):
        if self.crosshair_button.config('relief')[-1] == 'sunken':
            self.crosshair_button.config(relief=tk.RAISED)
            if self.mandel_frame:
                self.mandel_frame.crosshairtoggle = False
                self.mandel_frame.canvas.delete('linex')
                self.mandel_frame.canvas.delete('liney')
        else:
            self.crosshair_button.config(relief=tk.SUNKEN)
            if self.mandel_frame:
                self.mandel_frame.crosshairtoggle = True

    def reset_button_command(self):
        self.mandel_frame.z,self.mandel_frame.mag,self.mandel_frame.res,self.mandel_frame.n_iter,self.mandel_frame.pad,self.mandel_frame.colormap,self.mandel_frame.zoom = self.mandel_frame.orig_settings
        self.mandel_frame.mandel.revx = False
        self.mandel_frame.mandel.revy = False
        self.mandel_frame.mandel.switchxy = False
        self.mandel_frame.update_mandel()

    def flip_button_command(self,xpress):

        if xpress^self.mandel_frame.mandel.switchxy:
            if self.mandel_frame.mandel.revx:
                self.mandel_frame.mandel.revx = False
            else:
                self.mandel_frame.mandel.revx = True
        else:
            if self.mandel_frame.mandel.revy:
                self.mandel_frame.mandel.revy = False
            else:
                self.mandel_frame.mandel.revy = True


        self.mandel_frame.update_mandel()

    def xyswap_button_command(self):
        if self.mandel_frame.mandel.switchxy:
            self.mandel_frame.mandel.switchxy = False
        else:
            self.mandel_frame.mandel.switchxy = True

        self.mandel_frame.update_mandel()

class MainGUI(tk.Frame):

    def __init__(self,parent=None,**kwargs):
        super().__init__(parent)
        self.parent = parent
        for key, value in kwargs.items():
            self.__setattr__(key + '_',value) #future prooofing for other dictionary setting arguments
        self.setup_interface()

    def setup_interface(self):
        self.parent.title('CuPy Mandelbrot')
        
        self.menubar = MenuBar(self.parent)
        self.parent.config(menu=self.menubar)

        self.toolbar = ToolBar(self.parent)
        self.toolbar.pack(side=tk.TOP,fill=tk.X)

        self.mandelframe =  MandelbrotFrame(self.parent,**self.mandelsettings_)
        self.mandelframe.pack()

        self.menubar.mandel_frame = self.mandelframe
        self.toolbar.mandel_frame = self.mandelframe

    def onclose(self):
        del(self.mandelframe.mandel)