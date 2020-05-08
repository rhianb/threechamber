from PIL import Image,ImageDraw
import cv2
from pickle import dump, load
import os.path

def drawtri():
  img = Image.new('RGB', (100,100), (255,255,255))
  draw = ImageDraw.Draw(img)
  draw.polygon([(10,10),(10,90), (90,10)], fill=(200,20,20))
  img.save("tri.jpg", "JPEG")

def circlemouse():
  im = Image.open("mouse.png")
  img = threshold(im, (50,50,50))
  img.save("mouse3.jpg", "JPEG")

def threshold(im, thres):
  img = Image.new('RGB',im.size, (255,255,255))
  px = im.load()
  px2 = img.load()
  for i in range(im.size[0]):
    for j in range(im.size[1]):
      cur_color = px[i,j]
      if cur_color[0]<thres[0] or cur_color[1]<thres[1] or cur_color[2]<thres[2]:
        px2[i,j] = (0,0,0)
      else:
        px2[i,j] = (255,255,255)
  return img

def difference(im1,im2):
  im = Image.new('RGB',im1.size, (255,255,255))
  px1 = im1.load()
  px2 = im2.load()
  px3 = im.load()
  for i in range(im.size[0]):
    for j in range(im.size[1]):
      color1 = px1[i,j]
      color2 = px2[i,j]
      if color1!=color2:
        px3[i,j] = (0,0,0)
      else:
        px3[i,j] = (255,255,255)
  return im

def load_video(video):
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  last=frame
  i = 0
  while success:
    i+=1
    if i%50 == 3:
      pil_image=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
      pil_image=threshold(pil_image,(100,100,100))
      pil_image2=Image.fromarray(cv2.cvtColor(last, cv2.COLOR_BGR2RGB))
      pil_image2=threshold(pil_image2,(100,100,100))
      output=difference(pil_image,pil_image2)
      output.save("frames/diff"+str(i)+".jpg", "JPEG")
    last=frame
    success,frame = vidcap.read()

  # Homework for Rhi!
  # Make an image which is a red circle on a black background (Hint: consider drawtri)
  # Color invert the mouse threshold
  # Make some generative art!
  # Things to learn about: for loops, if statements, strings, functions, tuples, lists

def avg_video(video):
  if os.path.isfile("frames/mean.jpg"):
    return Image.open("frames/mean.jpg")
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
  px1 = [[(0,0,0) for _ in range(frame.size[1])] for _ in range(frame.size[0])]
  mean = Image.new('RGB',frame.size, (0,0,0))
  px = mean.load()
  skip=100
  while success:
    if frames%skip == 0:
      print(frames)
    success,frame = vidcap.read()
    if not success:
      break
    frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    frames+=1
    if frames%skip !=0:
      continue
    px2 = frame.load()
    for i in range(frame.size[0]):
      for j in range(frame.size[1]):
        px1[i][j] = tuple([x+y for (x,y) in zip(px1[i][j],px2[i,j])])
  for i in range(mean.size[0]):
      for j in range(mean.size[1]):
        px[i,j] = tuple([v//(frames//skip) for v in px1[i][j]])
        
  mean.save("frames/mean.jpg", "JPEG")

  return mean 

def stddev_video(video, mean=None):
  if os.path.isfile("frames/sd.jpg"):
    return Image.open("frames/sd.jpg")
  if mean is None:
    if os.path.isfile("frames/mean.jpg"):
      mean = Image.open("frames/mean.jpg")
    else:
      mean = avg_video(video)
    
  meanpx = mean.load()
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
  px1 = [[(0,0,0) for _ in range(frame.size[1])] for _ in range(frame.size[0])]
  sd = Image.new('RGB',frame.size, (0,0,0))
  px = sd.load()
  skip=100
  while success:
    if frames%skip == 0:
      print(frames)
    success,frame = vidcap.read()
    if not success:
      break
    frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    frames+=1
    if frames%skip !=0:
      continue
    px2 = frame.load()
    for i in range(frame.size[0]):
      for j in range(frame.size[1]):
        px1[i][j] = tuple([x+(y-z)**2 for (x,y,z) in zip(px1[i][j],px2[i,j],meanpx[i,j])])
  for i in range(sd.size[0]):
      for j in range(sd.size[1]):
        px[i,j] = tuple([v//(frames//skip) for v in px1[i][j]])
  
  sd.save("frames/sd.jpg")
  return sd

def z_video(video):
  mean = avg_video(video)
  sd = stddev_video(video, mean)
  mean_px = mean.load()
  sd_px = sd.load()
  zs = []
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
  skip=100
  while success:
    if frames%skip == 0:
      print(frames)
    success,frame = vidcap.read()
    if not success:
      break
    frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    frames+=1
    if frames%skip !=0:
      continue
    px2 = frame.load()
    z = [[(0,0,0) for _ in range(frame.size[1])] for _ in range(frame.size[0])]
    z_image = Image.new('RGB',frame.size, (0,0,0))
    z_px = z_image.load()
    for i in range(frame.size[0]):
      for j in range(frame.size[1]):
        z[i][j] = tuple([max(0, int((m-x))) if s!=0 else 0 for (m,s,x) in zip(mean_px[i,j],sd_px[i,j],px2[i,j])])
        z_px[i,j] = tuple([min(255,4*max(0,(int((m-x))))) if s!=0 else 0 for (m,s,x) in zip(mean_px[i,j],sd_px[i,j],px2[i,j])])
    zs.append(z)
    z_image.save("frames2/z2_%d.jpg"%frames, "JPEG")
  return zs
    

z_file = 'pickle_zs'

def cz_video(video):
  if os.path.isfile(z_file):
    f = open(z_file, "rb")
    zs = load(f)
  else:
    zs = z_video(video)
    f = open(z_file, 'wb')
    dump(zs, f)
    f.close()
  last = None
  for z  in  zs:
    X,Y = 0,0
    w = 0
    for i in range(len(z)):
      for j in range(len(z[0])):
        if last is not None:
          if abs(i-last[0])>120 or abs(j-last[1])>120:
            continue
        a, b, c  = z[i][j]
        wi = a**4 + b**4 + c**4
        w+= wi 
        X+=i*wi
        Y+=j*wi
    last = (X/w,Y/w)
    print("(" +str(X/w)+ ", "+str(Y/w)+")")


