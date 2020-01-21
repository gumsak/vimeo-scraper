# -*- coding: utf-8 -*-
"""
Program used to put together video/audio segments, to produce a playable 
video (mp4, avi...)
"""

import ffmpy
import base64
import os
import subprocess

def cat_segments(segments_directory, segments_list, segments_extension,
                 has_init_segment, output_name, output_extension):
    
    output = output_name + output_extension
    
    initial_segment = ''
    
    #decode the initial segment (must be the 1st element of the segments list)
    if has_init_segment:
        f = open(segments_directory + segments_list[0], "r")
        out = open(segments_directory + output, "w+")
        base64.decode(f, out)
       
        f.close()
        out.close()
        
        #os.system('cat ' +  + ' *' + segments_extension + '>>')

    """ref: https://www.geeksforgeeks.org/python-program-to-merge-two-files-into-a-third-file/"""
    with open(segments_directory + output, "w+") as outfile:
        for file_segment in os.listdir(segments_directory):
            if file_segment.endswith(segments_extension):
                with open(file_segment) as infile:
                    
                    outfile.write(infile.read())
    
    def encode_mp4(file):
        
        ff = ffmpy.FFmpeg(inputs={file: None},
                          outputs={file: None}
                          )
        ff.run()
    
    def encode_mp3(input_file, output_file):
        """
        

        Parameters
        ----------
        input_file : TYPE
            DESCRIPTION.
        output_file : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        """
        subprocess.call(['ffmpeg',
                         '-i',
                         input_file,
                         '-codec:a',
                         'libmp3lame',
                         '-qscale:a',
                         '2',
                         output_file])
    
    def delete_files(directory = '', extension):
        """delete specific files from the given directory
        
        Parameters
        ----------
        directory : STRING
            (optional) path of the directory to check
        extension : STRING
            extension of the files to delete

        """

        for file in os.listdir(directory):
            if file.endswith(extension):
                file_path = os.path.join(directory, file)
                
                try:
                    os.remove(file)
                except:
                    print("Error while removing file")
    
def put_together(video_file, audio_file, output_file):
    """join an audio file and a video file to create a new file"""
    
    subprocess.call(['ffmpeg',
                     '-i',
                     video_file,
                     'i',
                     audio_file,
                     '-c',
                     'copy',
                     output_file])