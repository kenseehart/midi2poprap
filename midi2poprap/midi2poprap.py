
'''MIDI to Poprap pdf'''

import argparse
from genericpath import samefile
from posixpath import dirname
import sys
import os
from os.path import basename, splitext, join
from typing import Tuple, List
import json

from mido import Message, MetaMessage, MidiFile, MidiTrack
from PIL import Image, ImageDraw, ImageFont

this_name = splitext(basename(__file__))[0]
this_dir = dirname(this_name)

verbose = False

def vprint(*args, **kwargs):
    if verbose:
        print(*args, file=sys.stderr, **kwargs)

def eprint(*args, **kwargs):
    print(*args, file=sys.stderr, **kwargs)

class NoException(Exception):
    'An exception that never happens (useful for conditionall disabling exception handling)'
    pass



def make_image(pops:List[Tuple[int,int]], cell_size:int, font:str, font_size, x0:int, y0:int) -> Image.Image:
    im = Image.new('1', (2100, 3000), 1)
    draw = ImageDraw.Draw(im) 
    font = ImageFont.truetype(font, font_size)
    popset = set(pops)

    for t in range(1,33):
        yoff = font_size//3
        draw.text((x0, y0+t*cell_size-yoff), f'{t:2d}', font = font, align ="right") 

    for (i, n) in enumerate(['D', 'E', 'F#', 'G', 'A', 'B', 'C#', 'D', 'E', 'F#', 'G', 'A']):
        xoff = font_size*len(n)//4
        draw.text((x0+(i+1)*cell_size-xoff, y0), n, font = font, align ="center") 

    r = int(cell_size*.4)
    rp = int(cell_size*.32)
    for t in range(0,32):
        for i in range(12):
            draw.ellipse([x0+(i+1)*cell_size-r, y0+(t+1)*cell_size-r, x0+(i+1)*cell_size+r, y0+(t+1)*cell_size+r], None, 0)
            if (t,i) in pops:
                draw.ellipse([x0+(i+1)*cell_size-rp, y0+(t+1)*cell_size-rp, x0+(i+1)*cell_size+rp, y0+(t+1)*cell_size+rp], 0, 0)

    im.show() 
    return im


note_names =  ['C', 'C#', 'D', 'D#', 'E', 'F#', 'G', 'G#', 'A', 'A#', 'B']

major = [0,2,4,5,7,9,11,12,14,16]
major_index = {k:i for i, k in enumerate(major)}

def get_scale_note(note:int, tonic:int, nrange:int):
    'return the major scale note index 0:nrange given the midi note value where 0 maps to nkey'
    nc = note-tonic

    try:
        i = major_index[nc]
    except KeyError:
        eprint(f'Warning: {note_names[note%12]} is out of range or out of key. Expected {note_names[tonic%12]} major starting at midi {tonic}')
        return -1
    return i

def midi2pops(mid:MidiFile, tonic:int, nrange:int) -> List[List[int]]:
    'translate midi object to pops list'

    if len(mid.tracks)>1:
        eprint(f'Warning: {midifile} contains {len(mid.tracks)} tracks. Only the first track will be used.')

    track = mid.tracks[0]
    msg:Message
    pops=[] # list of pop coordinates (time index 1-32, note in D Major)
    t:int = 0

    for msg in track:
        vprint(msg)

        if msg.type=='note_on' and msg.velocity>0:

            i = get_scale_note(msg.note, tonic, nrange)
            t += 1
            vprint (t, i)

            if t>32:
                eprint(f'Warning: exceeded 32 time indexes, truncating song')
                break

            pops.append((t,i))

    return pops

def pops2midi(pops:List[List[int]]) -> MidiFile:
    pops.sort()

    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)
    track.append(Message('program_change', program=12, time=0))

    dt=80
    tonic=62
    notes = []
    for (t, n) in pops:
        note = tonic+major[n]
        notes.append((dt*t, 'note_on', note ))
        notes.append((dt*t+dt, 'note_off', note ))

    notes.sort()

    track.append(MetaMessage('key_signature', key='D'))

    t = 0
    for ta, m, note in notes:
        dt = ta-t
        t = ta
        track.append(Message(m, note=note, velocity=64, time=dt))

    return mid


def pops2imagefile(pops, outfile:str):
    img = make_image(pops, 80, 'calibri', 40, 320, 100)

    _, ext = splitext(outfile)
    ext = ext.lower()

    if ext=='.pdf':
        eprint('Sorry, pdf is not yet supported.')
        #save_pdf(img, outfile)
    else:
        img.save(outfile)

def make_sample(midifile:str, outfile:str):
    # Minuet in G, JS Bach  
    pops = [
        (0, 4), (0, 2), (0, 0),
        (2, 0),
        (3, 1),
        (4, 2), (4, 1),
        (5, 1), 
        (6, 4), (6, 2),
        (8, 0),
        (10, 0),
        (12, 5), (12, 3),
        (14, 2),
        (15, 3),
        (16, 4),
        (17, 5),
        (18, 6), (18, 2),
        (20, 0),
        (22, 0),
    ]

    midi:MidiFile = pops2midi(pops)
    midi.save(midifile)

    pops2imagefile(pops, outfile)


def midi2poprap(midifile:str, outfile:str, tonic:int=62, nrange:int=11):
    #create_midi(midifile)
    mid = MidiFile(midifile)
    if len(mid.tracks)>1:
        eprint(f'Warning: {midifile} contains {len(mid.tracks)} tracks. Only the first track will be used.')

    track = mid.tracks[0]
    msg:Message
    pops=[] # list of pop coordinates (time index 1-32, note in D Major)
    t = 0
    t0 = 0

    notes = [] # (time, midi note)
    min_dt = 1000000

    for msg in track:
        vprint(msg)
        t += msg.time
        dt = t - t0
        t0 = t

        if 0<dt<min_dt:
            min_dt = dt

        if msg.type=='note_on' and msg.velocity>0:

            notes.append((t, msg.note))
            
    dt = min_dt

    for (t, note) in notes:
        n = get_scale_note(note, tonic, nrange)
        ti = t/dt

        vprint (ti, n)

        if ti>32:
            eprint(f'Warning: exceeded 32 time indexes, truncating song')
            break

        pops.append((ti, n))

    pops2imagefile(pops, outfile)






def main():
    global verbose

    parser = argparse.ArgumentParser(prog=this_name, description=__doc__)
    parser.add_argument('midi', help='input midi filename')
    parser.add_argument('outfile', help='output png|jpg|tiff filename')
    parser.add_argument('-v', action='store_true', help='show debugging output')
    parser.add_argument('-e', action='store_true', help='raise exception on error')
    parser.add_argument('-s', action='store_true', help='create a sample midi and ouput')

    args = parser.parse_args()
    verbose = args.v
    etype = NoException if args.e else Exception # conditional exception handling

    try:
        if args.s:
            make_sample(args.midi, args.outfile)
        else:
            midi2poprap(args.midi, args.outfile)
    except etype as e: # Best if replaced with explicit exception
        print (e, file=sys.stderr)
        exit(1)

if __name__=='__main__':
    main()

