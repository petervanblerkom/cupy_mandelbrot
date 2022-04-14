import numpy as np
import cupy as cp
from PIL import Image

iterative_complex_escape = cp.ElementwiseKernel(
    'T z, T c, uint32 N',
    'uint32 m',
    '''
        T q = z;
        m = 0;
        for(int j = 0; j<N; j++){
            q = q * q + c;
            if(abs(q)>2){
                m = j;
            }
        }
    ''',
    'iterative_complex_escape')


colormap_kernel = cp.ElementwiseKernel(
    'T w, T m', #input w, mode m with 0 == hsv with only h changing
    'uint8 a, uint8 b, uint8 c',
    '''
    if(m==0) {

        if(w==0) {
            a = b = c = 0;
        } else {
            a = w%255;
            b = c = 255;
        }
    } else if (m==1){
        if(w==0) {
            a = b = c = 0;
        } else {
            a = w%255;
            b = 255-w/255;
            c = 255;
        }
    } else if (m==2){
        if(w==0) {
            a = b = c = 0;
        } else {
            a = w%255;
            b = 255-(w*64)/255;
            c = 255;
        }
    }
    ''',
    'colormap_kernel')

colormap_dict = {'HSV0':0,'HSV1':1,'HSV2':2}

# def blocksplit(c,sets): 

#     #split into blocks that may not be evenly spaced, reassemble with np.block()

#     q = [np.array_split(x,split,axis=1) for x in np.array_split(z,split,axis=0)] 

#     return(q)


def getFrameFromCenter(center=-0.75 + 0j,mag=1.0,ratio=1.0):
    if mag > 0:
        zoom = 1/mag
    else:
        zoom = 1.0

    xmin = center.real - zoom
    xmax = center.real + zoom
    ymin = center.imag - zoom * ratio
    ymax = center.imag + zoom * ratio

    reRange = (xmin,xmax)
    imRange = (ymin,ymax)

    return reRange, imRange

def getCoordFromPixel(px,py,pixels,reRange,imRange):
    real_pt = (px/pixels) * (reRange[1] - reRange[0]) + reRange[0]
    im_pt = (py/pixels) * (imRange[0] - imRange[1]) * 1j + imRange[1] * 1j

    return real_pt + im_pt
    


class Mandelbrot:

    def __init__(self,mempool,reRange,imRange,mag,pixels,ratio=1.0,iterations=256):
        print("Creating mandelbrot")

        self.mempool = mempool
        self.mag = mag
        self.pixels = pixels
        self.iterations = iterations
        self.ratio = ratio
        self.imRange = imRange
        self.reRange = reRange

    @classmethod
    def fromCenter(cls,mempool,center,mag,pixels,ratio=1.0,iterations=256):
        reRange, imRange = getFrameFromCenter(center,mag,ratio)
        return cls(mempool,reRange,imRange,mag,pixels,ratio,iterations)



    def create_pixel_plane(self,revx=False,revy=False,switchxy=False):

        #turn a boundary into a pixel grid of values in the complex plane

        if revx:
            self.reRange = (self.reRange[1],self.reRange[0])
        if revy:
            self.imRange = (self.imRange[1],self.imRange[0])

        c0 = cp.mgrid[self.imRange[1]:self.imRange[0]:self.pixels*1j,self.reRange[0]:self.reRange[1]:int(self.pixels*self.ratio)*1j]
   
        self.c = c0[1] + 1j*c0[0]

        # if not switchxy:
        #     self.c = self.c.T

    def coord_from_pixel(self,xpix,ypix):
        return (self.c[ypix][xpix]).get()

    def run_iteration(self):
        self.escape = iterative_complex_escape(0,self.c,self.iterations)

    def make_image(self,colormap = 'HSV0'):
        self.colormap = colormap
        self.image = colormap_kernel(self.escape,colormap_dict[colormap])
        q_a = cp.asnumpy(self.image[0])
        q_b = cp.asnumpy(self.image[1])
        q_c = cp.asnumpy(self.image[2])
        return q_a, q_b, q_c

    def make_mandel_img(self,colormap='HSV0'):
        self.create_pixel_plane()
        self.run_iteration()
        h,s,v = self.make_image(colormap)
        img_a = Image.fromarray(h,mode='L')
        img_b = Image.fromarray(s,mode='L')
        img_c = Image.fromarray(v,mode='L')
        img = Image.merge('HSV',(img_a,img_b,img_c))
        return img


    def __del__(self):
        self.mempool.free_all_blocks()
        print("Freeing memory")

        


    




