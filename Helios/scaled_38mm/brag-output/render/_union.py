import subprocess, numpy as np, io, sys
from PIL import Image
BG = np.array([0x16,0x19,0x1e], dtype=np.int16)
THR = 10

def read_all(path):
    p = subprocess.run(["ffmpeg","-v","error","-i",path,"-f","rawvideo","-pix_fmt","rgb24","-"],
                       capture_output=True)
    a = np.frombuffer(p.stdout, dtype=np.uint8)
    n = a.size // (1920*1080*3)
    return a[:n*1920*1080*3].reshape(n,1080,1920,3).astype(np.int16)

def masks(path):
    v = read_all(path)
    return (np.abs(v - BG).max(axis=3) > THR), v.shape[0]

def bands(m, label):
    # m: (rows, cols) boolean union mask
    occ = m.any(axis=1)
    print(f"\n-- {label}: rows with any subject --")
    # contiguous occupied runs
    d = np.diff(occ.astype(int)); starts = list(np.where(d==1)[0]+1); ends = list(np.where(d==-1)[0])
    if occ[0]: starts=[0]+starts
    if occ[-1]: ends=ends+[len(occ)-1]
    for s,e in zip(starts,ends):
        cols = np.where(m[s:e+1].any(axis=0))[0]
        print(f"   y {s:4}-{e:4} ({100*s/1080:5.1f}%-{100*e/1080:5.1f}%)  x {cols[0]:4}-{cols[-1]:4}")
    free = np.where(~occ)[0]
    d = np.diff(free); brk = np.where(d>1)[0]
    runs=[]; st=0
    for b in brk: runs.append((free[st],free[b])); st=b+1
    if len(free): runs.append((free[st],free[-1]))
    print(f"   FREE row bands: " + ", ".join(f"{a}-{b}" for a,b in runs))

for name, path, subs in [
    ("stack", "clips/stack.mp4", [("scene1 f0-135",0,136), ("scene2 f126-269",126,270)]),
    ("bay",   "clips/bay.mp4",   [("all",0,None)]),
    ("nose",  "clips/nose.mp4",  [("all",0,None), ("f70+",70,None), ("f0-80",0,81)]),
    ("hero",  "clips/hero.mp4",  [("all",0,None)]),
]:
    m, n = masks(path)
    print(f"\n===== {name}  ({n} frames) =====")
    for lab, a, b in subs:
        bands(m[a:(b if b else n)].any(axis=0), f"{name} {lab}")
