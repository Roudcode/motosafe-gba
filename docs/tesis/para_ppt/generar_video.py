"""Compose the authored screenshots and typography as an original motion video.

Requires Pillow, numpy and imageio-ffmpeg. No browser, account or remote render.
The original JPGs are never overwritten.
"""
import argparse
import json
import math
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import wave

import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter

sys.path.insert(0, str(Path(tempfile.gettempdir()) / 'motosafe-motion-runtime'))
import imageio_ffmpeg

HERE = Path(__file__).resolve().parent
CFG = json.loads((HERE / 'motion_scenes.json').read_text(encoding='utf-8'))
W, H = CFG['width'], CFG['height']
FPS = CFG['fps']
FONT = Path('C:/Windows/Fonts/segoeui.ttf')
BOLD = Path('C:/Windows/Fonts/segoeuib.ttf')
COLORS = {
    'light': ('#f6f5f0', '#16212b', '#5a6670', '#987000'),
    'yellow': ('#ffd039', '#17212b', '#494838', '#17212b'),
    'dark': ('#101d28', '#f5f5f0', '#b6c1c8', '#ffd039'),
}


def font(size, bold=False):
    return ImageFont.truetype(str(BOLD if bold else FONT), size)


def wrap(text, f, width):
    lines, line = [], ''
    for word in text.split():
        test = (line + ' ' + word).strip()
        if f.getlength(test) > width and line:
            lines.append(line)
            line = word
        else:
            line = test
    if line:
        lines.append(line)
    return lines


def text_layer(text, size, color, width=1800, bold=False):
    f = font(size, bold)
    lines = wrap(text, f, width)
    height = len(lines) * int(size * 1.35) + 14
    img = Image.new('RGBA', (width, height))
    d = ImageDraw.Draw(img)
    for i, line in enumerate(lines):
        d.text((0, i * int(size * 1.35)), line, font=f, fill=color, stroke_width=0)
    return img


def device(file, kind):
    screenshot = Image.open(HERE / file).convert('RGB')
    if kind == 'phone':
        sw, sh, pad, top = 345, round(345 * screenshot.height / screenshot.width), 12, 12
        radius = 44
    else:
        sw, sh, pad, top, radius = 800, round(800 * screenshot.height / screenshot.width), 9, 27, 20
    canvas = Image.new('RGBA', (sw + pad * 2, sh + top + pad))
    d = ImageDraw.Draw(canvas)
    d.rounded_rectangle((0, 0, canvas.width-1, canvas.height-1), radius=radius, fill='#1a2026', outline='#56636f', width=2)
    screenshot = screenshot.resize((sw, sh), Image.Resampling.LANCZOS)
    mask = Image.new('L', (sw, sh), 0)
    ImageDraw.Draw(mask).rounded_rectangle((0, 0, sw, sh), radius=32 if kind == 'phone' else 5, fill=255)
    canvas.paste(screenshot, (pad, top), mask)
    if kind == 'phone':
        d.rounded_rectangle((canvas.width//2-50, 17, canvas.width//2+50, 28), radius=6, fill='#161c22')
    else:
        for x in (24, 45, 66):
            d.ellipse((x, 9, x+7, 16), fill='#9ba5ac')
    return canvas


def ease(v):
    return 1 - (1 - max(0, min(1, v))) ** 3


def over(frame, layer, xy, opacity=1):
    if opacity <= 0:
        return
    if opacity < .998:
        layer = layer.copy()
        layer.putalpha(layer.getchannel('A').point(lambda a: int(a * opacity)))
    frame.paste(layer, (round(xy[0]), round(xy[1])), layer)


def prepare(s):
    bg, fg, muted, accent = COLORS[s['theme']]
    static = Image.new('RGB', (W, H), bg)
    d = ImageDraw.Draw(static)
    d.text((92, 49), 'MotoSafe', font=font(30, True), fill=fg)
    d.rounded_rectangle((250, 54, 309, 85), radius=8, fill='#ffd039')
    d.text((259, 55), 'GBA', font=font(19, True), fill='#17212b')
    # Public-facing caveats stay visible in the video as well as the notes.
    note = text_layer(s['note'], 24, muted, width=1740)
    over(static, note, (92, 921))
    d.text((92, 1031), s['source'], font=font(20), fill=muted)
    kind = s['kind']
    size = 103 if kind == 'phone' else 91 if kind == 'desktop' else 126
    if kind == 'closing':
        size = 178
    if kind == 'numbers':
        size = 85
    max_width = 950 if kind in ('phone', 'desktop') else 1750
    while max(font(size, True).getlength(t) for t in s['title']) > max_width:
        size -= 1
    title_layers = [text_layer(t, size, accent if i == s['accent'] else fg, width=max_width+15, bold=True) for i, t in enumerate(s['title'])]
    title_y = 320 if kind in ('phone', 'desktop') else 270
    if kind in ('closing', 'numbers', 'ux'):
        title_y = 210
    copy_width = 820 if kind in ('phone', 'desktop') else 1650
    sub = text_layer(s['copy'], 34 if kind not in ('phone', 'desktop') else 32, muted, width=copy_width)
    obj = {'static': static, 'title': title_layers, 'title_y': title_y, 'title_size': size, 'sub': sub, 'color': (fg, muted, accent)}
    if s.get('image'):
        obj['device'] = device(s['image'], kind)
    if s.get('metrics'):
        obj['metrics'] = [(text_layer(n, 160, fg, width=800, bold=True), text_layer(l, 33, muted, width=800)) for n, l in s['metrics']]
    if kind == 'ux':
        obj['ux'] = text_layer('4 de 12 compararon rutas y explicaron cobertura sin ayuda', 39, fg, width=1600, bold=True)
    return obj


def render(s, obj, local):
    p = local / s['duration']
    e1, e2 = ease(local / .7), ease((local-.17)/.8)
    frame = obj['static'].copy()
    x = 1070 if s.get('side') == 'left' else 110
    size = obj['title_size']
    y = obj['title_y']
    for i, layer in enumerate(obj['title']):
        e = e1 if i == 0 else e2
        over(frame, layer, (x, y + i * size * 1.13 + 85*(1-e)), e)
    sub_y = y + size*2.3 + 30
    over(frame, obj['sub'], (x, sub_y + 30*(1-e2)), e2)
    if 'device' in obj:
        img = obj['device']
        camera = ease(p)
        # Continuous rotation, lift and close-up reproduce the device motion
        # in the supplied references while retaining the real app capture.
        scale = .92 + .08*camera
        moving = img.resize((round(img.width*scale), round(img.height*scale)), Image.Resampling.BICUBIC)
        angle = (5.0 - 4.0*camera) if s['kind']=='phone' else (3.0 - 2.0*camera)
        moving = moving.rotate(angle, Image.Resampling.BICUBIC, expand=True)
        left = 1340 if s['kind']=='phone' else (62 if s.get('side')=='left' else 1065)
        top = 110 if s['kind']=='phone' else 205
        left += 35*(1-e2) - 18*camera
        top += 125*(1-e2) - 15*math.sin(p*math.pi)
        shadow = Image.new('RGBA', moving.size)
        shadow.putalpha(moving.getchannel('A').point(lambda a: int(a*.18)))
        shadow = shadow.filter(ImageFilter.GaussianBlur(15))
        over(frame, shadow, (left+20, top+28), e2)
        over(frame, moving, (left, top), e2)
    if 'metrics' in obj:
        for k, (number,label) in enumerate(obj['metrics']):
            mx = 110 + k*895
            over(frame, number, (mx, 540+50*(1-e2)), e2)
            over(frame, label, (mx, 740+30*(1-e2)), e2)
    if 'ux' in obj:
        over(frame, obj['ux'], (110, 680+40*(1-e2)), e2)
    return frame


def soundtrack(dest, seconds):
    """Quiet original instrumental bed, synthesized locally, no licensed track."""
    rate = 44100
    length = int(seconds*rate)
    audio = np.zeros(length, dtype=np.float32)
    rng = np.random.default_rng(42)
    beat = .625  # 96 BPM
    chords = [(146.832, 220, 293.665), (130.813,196,261.626), (174.614,261.626,349.228), (164.814,246.942,329.628)]
    for bar in range(math.ceil(seconds / (beat*4))):
        start = int(bar*beat*4*rate)
        dur = min(int(beat*4*rate), length-start)
        tt = np.arange(dur)/rate
        env = np.minimum(tt/.25,1) * np.minimum((dur/rate-tt)/.7,1)
        chord = chords[bar%len(chords)]
        pad = sum(np.sin(2*np.pi*f*tt) for f in chord)/3
        audio[start:start+dur] += (.065*env*pad).astype(np.float32)
        for j in range(8):
            offset = start+int(j*beat*.5*rate)
            n = min(int(.5*rate),length-offset)
            if n <= 0:
                continue
            pt = np.arange(n)/rate
            f = chord[j%3]*2
            audio[offset:offset+n] += (.065*np.exp(-pt*10)*np.sin(2*np.pi*f*pt)).astype(np.float32)
    for k in range(math.ceil(seconds/beat)):
        start = int(k*beat*rate)
        n = min(int(.16*rate),length-start)
        if n<=0:
            continue
        tt=np.arange(n)/rate
        if k%2==0:
            audio[start:start+n] += (.09*np.exp(-tt*28)*np.sin(2*np.pi*(56*tt+2*(1-np.exp(-tt*30))))).astype(np.float32)
        noise = rng.standard_normal(n).astype(np.float32)
        noise[1:] -= noise[:-1].copy()
        audio[start:start+n] += .008*np.exp(-tt*70)*noise
    tt = np.arange(length)/rate
    audio *= np.minimum(tt/1.3,1)*np.minimum((seconds-tt)/2,1)
    audio=np.clip(audio,-.8,.8)
    # A centered mix keeps the presentation clear on mono classroom speakers.
    pcm=(np.column_stack([audio,audio])*32767).astype('<i2')
    with wave.open(str(dest),'wb') as wav:
        wav.setnchannels(2);wav.setsampwidth(2);wav.setframerate(rate);wav.writeframes(pcm.tobytes())


def main():
    ap=argparse.ArgumentParser()
    ap.add_argument('--preview-only',action='store_true')
    args=ap.parse_args()
    private=Path(tempfile.gettempdir())/'motosafe-motion-render'
    private.mkdir(exist_ok=True)
    objects=[prepare(s) for s in CFG['scenes']]
    # One representative still for every scene, plus contact sheet for QA.
    thumbs=[]
    for i,(s,obj) in enumerate(zip(CFG['scenes'],objects)):
        im=render(s,obj,min(2.5,s['duration']/2))
        im.save(private/f'scene_{i+1:02d}.jpg',quality=92)
        thumbs.append(im.resize((480,270),Image.Resampling.LANCZOS))
    sheet=Image.new('RGB',(1920,810),'#111111')
    for i,thumb in enumerate(thumbs):
        sheet.paste(thumb,((i%4)*480,(i//4)*270))
    sheet.save(private/'contact_sheet.jpg',quality=95)
    print(json.dumps({'preview':str(private/'contact_sheet.jpg'),'scenes':len(objects)}),flush=True)
    if args.preview_only:
        return
    seconds=sum(s['duration'] for s in CFG['scenes'])
    audio=private/'soundtrack.wav'
    soundtrack(audio,seconds)
    target=HERE/'MotoSafe_GBA_Motion.mp4'
    ffmpeg=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ffmpeg,'-y','-hide_banner','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-s',f'{W}x{H}','-pix_fmt','rgb24','-r',str(FPS),'-i','-','-i',str(audio),'-map','0:v:0','-map','1:a:0','-c:v','libx264','-preset','fast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','160k','-movflags','+faststart','-shortest',str(target)]
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    for i,(s,obj) in enumerate(zip(CFG['scenes'],objects)):
        for k in range(round(s['duration']*FPS)):
            im=render(s,obj,k/FPS)
            # Brief fade through the next scene's background, not a slideshow
            # dissolve: the next camera composition enters independently.
            remaining=s['duration']-k/FPS
            if remaining<.22 and i<len(objects)-1:
                next_bg=Image.new('RGB',(W,H),COLORS[CFG['scenes'][i+1]['theme']][0])
                im=Image.blend(im,next_bg,ease(1-remaining/.22))
            proc.stdin.write(im.tobytes())
        print(json.dumps({'scene':i+1,'of':len(objects)}),flush=True)
    proc.stdin.close()
    status=proc.wait()
    if status:
        raise RuntimeError(f'ffmpeg exit {status}')
    # Decode the complete final file to check the media bitstream.
    subprocess.run([ffmpeg,'-v','error','-i',str(target),'-f','null','-'],check=True)
    print(json.dumps({'output':str(target),'seconds':seconds,'fps':FPS,'size':target.stat().st_size,'decode':'OK'}),flush=True)


if __name__=='__main__':
    main()
