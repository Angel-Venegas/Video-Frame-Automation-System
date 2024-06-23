**Project Description**
  The Video Frame Automation System is designed to streamline the process of identifying, analyzing, and uploading specific video frames that need attention. The project utilizes Python to automate several manual tasks, including reading proprietary data, parsing video files, generating timecodes, creating thumbnails, and uploading the results to Frame.io for further processing.

**Key Features**
  Automated Script Execution:
    Built an automation script using Python to replace manual positions within seconds.
    The script handles proprietary data from Baselight machines to locate filesystem frames.
  
  Database Integration:
    All requests are saved to a MySQL database for easy data analysis and retrieval.
  
  Data Export:
    Export results in basic CSV format and a XLSX file.
    Includes timecode and thumbnail previews uploaded to Frame.io.


**Components and Dependencies**
  Python Libraries:
    os
    requests
    frameioclient
    pandas
    moviepy.editor
    PIL
    mysql.connector
    argparse
    subprocess
    re
    numpy
    time

  MySQL: Used for storing data from Xytech and Baselight files.
  
  FFmpeg: Utilized for video processing and extracting timecodes.
  
  Frame.io API: For uploading the processed video shots.


**Usage Instructions**
  Setting Up the Database:
  
  Create the database and user by running the following SQL commands
    CREATE DATABASE video_data;
    CREATE USER 'Fix_Me_User'@'localhost' IDENTIFIED BY 'Fix_Me_User_Login123';
    GRANT ALL PRIVILEGES ON video_data.* TO 'Fix_Me_User'@'localhost';
    FLUSH PRIVILEGES;

**Running the Script:**
  Open the integrated terminal in your Python IDE by right clicking main.py since the script uses argparse commands.
  Run the script with the necessary arguments:
  To store Xytech data into the database: python main.py --xytech Xytech.txt
  To store Baselight data into the database: python main.py --baselight Baselight_export.txt
  To process the frame ranges, file swaps, and timecodes of the video file: python main.py --process twitch_nft_demo.mp4
  To process a video file, generate an XLS file, and upload the clips to fix to frame.io (frame ranges only): python main.py --process twitch_nft_demo.mp4 --output frames_to_fix.xlsx


**What The Script Does In Order:**
  --xytech
    1. Inserts workorder number and all of the locations of the Xytech file into the database
  --baselight
    2. From the Baselight file, inserts the folders and their associated frames in order from least to greatest into the database
  --process
    3.
    Steps:
        1. Retrieve the information from the database and store their respected row datas into dictionaries
        
        We want to extract all of the clips that fall into the ranges of frames to fix from the video.
            2. Swap the suffix file locations of baselight in place of the xytech locations
            3. Each file location is associated with frames so make tuples of each swapped file location with a singular corresponding frame and sort all of them from least to greatest.
            4. Then place those sorted frames into ranges and associate them with their corresponding file locations if they incremenet by one and if they dont then they are stand alone.
            5. Get the timecode of the entire video which will be in the format HH:MM:SS.MS (hours:minutes:seconds.milliseconds) because that is what ffmpeg chooses.
            6. Since the video is 60 fps, then for each range, convert the start and end frames into a time code format that matches the format ffmpeg uses to create timecode (HH:MM:SS.MS).
            7. In that same loop, rows are stored in the xls_data list where each row is a string representing the Location---Frames To Fix---Timecode(HH:MM:SS.MS).
  --process and --output
    4.
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

**The Four Manual Positions We Are Automating:**
    --xytech:
        Inserts the workorder number and all locations from the Xytech file into the database.
        **Automation Benefit:** Eliminates the need to manually input workorder numbers and locations into the database, ensuring accuracy and saving time.

    --baselight:
        Inserts the folders and associated frames from the Baselight file into the database, sorted in ascending order.
        **Automation Benefit:** Automates the tedious process of sorting frames and entering them into the database, ensuring data integrity and consistency.

    --process:
        Retrieves and stores database data into dictionaries.
        Swaps Baselight suffix locations with corresponding Xytech locations.
        Creates tuples of swapped file locations and frames, sorting them.
        Groups sorted frames into ranges, associates with file locations.
        Extracts the video’s timecode using FFmpeg.
        Converts frame ranges to timecodes (HH:MM
        .MS) at 60 fps.
        Stores Location, Frames to Fix, and Timecode in a list.
        **Automation Benefit**: Automates the complex process of analyzing and sorting video frames, generating accurate frame ranges, and converting them to timecodes, reducing errors and manual effort.

    --process and --output:
        Writes data to an XLS file with columns for Location, Frames to Fix, Timecode, and Thumbnail.
        Generates thumbnails by calculating the center of each frame range.
        Renders video shots for each frame range.
        Uploads the shots to Frame.io using their API.
        **Automation Benefit:** Streamlines the creation of detailed reports, thumbnail generation, and video shot rendering, as well as automating the upload process to Frame.io, ensuring timely and efficient delivery of processed data.

data_to_csv.py
  Reads data from Xytech and Baselight, processes the data, performs the necessary swaps, sorts the frames and frame ranges in order each associated with a location, and writes the locations with their frames to fix in a csv file called output.csv in ascending order.
