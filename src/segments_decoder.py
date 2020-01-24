# -*- coding: utf-8 -*-
"""
Program used to put together video/audio segments, to produce a playable 
video (mp4, avi...). 
Uses ffmpy to exectue FFmpeg commands: 
    https://ffmpy.readthedocs.io/en/latest/ffmpy.html
"""

from __future__ import print_function
import ffmpy
import base64
import os
import subprocess

def cat_segments(segments_directory, segments_extension,
                 has_init_segment, output_name, output_extension, 
                 init_segment_name = None, nb_segments = 0, segments_list=None,
                 segment_pattern = 'segment-{}.m4s'):
    """
    Concatenate multiple files together.

    Parameters
    ----------
    segments_directory (string): directory of the files to concatenate
    
    segments_extension (string): extension of the files to concatenate
    
    has_init_segment (boolean): define whether or not an initial file/segment
    has to be treated first
    
    output_name (string): name of the file produced by the concatenation
    
    output_extension (string): extension of the produced file
    
    init_segment_name (string): (optional) name of the initial file/segment. 
    The default is None.
    
    nb_segments (int): (optional) amount of files to handle. The default is 0.
        
    segments_list [NOT IMPLEMENTED] : (optional) list of files to handle. The 
    default is None.
        
    segment_pattern (string): (optional) patern/name of the files to handle. 
    The default is 'segment-{}.m4s'.
    """
    output_file = segments_directory + output_name + output_extension
            
    out = open(output_file, "ab")
    
    #decode the initial segment (must be the 1st element of the segments list)
    if has_init_segment:
        f = open(segments_directory + init_segment_name, "rb")
        
        base64.decode(f, out)
       
        f.close()
        
        #os.system('cat ' +  + ' *' + segments_extension + '>>')

    """ref: https://www.geeksforgeeks.org/python-program-to-merge-two-files-into-a-third-file/"""
    
    '''
    with open(segments_directory + output_file, "ab") as outfile:
        for file_segment in os.listdir(segments_directory):
            if file_segment.endswith(segments_extension):
                with open(file_segment, "rb") as infile:
                    
                    outfile.write(infile.read())
    '''
    
    #cat all the segments in order
    #ref: https://stackoverflow.com/a/58575327
    
    #segments_file = 'final.m4s'
    #m4s_file = open(segments_directory + segments_file, "a")
    
    for i in range (0, nb_segments):
        file_to_open = segment_pattern.format(str(i+1))
        full_path = os.path.join(segments_directory, file_to_open)
        
        #if full_path.endswith(segments_extension):
        print(full_path)
        with open(full_path, "rb") as infile:
            out.write(infile.read())
            infile.close()
    
    """
    make sure to get the correct path
    ref:
        https://stackoverflow.com/a/53296655
    & 
        https://stackoverflow.com/a/26065676
    """
    """
    for file_segment in os.listdir(segments_directory):
        full_path = os.path.join(segments_directory, file_segment)
        
        if full_path.endswith(segments_extension):
            print(full_path)
            with open(full_path, "rb") as infile:
                out.write(infile.read())
                infile.close()
    """       
    out.close()
    
def encode_mp4(input_file, output_file):
    """
    Encodes the given file to .mp4 using FFMPEG (through FFMPY)
    
    file (string): file to encode    
    """
    
    '''
    subprocess.call(['ffmpeg',
                     '-y',
                     '-i',
                     input_file, 
                     '-c', 'copy',
                     output_file])
    '''
    ff = ffmpy.FFmpeg(inputs= {input_file:None},
                 outputs= {output_file:'-c copy'}, 
                 global_options = ('-y')
                 )
    ff.run()
    
def encode_mp3(input_file, output_file):
    """
    Encode a binary sound file to produce an mp3 file 
    
    input_file : (binary) audio file to encode
    
    output_file : name of the mp3 file generated (add file extension in name)
    """
    
    ff = ffmpy.FFmpeg(executable= '/usr/bin/ffmpeg', 
                 inputs= {input_file:None},
                 outputs= {output_file:'-y -vn -ar 44100 -ac 2 -b:a 192k'}, 
                 global_options = ('-y')
                 )
    ff.run()
    
    """
    subprocess.call(['ffmpeg',
                         '-i',
                         input_file,
                         '-codec:a',
                         'libmp3lame',
                         '-qscale:a',
                         '2',
                         output_file])
    """
    
    """
    #ref https://stackoverflow.com/a/12952172
    subprocess.call(['/usr/bin/ffmpeg',
                     '-y',
                         '-i',
                         input_file,
                         '-vn',
                         '-ar',
                         '44100',
                         '-ac',
                         '2',
                         '-b:a',
                         '192k',
                         output_file])
    """
    
def delete_files(extension, directory=''):
    """Delete specific files from the given directory
    
    extension (string): extension of the files to delete
    
    directory (string): (optional) path of the directory to check
    """

    for file in os.listdir(directory):
        if file.endswith(extension):
            file_path = os.path.join(directory, file)
                
            try:
                os.remove(file)
            except:
                print("Error while removing file")
    
def combine_files(video_file, audio_file, output_file):
    """Join an audio file & a video file to create a new video file with sound"""
    
    """
    subprocess.call(['ffmpeg',
                     '-y',
                     '-i',
                     video_file,
                     '-i',
                     audio_file,
                     '-c',
                     'copy',
                     output_file])
    """

    ff = ffmpy.FFmpeg(inputs= {video_file:None, audio_file:None},
                 outputs= {output_file:'-c copy'}, 
                 global_options = ('-y')
                 )
    ff.run()