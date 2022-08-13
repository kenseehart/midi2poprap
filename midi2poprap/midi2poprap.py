
'''MIDI to Poprap pdf'''

import argparse
from genericpath import samefile
from posixpath import dirname
import sys
import os
from os.path import basename, splitext, join
from typing import Tuple, List

from mido import Message, MidiFile, MidiTrack
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
    pass



def create_midi(midifile:str):
    'create a simple midi file for testing'
    mid = MidiFile()
    track = MidiTrack()
    mid.tracks.append(track)

    track.append(Message('program_change', program=12, time=0))
    track.append(Message('note_on', note=64, velocity=64, time=100))
    track.append(Message('note_off', note=64, velocity=127, time=200))
    track.append(Message('note_on', note=66, velocity=64, time=200))
    track.append(Message('note_off', note=66, velocity=127, time=300))
    track.append(Message('note_on', note=68, velocity=64, time=300))
    track.append(Message('note_off', note=68, velocity=127, time=400))

    mid.save(midifile)


def make_image(pops:List[Tuple[int,int]], cell_size:int, font:str, font_size, x0:int, y0:int) -> Image.Image:
    im = Image.new('1', (2100, 3000), 1)
    draw = ImageDraw.Draw(im) 
    font = ImageFont.truetype(font, font_size)
    popset = set(pops)

    for t in range(1,33):
        yoff = font_size//3
        draw.text((x0, y0+t*cell_size-yoff), f'{t:2d}', font = font, align ="right") 

    for (i, n) in enumerate(['D', 'E', 'F#', 'G', 'A', 'B', 'C#', 'E', 'F#', 'G', 'A']):
        xoff = font_size*len(n)//4
        draw.text((x0+(i+1)*cell_size-xoff, y0), n, font = font, align ="center") 

    r = int(cell_size*.4)
    rp = int(cell_size*.32)
    for t in range(1,33):
        for i in range(11):
            draw.ellipse([x0+(i+1)*cell_size-r, y0+t*cell_size-r, x0+(i+1)*cell_size+r, y0+t*cell_size+r], None, 0)
            if (t,i) in pops:
                draw.ellipse([x0+(i+1)*cell_size-rp, y0+t*cell_size-rp, x0+(i+1)*cell_size+rp, y0+t*cell_size+rp], 0, 0)

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

def midi2poprap(midifile:str, outfile:str, tonic:int=60, nrange:int=11):
    #create_midi(midifile)
    mid = MidiFile(midifile)
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

    img = make_image(pops, 80, 'calibri', 40, 320, 100)

    _, ext = splitext(outfile)
    ext = ext.lower()

    if ext=='.pdf':
        eprint('Sorry, pdf is not yet supported.')
        #save_pdf(img, outfile)
    else:
        img.save(outfile)






def main():
    global verbose

    parser = argparse.ArgumentParser(prog=this_name, description=__doc__)
    parser.add_argument('midi', help='input midi filename')
    parser.add_argument('outfile', help='output png|jpg|tiff filename')
    parser.add_argument('-v', action='store_true', help='show debugging output')
    parser.add_argument('-e', action='store_true', help='raise exception on error')

    args = parser.parse_args()
    verbose = args.v
    etype = NoException if args.e else Exception # conditional exception handling

    try:
        r = midi2poprap(args.midi, args.outfile)
    except etype as e: # Best if replaced with explicit exception
        print (e, file=sys.stderr)
        exit(1)

if __name__=='__main__':
    main()

