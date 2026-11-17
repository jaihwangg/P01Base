"""External NDI test sender; uses the NDI runtime already bundled with this UE install.
Run with Python 3, optionally --seconds 180. No audio is transmitted.
"""
import ctypes as c, time, argparse
from pathlib import Path
parser=argparse.ArgumentParser(); parser.add_argument('--seconds',type=int,default=180); parser.add_argument('--orientation',action='store_true')
args=parser.parse_args()
dll=Path('C:/Program Files/Epic Games/UE_5.8/Engine/Plugins/Media/NDIMedia/Binaries/ThirdParty/Win64/Processing.NDI.Lib.x64.dll')
ndi=c.CDLL(str(dll))
class Create(c.Structure):
    _fields_=[('name',c.c_char_p),('groups',c.c_char_p),('clock_video',c.c_bool),('clock_audio',c.c_bool)]
class Frame(c.Structure):
    _fields_=[('width',c.c_int),('height',c.c_int),('fourcc',c.c_int),('fps_n',c.c_int),('fps_d',c.c_int),('aspect',c.c_float),('format',c.c_int),('timecode',c.c_int64),('data',c.POINTER(c.c_uint8)),('stride',c.c_int),('metadata',c.c_char_p),('timestamp',c.c_int64)]
ndi.NDIlib_initialize.restype=c.c_bool
ndi.NDIlib_send_create.argtypes=[c.POINTER(Create)]; ndi.NDIlib_send_create.restype=c.c_void_p
ndi.NDIlib_send_send_video_v2.argtypes=[c.c_void_p,c.POINTER(Frame)]
ndi.NDIlib_send_destroy.argtypes=[c.c_void_p]
assert ndi.NDIlib_initialize()
sender=ndi.NDIlib_send_create(c.byref(Create(b'PJ2DMX Test',None,True,False)))
assert sender
w,h=640,360
colors=[(255,255,255),(255,255,0),(0,255,255),(0,255,0),(255,0,255),(255,0,0),(0,0,255),(24,24,24)]
row=b''.join(bytes((b,g,r,255))*(w//8) for r,g,b in colors)
pattern=(bytes((0,0,255,255))*w*(h//2)+bytes((255,0,0,255))*w*(h//2)) if args.orientation else row*h
buffer=(c.c_uint8*(w*h*4)).from_buffer_copy(pattern)
frame=Frame(w,h,int.from_bytes(b'BGRA','little'),30,1,w/h,1,0,buffer,w*4,None,0)
print('NDI sender: PJ2DMX Test (640x360 / 30 fps), no audio',flush=True)
start=time.monotonic(); count=0
try:
    while time.monotonic()-start<args.seconds:
        # Moving bright strip proves that the receiver is displaying new frames.
        y=count%h
        c.memmove(c.addressof(buffer)+y*w*4,pattern[y*w*4:(y+1)*w*4],w*4)
        y=(y+1)%h
        c.memset(c.addressof(buffer)+y*w*4,255,w*4)
        frame.timecode=count*10000000//30
        ndi.NDIlib_send_send_video_v2(sender,c.byref(frame)); count+=1
finally:
    ndi.NDIlib_send_destroy(sender); ndi.NDIlib_destroy()
    print('Frames sent:',count,flush=True)
