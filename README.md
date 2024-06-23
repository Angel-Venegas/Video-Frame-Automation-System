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
To store Xytech data:
