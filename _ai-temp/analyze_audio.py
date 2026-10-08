import soundfile as sf, os, glob, math, collections

def rms_db(x):
    if len(x)==0: return -math.inf
    r = math.sqrt(sum(v*v for v in x)/len(x))
    return 20*math.log10(r) if r>0 else -math.inf

def peak_db(x):
    p = max(abs(v) for v in x) if len(x) else 0
    return 20*math.log10(p) if p>0 else -math.inf

def silence_frac(x, fs, thr=-45.0):
    win = max(1, int(fs*0.1))
    n = len(x)//win
    if n==0: return 1.0
    s = 0
    for i in range(n):
        seg = x[i*win:(i+1)*win]
        r = math.sqrt(sum(v*v for v in seg)/len(seg))
        db = 20*math.log10(r) if r>0 else -math.inf
        if db < thr: s+=1
    return s/n

rows=[]
files = sorted(glob.glob('assets/voice/*')) + sorted(glob.glob('assets/audio/amb/*')) + sorted(glob.glob('assets/audio/music/*')) + sorted(glob.glob('assets/audio/sfx/*'))
for f in files:
    if not f.endswith(('.mp3','.ogg','.wav','flac','.m4a')): continue
    try:
        data, fs = sf.read(f, dtype='float32')
    except Exception as e:
        rows.append((f, 'READ FAIL', str(e)[:80])); continue
    if data.ndim>1: data = data.mean(axis=1)
    dur = len(data)/fs
    rows.append((f, round(dur,1), round(rms_db(data),1), round(peak_db(data),1), round(silence_frac(data,fs),2)))

voice = [r for r in rows if 'assets/voice' in r[0] and r[1]!='READ FAIL']
bad = [r for r in voice if r[2] < -40 or r[4] > 0.6 or r[1] < 0.5]
print("=== SUSPICIOUS VOICE FILES (rms<-40dB or >60% silent or <0.5s) ===")
for r in sorted(bad, key=lambda r: r[2]): print(r)
print()
fails = [r for r in rows if r[1]=='READ FAIL']
print("=== READ FAILS:", len(fails))
for r in fails: print(r)
print()
print("voice files:", len(voice))
b = collections.Counter()
for r in voice:
    b['< -50' if r[2]<-50 else '< -40' if r[2]<-40 else '< -30' if r[2]<-30 else '>= -30'] += 1
print(b)
# any amb/sfx/music with issues
other = [r for r in rows if 'assets/audio' in r[0] and r[1]!='READ FAIL']
obad = [r for r in other if r[2] < -55 or r[1] < 0.2]
print("=== SUSPICIOUS SFX/MUSIC/AMB ===")
for r in obad: print(r)
