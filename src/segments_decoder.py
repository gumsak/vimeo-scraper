# -*- coding: utf-8 -*-
"""
Program used to put together video/audio segments, to produce a playable 
video (mp4, avi...)
"""

from __future__ import print_function
import ffmpy
import base64
import os
import subprocess

def cat_segments(segments_directory, segments_extension,
                 has_init_segment, output_name, output_extension, 
                 init_segment_name = None, nb_segments = 0, segments_list=None,
                 segment_patern = 'segment-{}.m4s'):
    
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
        file_to_open = segment_patern.format(str(i+1))
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

    #outfile.close()
    #infile.close()
    
def encode_mp4(input_file, output_file):
    """
    Encodes the given file to .mp4 using FFMPEG (through FFMPY)
    
    file (string): file to encode    
    """
    subprocess.call(['ffmpeg',
                     '-y',
                     '-i',
                     input_file, 
                     '-c', 'copy',
                     output_file])
    
def encode_mp3(input_file, output_file):
    """
        
    input_file : TYPE
    DESCRIPTION.
    output_file : TYPE
    DESCRIPTION.
    """
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
    
def delete_files(extension, directory=''):
    """delete specific files from the given directory
        
    directory : STRING
    (optional) path of the directory to check
    extension : STRING
    extension of the files to delete
            
    Return: None
    """

    for file in os.listdir(directory):
        if file.endswith(extension):
            file_path = os.path.join(directory, file)
                
            try:
                os.remove(file)
            except:
                print("Error while removing file")
    
def combine_files(video_file, audio_file, output_file):
    """join an audio file and a video file to create a new file"""
    
    subprocess.call(['ffmpeg',
                     '-y',
                     '-i',
                     video_file,
                     '-i',
                     audio_file,
                     '-c',
                     'copy',
                     output_file])