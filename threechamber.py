from PIL import Image,ImageDraw
import cv2
from pickle import dump, load
import os

stats_dir = "statistics/"
mean_file = stats_dir+"mean.jpg"
sd_file = stats_dir+"sd.jpg"
z_dir = "z_pics/"
z_pickle = 'zscore.pickle'
points_file = 'statistics/mouse_location'
chambers_file = 'statistics/mouse_chamber'

# Only analyze 1 out of every skip frames for speed
skip=100
# Depends on the video
fps=30

def setup():
  if not os.path.isdir(stats_dir):
    os.mkdir(stats_dir)
  if not os.path.isdir(z_dir):
    os.mkdir(z_dir)


def avg_video(video):
  if os.path.isfile(mean_file):
    return Image.open(mean_file)
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
  px1 = [[(0,0,0) for _ in range(frame.size[1])] for _ in range(frame.size[0])]
  mean = Image.new('RGB',frame.size, (0,0,0))
  px = mean.load()
  
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
  mean.save(mean_file, "JPEG")
  return mean 


def stddev_video(video):
  if os.path.isfile(sd_file):
    return Image.open(sd_file)
  mean = avg_video(video)   
  meanpx = mean.load()
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
  px1 = [[(0,0,0) for _ in range(frame.size[1])] for _ in range(frame.size[0])]
  sd = Image.new('RGB',frame.size, (0,0,0))
  px = sd.load()
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
  
  sd.save(sd_file)
  return sd


def z_video(video):
  mean = avg_video(video)
  sd = stddev_video(video)
  mean_px = mean.load()
  sd_px = sd.load()
  zs = []
  vidcap = cv2.VideoCapture(video)
  success,frame=vidcap.read()
  frame=Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
  frames = 0
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
    z_image.save(z_dir+"z_%d.jpg"%frames, "JPEG")
  return zs


def cz_video(video):
  if os.path.isfile(z_pickle):
    f = open(z_pickle, "rb")
    zs = load(f)
  else:
    zs = z_video(video)
    f = open(z_pickle, 'wb')
    dump(zs, f)
    f.close()
  out = open(points_file, "w")
  last = None
  for z  in  zs:
    X,Y = 0,0
    w = 0
    for i in range(len(z)):
      for j in range(len(z[0])):
        if last is not None:
          if abs(i-last[0])>120 or abs(j-last[1])>120:
            continue
        a, b, c = z[i][j]
        wi = a**4 + b**4 + c**4
        w+= wi 
        X+=i*wi
        Y+=j*wi
    last = (X/w,Y/w)
    out.write("(" +str(X/w)+ ", "+str(Y/w)+")")
  out.close()


def which_chamber(video):
  out = open(chambers_file, "w")
  if not os.path.isfile(points_file):
    cz_video(video)
  f = open(points_file)
  for line in f:
    x = float(line.split(", ")[0][1:])   
       
    #Wall locations hard coded for now    
    if x < 210:
      out.write ("0\n")
    if x >= 210 and x < 405:
      out.write ("1\n")
    if x >= 405:
      out.write("2\n")
  out.close()


def time_chamber(video):
  setup()
  if not os.path.isfile(chambers_file):
    which_chamber(video)
  f = open(chambers_file)
  counts = [0,0,0]
  for line in f:
    chamber = int(line)
    counts[chamber]+=skip/fps
  print(counts)

      
  
  
  
  
  
  
  
  
  
