# -*- coding: utf-8 -*-
"""
Program used to put together video/audio segments, to produce a playable 
video (mp4, avi...). 
Uses ffmpy to exectue FFmpeg commands: 
    https://ffmpy.readthedocs.io/en/latest/ffmpy.html
    
TODO: set more secured names for the temp files to avoid deleting a user's video
"""

from __future__ import print_function
import ffmpy
import base64
import os
import fnmatch

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
    
    #cat all the segments in order
    #ref: https://stackoverflow.com/a/58575327
    for i in range (0, nb_segments):
        file_to_open = segment_pattern.format(str(i+1))
        full_path = os.path.join(segments_directory, file_to_open)
        
        #if full_path.endswith(segments_extension):
        print(full_path)
        with open(full_path, "rb") as infile:
            out.write(infile.read())
            infile.close()
         
    out.close()
    
def cat_files(segments_directory, init_file, segment_file,
              output_name, output_extension = ''):
    """
    Concatenate 2 specific files (an init file and a file containing the rest 
    of the files/segments put together)

    segments_directory (string): directory containing the downloaded segments 
    (ex: '/videos/')
        
    init_file (string): name of the file containing the initial segment 
        
    segment_file (string): name of the file containing the rest of the segments
        
    output_name (string): name of the output file; resulting on the concatenation 
    of the init file and segment file
        
    output_extension (string): (optional) file extension type; useless if it 
    is already put in the output_name (will lead to an error actually)
    """
    output_file = segments_directory + output_name + output_extension
            
    out = open(output_file, "ab")
    
    #decode the initial segment (must be the 1st element of the segments list)
    f = open(segments_directory + init_file, "rb")  
    base64.decode(f, out) 
    f.close()
    
    segment = open(segments_directory + segment_file, "rb")  
    out.write(segment.read())
    segment.close()

    out.close()
    
def encode_mp4(input_file, output_file):
    """
    Encodes the given file to .mp4 using FFMPEG (through FFMPY)
    
    file (string): file to encode    
    """

    ff = ffmpy.FFmpeg(inputs= {input_file:None},
                 outputs= {output_file:'-c copy'}, 
                 global_options = ('-y')
                 )
    ff.run()
    
def encode_mp3(input_file, output_file, ffmpeg_path= 'ffmpeg'):
    """
    Encode a binary sound file to produce an mp3 file 
    
    input_file : (binary) audio file to encode
    
    output_file : name of the mp3 file generated (add file extension in name)
    
    ffmpeg_path (string): (optional) path to your ffmpeg exec - '/usr/bin/ffmpeg' 
    is the standard path and it is generally included in your $PATH
    """
    
    ff = ffmpy.FFmpeg(executable= ffmpeg_path, 
                 inputs= {input_file:None},
                 outputs= {output_file:'-y -vn -ar 44100 -ac 2 -b:a 192k'}, 
                 global_options = ('-y')
                 )
    ff.run()
    
def delete_files(directory=''):
    """Delete specific files from the given directory
    
    extension (string list): extension of the files to delete
    
    directory (string): (optional) path of the directory to check
    """
         
    for file in os.listdir(directory):
        #for extension_type in extensions:
            
        #if file.endswith(extension_type):
        if fnmatch.fnmatch(file, '*.m4s') or fnmatch.fnmatch(file, '*.txt'):
            #file_path = os.path.join(directory, file)
            try:
                os.remove(directory + file)
            except:
                print("Error while removing file")
          
        if fnmatch.fnmatch(file, 'tmp.mp*') or fnmatch.fnmatch(file, 'fin.mp*'):
            try:
                os.remove(directory + file)
            except:
                print("Error while removing file")
                                    
def delete_file_pattern(file_list, directory=''):
    """Delete specific files from the given directory
    
    file_list (string list): pattern of the files to delete
    
    directory (string): (optional) path of the directory to check
    """
         
    for file in os.listdir(directory):
        for pattern in file_list:
            
            if fnmatch.fnmatch(file, pattern):
                try:
                    os.remove(directory + file)
                except:
                    print("Error while removing file")
                                    
def combine_files(video_file, audio_file, output_file):
    """Join an audio file & a video file to create a new video file with sound"""

    ff = ffmpy.FFmpeg(inputs= {video_file:None, audio_file:None},
                 outputs= {output_file:'-c copy'}, 
                 global_options = ('-y')
                 )
    ff.run()