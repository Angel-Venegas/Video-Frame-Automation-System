'''
Do this on sql so then you could populate the databases:

CREATE DATABASE video_data;
CREATE USER 'Fix_Me_User'@'localhost' IDENTIFIED BY 'Fix_Me_User_Login123';
GRANT ALL PRIVILEGES ON video_data.* TO 'Fix_Me_User'@'localhost';
FLUSH PRIVILEGES;
'''

import os
import requests
from frameioclient import FrameioClient
import pandas as pd
from moviepy.editor import VideoFileClip
from PIL import Image
import mysql.connector
import argparse
import subprocess
import re
import numpy as np
from PIL import Image
import time


connection = mysql.connector.connect(
    host="localhost",
    user="Fix_Me_User",
    password="Fix_Me_User_Login123",
    database="video_data"
)
print("Connected to MySQL server")
print()


# Reads and parses the Xytech file's (The centralized or facility storage) data into a dictionary
xytech_data = {}
def store_xytech_data(xytech_file_path):
    with open('Xytech.txt', 'r') as xytech_file: # The with statement ensures that the file is properly closed after the block of code inside the with statement is executed.
        lines = xytech_file.readlines() # This method returns a list containing each line in the file as a list item.

        # Extracting workorder number, producer, operator, job, locations, and notes
        workorder_number = int(lines[0].split()[-1]) # Splits the words by space and gets the last element in the list
        print(f"Workorder Number: {workorder_number}")
        producer = lines[2].split(':')[-1].strip() # Splits strings by : and strip() will remove any leading and trailing whitespaces for the last element of the list which is a String
        print(f"Producer: {producer}")
        operator = lines[3].split(':')[-1].strip()
        print(f"Operator: {operator}")
        job = lines[4].split(':')[-1].strip()
        print(f"Job: {job}")
        locations = [line.strip() for line in lines[8:16]] # For each line in file lines 9 through 16 (index 8 is inclusive while index 16 is exclusive)
        print("Xytech Locations:")
        for location in locations:
            print(location)
        notes = lines[-1].strip() # Last Element is the 'Notes:' Message
        print(f"Notes: {notes}")

        # Stores the data in dictionary
        xytech_data = {
            'workorder_number': workorder_number,
            'producer': producer,
            'operator': operator,
            'job': job,
            'locations': locations,
            'notes': notes
        }

        # Inserts the data into the database xytech collection
        try:
            cursor = connection.cursor() # This is the cursor object created by calling connection.cursor(). The cursor is used to execute SQL commands and queries.
            
            # Create the 'xytech_collection' table if it does not exist in the database with columns workorder_number and location
            cursor.execute("CREATE TABLE IF NOT EXISTS xytech_collection (workorder_number INT, location TEXT)")
            
            # Inserts the workorder number in the workorder_number column and the locations into the location column of the 'xytech_collection' table
            for location in locations:
                cursor.execute("INSERT INTO xytech_collection (workorder_number, location) VALUES (%s,%s)", (workorder_number, location)) # Executes the query

            # This method is called on a database connection object to save (or commit) all the changes made during the current transaction to the database.
            connection.commit()
            print("Data inserted into the database successfully")

        except mysql.connector.Error as error:
            print("Error:", error)


# Reads and parses the Baselight file's (Local storage) data into a dictionary
baselight_data = {}
def store_baselight_data(baselight_file_path):
    with open('Baselight_export.txt', 'r') as baselight_file:
        for line in baselight_file:
            # Skips empty lines since if strip() returns an empty string, an empty string evaluates to false
            if not line.strip():
                continue

            parts = line.split() # The first part is the location and the rest are frames or errors

            # Checks if there are enough parts to extract file path (so the path and frame ranges, not just a path)
            if len(parts) >= 1:
                file_path = parts[0]
                # Checking if the other parts have only digits for frame numbers to store them in a list
                frame_numbers = [int(frame_num) for frame_num in parts[1:] if frame_num.isdigit()] # This iterates over each element "frame_num" in parts starting from the second element (index 1) to the end of the list and if its a digit, store it in the array as a digit.
                
                if file_path in baselight_data: # The file path is the key and it appends the frame_numbers to the dictionary under file_path if file_path already exists in the dictionary
                    baselight_data[file_path].extend(frame_numbers) # The .extend() method is used with lists to add the elements of an iterable (such as another list, tuple, or string) to the end of the current list. This method modifies the original list in place and does not return a new list.
                else: # Otherwise add the file path to the dictionary
                    baselight_data[file_path] = frame_numbers # Each file path is associated with a single list of frame numbers
            else:
                print("Warning: Skipping line with insufficient data:", line.strip())

        
        try:
            cursor = connection.cursor()

            # Creates the 'baselight_export_collection' table if it does not exist columns folder and frames
            cursor.execute("CREATE TABLE IF NOT EXISTS baselight_export_collection (folder TEXT, frames TEXT)")

            for folder, frames in baselight_data.items(): # For each folder and frames in the dictionary, insert them in their respective columns
                cursor.execute("INSERT INTO baselight_export_collection (folder, frames) VALUES (%s, %s)", (folder, ','.join(map(str, frames)))) # map(str, frames): This applies the str function to each element in the frames list, converting each element to a string. Then the ','.join(...): takes the list of strings produced by map and joins them into a single string, with each element separated by a comma.

            # Commits the transaction
            connection.commit()
            print("Data inserted into the database successfully")

        except mysql.connector.Error as error:
            print("Error:", error)

        finally:
            # Close the database connection
            cursor.close()
print()





'''
    HH: Hours
    MM: Minutes
    SS: Seconds
    FF: Frames (Frames within a second)
'''
def frame_to_timecode_ff(frame, fps=60):
    total_seconds = frame / fps # since it is frames per second
    hours = int(total_seconds / 3600) # we want hours in those seconds
    minutes = int((total_seconds % 3600) / 60)
    seconds = int(total_seconds % 60)
    frames = round((total_seconds * fps) % fps)  # Corrected line
    return "{:02d}:{:02d}:{:02d}:{:02d}".format(hours, minutes, seconds, frames) 
    #"{:02d}:{:02d}:{:02d}:{:02d}"


'''
    HH: Hours
    MM: Minutes
    SS: Seconds
    MS: Milliseconds
'''
def frame_to_timecode_ms(frame, fps=60): # Own timecode method to convert marks to timecode
    total_seconds = frame / fps  # Calculate total seconds
    milliseconds = int(total_seconds * 1000)  # Convert total seconds to milliseconds
    hours = milliseconds // 3600000  # Calculate hours
    minutes = (milliseconds % 3600000) // 60000  # Calculate minutes
    seconds = (milliseconds % 60000) // 1000  # Calculate seconds
    milliseconds %= 1000  # Calculate remaining milliseconds
    return "{:02d}:{:02d}:{:02d}.{:03d}".format(hours, minutes, seconds, milliseconds)

def get_video_timecode(video_file_path): # Time Code Example: 00:01:39.63
    '''
    The duration format provided by ffmpeg is in the form of HH:MM:SS.MS (hours:minutes:seconds.milliseconds):
        HH: Hours
        MM: Minutes
        SS: Seconds
        MS: Milliseconds
    '''
    # Full path to the ffmpeg executable
    ffmpeg_path = r'C:\ProgramData\Microsoft\Windows\Start Menu\Programs\ffmpeg-2024-04-29-git-cf4af4bca0-full_build\bin\ffmpeg.exe'
    
    # Command to run ffmpeg and get time code
    command = [ffmpeg_path, '-i', video_file_path]
    print("Lines In FFMPEG:")
    
    try:
        # Run the command and capture output
        process = subprocess.Popen(command, stderr=subprocess.PIPE, universal_newlines=True)
        
        # Regular expression pattern to match time code in format HH:MM:SS.MS
        time_code_pattern = r'(\d{2}:\d{2}:\d{2}.\d{2})'
        
        # Iterate over the lines of ffmpeg output
        for line in process.stderr:
            # Search for time code in the line
            print(line)
            match = re.search(time_code_pattern, line)
            if match:
                return match.group(1)  # Return the first match found
        
        # If no time code is found, return None
        return None
    except subprocess.CalledProcessError as e:
        print("Error running ffmpeg:", e.output)
        return None  # Error occurred
    
sorted_ranges = [] # Stored ranges only
sorted_locations = {} # Key: is range, Value: is location
def sort_frame_ranges():
    global sorted_ranges
    location_frame_pairs = [] # A list to store pairs of location and frame
    
    # Iterate through each location in order_of_xytech_locations
    for location in order_of_xytech_locations:
        # Iterate through each frame for the current location
        for frame in baselight_data[location]:
            # Append a tuple containing the combined or swapped location and a corresponding singular frame to the list
            location_frame_pairs.append((order_of_xytech_locations[location], frame))

    sorted_pairs = sorted(location_frame_pairs, key=lambda pair: pair[1]) # Sort the pairs based on the frames which will be from least to greatest

    print("Frames Sorted Into Pairs (Location, Frame)")
    for pair in sorted_pairs:
        print(pair[0], pair[1])

    print("\n\nFrames Sorted Into Ranges (Location, Frame)")

    # Iterates through sorted pairs and puts frames that increment by 1 into a range, otherwise make them standalone
    i = 0
    while i < len(sorted_pairs):
        location, frame = sorted_pairs[i]
        
        # Initialize variables to keep track of the range
        prev_frame = frame
        next_frame = frame
        
        # Checks all the consecutive frames
        while i + 1 < len(sorted_pairs) and sorted_pairs[i+1][1] == next_frame + 1:
            next_frame = sorted_pairs[i+1][1] # Move next_frame to the next frame to check
            i += 1
        
        # Print the range
        if prev_frame == next_frame:
            
            print(f"{location}: {prev_frame}")
        else:
            print(f"{location}: {prev_frame}-{next_frame}")
            sorted_ranges.append(f"{prev_frame}-{next_frame}") # Stores sorted ranges only
            sorted_locations[f"{prev_frame}-{next_frame}"] = location # Stores sorted locations only as a value for which its key is the ranges
        
        i += 1

order_of_xytech_locations = {} # To keep track of baselight locations and their order as they appear in the Xytech file, [ key: ] is a baselight location which is a key in baselight_data associated with the frames as a its value, [ value: ] is the swapped location
def swap_locations():
    global order_of_xytech_locations # Dictionary where the key is a baselight location and the value is 
    xytech_locations = xytech_data['locations']  # An array of locations

    # We are iterating over each location in xytech to see if its suffix location matches a suffix location of baselight in order to combine xytech's prefix with baselights suffix
    # and make sure the order that this happens in is in the way that the order of the locations appear in the xytech file.
    # This will simulate file swapping because you are putting baselights location in the position of xytech and we want the baselight location's frames be associated with those locations.
    # Splits xytech locations
    for location_x in xytech_locations: # Iterates over xytech's locations
        index_dune2 = location_x.find('/Dune2') # Finds the position of where this suffix begins
        prefix_x = location_x[0:index_dune2] # Before /Dune2 (/hpsans13/production)
        suffix_x = location_x[index_dune2:] # After /Dune2 (/Dune2/reel1/partA/1920x1080)

        # Splits baselight's location and finds if it's suffix matches xytech's suffix
        for location_b in baselight_data: # Iterates over baselight's locations
            index_dune2 = location_b.find('/Dune2')
            prefix_b = location_b[0:index_dune2] # Before /Dune2 (/baselightfilesystem1)
            suffix_b = location_b[index_dune2:] # After /Dune2 (/Dune2/reel1/partA/1920x1080)

            if suffix_b == suffix_x: # If baselight's suffix folder matches xytech's suffix folder then combine xytech's prefix with baselight's suffix
                order_of_xytech_locations[location_b] = prefix_x + suffix_b # and store it as a value for the baselight full location which is its corresponding key.

def populate_using_database():
    # Initialize xytech_data and baselight_data as a global variable so it can be modified inside the function and as well as anywhere else in the file
    global xytech_data
    global baselight_data

    # Query to retrieve data from the xytech_collection table
    try: # The xytech map only has workorder_number and locations(which are arrays of locations)
        locations = []
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM xytech_collection") # Selects all the rows from the table
        rows = cursor.fetchall() # Is used to fetch all (remaining) rows of a query result, returning a list. If no more rows are available, it returns an empty list.
        for row in rows:
            workorder_number, location = row # The different columns from the row
            
            locations.append(location)

        # Stores the needed data in the dictionary
        xytech_data = {
            'workorder_number': workorder_number,
            'locations': locations
        }

    except mysql.connector.Error as error:
        print("Error:", error)

    # Query to retrieve data from baselight_export_collection table
    try: # Assoiciating unique file paths with their ranges
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM baselight_export_collection")
        rows = cursor.fetchall()
        for row in rows:
            file_path, frames_str = row

            # Split the frames_str by commas and convert each frame number to an integer
            frame_numbers = [int(frame_num) for frame_num in frames_str.split(',') if frame_num.isdigit()]

            # Append frame_numbers to the dictionary under file_path if file_path already exists in the dictionary
            if file_path in baselight_data:
                baselight_data[file_path].extend(frame_numbers)
            else: # Otherwise add it to the dictionary
                baselight_data[file_path] = frame_numbers

    except mysql.connector.Error as error:
        print("Error:", error)

    finally:
        # Close the database connection
        cursor.close()

    # Print the retrieved data
    print("Xytech Data:")
    print('Work Order Number:', xytech_data['workorder_number'])
    print('Locations:')
    for location in xytech_data['locations']:
        print(location)

    print("\n\nBaselight Data:")
    for path, frames in baselight_data.items(): # items() to iterate over key-value
        print("", path, end='')
        for frame in frames:
            print(' ',frame, end='')
        print()

    print('\n')

# python main.py --process twitch_nft_demo.mp4
# process---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
def find_ranges_within_video_length(video_file_path):
    global xls_data
    print(video_file_path)
    print()

    populate_using_database()
    
    swap_locations()

    print('Swapped Locations:')
    for location in order_of_xytech_locations:
        print("Baselight's Location And Key Value: ", end='')
        print(location, baselight_data[location], sep=":> ")
        print("Combined Location In The Order It Appears In Xytech File: ", end='')
        print(order_of_xytech_locations[location], end='-----\n\n')
    
    print('\n')

    sort_frame_ranges()
    print('\n\nSorted Ranges and Ranges Only:')

    for range in sorted_ranges: # Sorted ranges are the frames to fix
        print(range)
    print('\n\n')
    
    # Extract timecode from the video using FFMPEG
    video_time_code = get_video_timecode(video_file_path)
    print('Video Time Code:', video_time_code)


    # This finds all of the ranges in milliseconds which matches ffmpegs format which is what we want
    print('\nAll ranges only that fall in the length of video 60 fps in fromat HH:MM:SS.MS ')

    for range in sorted_ranges:
        frames = range.split('-')
        start_frame = frame_to_timecode_ms(int(frames[0]))
        end_frame = frame_to_timecode_ms(int(frames[1]))

        if (start_frame > video_time_code and end_frame > video_time_code):
            break

        range_to_timecode = f"{start_frame}-{end_frame}"
        fix_info = f"{sorted_locations[range]} {range} {range_to_timecode}\n"
        print(f"{sorted_locations[range]} {range} {range_to_timecode}")

        if fix_info != '\n':
            xls_data.append(fix_info)
        print(range, range_to_timecode)


    # But this file is only for the format of frames and not miliseconds which is what we do not want in the xlsx file
    '''
    print('\nAll ranges only that fall in the length of video 60 fps in fromat HH:MM:SS.FF ')

    with open("ThingsToFix.txt", "w") as fix_file:
        for range in sorted_ranges:
            frames = range.split('-')
            start_frame = frame_to_timecode_ff(int(frames[0]))
            end_frame = frame_to_timecode_ff(int(frames[1]))

            if (start_frame > video_time_code and end_frame > video_time_code):
                break

            range_to_timecode = f"{start_frame}-{end_frame}"
            fix_info = f"{sorted_locations[range]} {range} {range_to_timecode}\n"
            print(f"{sorted_locations[range]} {range} {range_to_timecode}")
            fix_file.write(fix_info)

            if fix_info != '\n':
                xls_data.append(fix_info)

    # Print confirmation message
    print("Information written to ThingsToFix.txt")
    '''
    print("Rows stored in xls_data list where each row is a string representing the Location---Frames To Fix---Timecode(HH:MM:SS.MS)")
    print('\n')
# process^---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
    





# python main.py --process twitch_nft_demo.mp4 --output frames_to_fix.xlsx
# process output (Frame.io)---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
xls_data = []
timecodes_HH_MM_SS_MS = []
def parse_to_xls(xls_file):
    print('\n\nFrame Ranges For Thumbnail Calculations:')
    # Create an empty list to store rows
    rows = []

    # Iterate over xls_data and append each entry to the list of rows
    for row in xls_data:
        location_frames_timecode = row.split()
        timecodes_HH_MM_SS_MS.append(location_frames_timecode[2])
        rows.append({'Location': location_frames_timecode[0],
                     'Frames To Fix': location_frames_timecode[1],
                     'Timecode': location_frames_timecode[2],
                     'Thumbnail': None})  # Initialize the Thumbnail column with None

    # Create a DataFrame from the list of rows
    df = pd.DataFrame(rows)

    # Iterate over each row in the DataFrame to generate thumbnails
    for index, row in df.iterrows():
        output_thumbnail = f"Thumbnails/thumbnail_{index}.png"
        try:
            generate_thumbnail(video_file, output_thumbnail, df.at[index, 'Frames To Fix'])
            # Update the Thumbnail column with the path to the generated thumbnail
            df.at[index, 'Thumbnail'] = output_thumbnail
        except Exception as e:
            print(f"Error generating thumbnail for row {index}: {e}")

    # Write the DataFrame to an Excel file
    with pd.ExcelWriter(xls_file, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)  # Exclude indices
        worksheet = writer.sheets['Sheet1']
        
        # Add the thumbnails to the Excel file
        for index, row in df.iterrows():
            if row['Thumbnail'] is not None:
                worksheet.insert_image(index + 1, df.columns.get_loc('Thumbnail'), row['Thumbnail'])
        
        # Resize each cell to 100x100 pixels
        for col_num in range(len(df.columns)):
            worksheet.set_column(col_num, col_num, 30)  # Set column width
        for row_num in range(len(df) + 1):  # Include header row
            worksheet.set_row(row_num, 100)  # Set row height
# output---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

def generate_thumbnail(video_file, output_thumbnail, frame_ranges):
    # Split the frame ranges
    frames = frame_ranges.split('-')
    print(frames)
    start_frame = int(frames[0])
    end_frame = int(frames[1])

    # Open the video file
    clip = VideoFileClip(video_file)

    # Calculate the middle frame or the frame closest to the middle
    middle_frame = (start_frame + end_frame) // 2
    print('Middle Frame:', middle_frame)

    # Set the time position to the middle frame (in seconds)
    # Calculate the time position in seconds
    time_position = round(middle_frame / clip.fps, 2)  # Round to two decimal places
    print('Time Position:', time_position)

    # Generate the thumbnail at the time position
    clip.save_frame(output_thumbnail, t=time_position)

    # Open the saved thumbnail image
    img = Image.open(output_thumbnail)

    # Resize the thumbnail to 96x74 pixels with antialiasing
    img_resized = img.resize((96, 74), resample=Image.BICUBIC)

    # Save the resized thumbnail
    img_resized.save(output_thumbnail)

    print("Thumbnail generated:", output_thumbnail)

def render_each_shot(video_file):
    print('\n\nTime Codes:', timecodes_HH_MM_SS_MS)
    
    # Create a folder to store the rendered shots
    shots_folder = "Shots To Fix"
    if not os.path.exists(shots_folder):
        os.makedirs(shots_folder)
    
    # Iterate over each timecode range
    for index, time_range in enumerate(timecodes_HH_MM_SS_MS):  # Start index from 0
        start, end = time_range.split('-')
        
        try:
            # Convert timecodes to seconds
            start_sec = timecode_to_seconds(start)
            end_sec = timecode_to_seconds(end)
            
            # Use moviepy to extract the specified shot from the video
            clip = VideoFileClip(video_file).subclip(start_sec, end_sec)
            
            # Construct the output file path for the shot using the frame ranges from sorted_ranges
            shot_name = f"{sorted_ranges[index]}.mp4"
            shot_path = os.path.join(shots_folder, shot_name)
            print(f"Rendering shot {index} to: {shot_path}")  # Debug print
            
            # Write the shot to the shots folder
            clip.write_videofile(shot_path, codec='libx264', audio_codec='aac', audio_bitrate='160k', fps=clip.fps)
            
            # Close the clip to release resources
            clip.close()
            
            print(f"Shot {index} rendered successfully")
        except Exception as e:
            print(f"Error rendering shot {index}: {e}")

def timecode_to_seconds(timecode):
    # Split the timecode into its components
    parts = re.split('[:.]', timecode)
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = int(parts[2])
    milliseconds = int(parts[3])

    total_seconds = (hours * 3600) + (minutes * 60) + seconds + (milliseconds / 1000)
    
    return total_seconds

'''
On Windows terminal type "where python" and navigate to that directory to find client.py:
    C:\\Users\\Administrator\\AppData\\Local\\Programs\\Python\\Python312\\Lib\\site-packages\\frameioclient\\client.py

    # method_whitelist=["POST", "OPTIONS", "GET"]
    allowed_methods =["POST", "OPTIONS", "GET", "PUT", "Delete"]
'''  

def upload_to_frameio():
    ACCESS_TOKEN = ''
    PROJECT_ID = ''
    FOLDER_PATH = 'Shots To Fix'

    headers = {
        'Authorization': f'Bearer {ACCESS_TOKEN}',
        'Content-Type': 'application/json'
    }

    # Get the root asset ID of the project
    project_url = f'https://api.frame.io/v2/projects/{PROJECT_ID}'
    project_response = requests.get(project_url, headers=headers)
    project_data = project_response.json()
    root_asset_id = project_data['root_asset_id']

    def upload_files_to_frameio(folder_path, parent_asset_id):
        for filename in os.listdir(folder_path):
            file_path = os.path.join(folder_path, filename)
            if os.path.isfile(file_path):
                print(f"Uploading {filename} to Frame.io")
                try:
                    # Check if file size is zero
                    file_size = os.path.getsize(file_path)
                    if file_size == 0:
                        print(f"Skipping {filename} due to zero file size.")
                        continue

                    # Create asset in Frame.io
                    create_asset_url = 'https://api.frame.io/v2/assets'
                    payload = {
                        'parent_id': parent_asset_id,
                        'name': filename,
                        'filetype': 'video/mp4',
                        'filesize': file_size,
                        'type': 'file'
                    }
                    create_asset_response = requests.post(create_asset_url, headers=headers, json=payload)
                    create_asset_data = create_asset_response.json()

                    if create_asset_response.status_code == 201:
                        asset_id = create_asset_data['id']
                        
                        # Upload file to the asset
                        upload_url = f'https://api.frame.io/v2/assets/{asset_id}/children'
                        with open(file_path, 'rb') as f:
                            upload_response = requests.put(upload_url, headers=headers, data=f)
                            if upload_response.status_code == 200:
                                print(f"Successfully uploaded {filename}")
                            else:
                                print(f"Failed to upload {filename}: {upload_response.status_code}")
                    else:
                        print(f"Failed to create asset for {filename}: {create_asset_response.status_code}")
                except Exception as e:
                    print(f"Error uploading {filename}: {str(e)}")

    # Upload all files in the specified folder
    upload_files_to_frameio(FOLDER_PATH, root_asset_id)
                




'''
In the context of the argparse module in Python, double dashes (--) are used to denote optional arguments (also known as flags or options) in the command-line interface. These optional arguments allow users to specify values for these options when running a script from the command line.

Double Dashes (--) for Optional Arguments
Double Dashes: When defining command-line options, double dashes are used to distinguish optional arguments from positional arguments.
Optional Arguments: These are not required for the script to run, but they provide additional functionality or specify certain behaviors.
'''
# Define argparse commands
parser = argparse.ArgumentParser(description='Populate baselight and xytech databases.')
parser.add_argument('--xytech', help='Path to xytech file') # Inserts workorder number and all of the locations into the database
parser.add_argument('--baselight', help='Path to baselight file') # Inserts the folders and their associated frames in order from least to greatest into the database
parser.add_argument('--process', help='Path to video file') # Generates output to the console to make sure that everything is being processed correctly (correct file swaps, frame range generation, frame range to time code, correct info being stored in lists, dictionaries, and tuples)
parser.add_argument('--output', help='Path to the XLS file that will be used to export the clips to fix')
args = parser.parse_args()

# Call respective functions based on user input
if args.xytech:
    store_xytech_data(args.xytech) # Inserts workorder number and all of the locations into the database
elif args.baselight:
    store_baselight_data(args.baselight) # Inserts the folders and their associated frames in order from least to greatest into the database
elif args.process:
    '''
    Steps:
        1. Retrieve the information from the database and store their respected row datas into dictionaries
        
        We want to extract all of the clips that fall into the ranges of frames to fix from the video.
            2. Swap the suffix file locations of baselight in place of the xytech locations
            3. Each file location is associated with frames so make tuples of each swapped file location with a singular corresponding frame and sort all of them from least to greatest.
            4. Then place those sorted frames into ranges and associate them with their corresponding file locations if they incremenet by one and if they dont then they are stand alone.
            5. Get the timecode of the entire video which will be in the format HH:MM:SS.MS (hours:minutes:seconds.milliseconds) because that is what ffmpeg chooses.
            6. Since the video is 60 fps, then for each range, convert the start and end frames into a time code format that matches the format ffmpeg uses to create timecode (HH:MM:SS.MS).
            7. In that same loop, rows are stored in the xls_data list where each row is a string representing the Location---Frames To Fix---Timecode(HH:MM:SS.MS).
    '''
    find_ranges_within_video_length(args.process)
    video_file = args.process

    if args.output:
        '''
            Steps:
                We want to generate an xlsx file with columns Location(Swapped Locations Which Points To The Facility Storage), Frames To Fix(Only Includes Ranges To Fix), 
                Timecode(HH:MM:SS:MS), and Thumbnail(The center of each frame range) with the corresponding datas for each row. After that we want to render each of the shots
                that fall within the frame range timecode and upload them to frame.io using their API.
                    1. Write the required columns and rows into the xls file.
                    2. Determine the thumbnail for each of the clips by calculating the center of each of the frame ranges and then dividing it by the clip's fps and using that value
                       to aquire the time position of the clip and using that position to extract a thumbnail from the clip.
                    3. That thumbnail is then resized and added to the xlsx file.
                    4. After that render each of the shots that fall in the generated timecodes (frame ranges are converted to video time code by using the video fps=60)
                    5. Lastly, iterate over all of the shots to fix and upload them to frame.io using their API.
        '''
        xls_file = args.output
        print(xls_file)
        parse_to_xls(xls_file)
        render_each_shot(video_file)
        print('\n\nUploading to frame.io:')
        upload_to_frameio()
   
else:
    print("Please provide either --xytech or --baselight or --process or (--process video --output file.xls) argument.")

# Open this file in the integrated terminal by right clicking and selecting it (main.py)
# python main.py --xytech Xytech.txt
# python main.py --baselight Baselight_export.txt
# python main.py --process twitch_nft_demo.mp4
# python main.py --process twitch_nft_demo.mp4 --output frames_to_fix.xlsx
 

'''
The error message indicates that the file 'Rendering/Xytech.txt' could not be found. This error commonly occurs due to the script's current working directory (CWD) being different from the directory where the file is located.

When you specify a file path like 'Rendering/Xytech.txt', Python will look for the file relative to the current working directory, not the directory where the Python script is located.

That's why you open this file in integrated terminal to begin reading from its current directory.
'''
