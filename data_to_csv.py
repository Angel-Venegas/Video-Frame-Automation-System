import csv

# Read and parse Xytech file
xytech_data = {} # Declaring an empty dictionary
with open('Xytech.txt', 'r') as xytech_file:
    lines = xytech_file.readlines() # method returns a list containing each line in the file as a list item.
    # Extract workorder number, producer, operator, job, locations, and notes
    workorder_number = int(lines[0].split()[-1]) # Gets the last element of the list
    print(f"Workorder Number: {workorder_number}")
    producer = lines[2].split(':')[-1].strip() # strip() will remove any leading and trailing whitespaces for the last element of the list
    print(f"Producer: {producer}")
    operator = lines[3].split(':')[-1].strip()
    print(f"Operator: {operator}")
    job = lines[4].split(':')[-1].strip()
    print(f"Job: {job}")
    locations = [line.strip() for line in lines[7:16]] # Gets 'Location:' and the file paths
    print("Xytech Locations:")
    for location in locations:
        print(location)
    notes = lines[-1].strip() # Last Element is the 'Notes:' Message
    print(f"Notes: {notes}")

    # Store data in dictionary
    xytech_data = {
        'workorder_number': workorder_number,
        'producer': producer,
        'operator': operator,
        'job': job,
        'locations': locations,
        'notes': notes
    }

# Read and parse Baselight file
baselight_data = {}
with open('Baselight_export.txt', 'r') as baselight_file:
    for line in baselight_file:
        # Skips empty lines since if strip() returns an empty string, an empty string evaluates to false
        if not line.strip():
            continue

        parts = line.split()
        # Check if there are enough parts to extract file path (so the path and frame ranges, not just a path)
        if len(parts) >= 1:
            file_path = parts[0]
            # Checking if the second part has only digits for frame numbers to store them in a list
            frame_numbers = [int(frame_num) for frame_num in parts[1:] if frame_num.isdigit()] # for frame_num in parts[1:]: This iterates over each element "frame_num" in parts starting from the second element (index 1) to the end of the list.
            # Append frame_numbers to the dictionary under file_path if file_path already exists in the dictionary
            if file_path in baselight_data:
                baselight_data[file_path].extend(frame_numbers)
            else: # Otherwise add it to the dictionary
                baselight_data[file_path] = frame_numbers
        else:
            print("Warning: Skipping line with insufficient data:", line.strip())

print("\n\nBaselight Data:")
for path, frames in baselight_data.items(): # items() to iterate over key-value
    print("", path, end='')
    for frame in frames:
        print(' ',frame, end='')
    print()

def swap_file_locations(prefix_x, suffix_x, order_of_xytech_locations): # splits baselight's location and finds if it's suffix matches xytech's suffix
    for location_b in baselight_data: # Iterates over baselight's locations
        index_dune2 = location_b.find('/Dune2')
        prefix_b = location_b[0:index_dune2]
        suffix_b = location_b[index_dune2:]

        if suffix_b == suffix_x:
            order_of_xytech_locations[location_b] = prefix_x + suffix_b

def split_xytech_location(location_x, order_of_xytech_locations):
    index_dune2 = location_x.find('/Dune2')
    prefix_x = location_x[0:index_dune2]
    suffix_x = location_x[index_dune2:]

    if swap_file_locations(prefix_x, suffix_x, order_of_xytech_locations) == None:
        return

print('\n\n')
order_of_xytech_locations = {} # To keep track of locations and their order in the Xytech file, key: baselight location key which is associated with the frames as a its value, value: combined location
xytech_locations = xytech_data['locations']
for location_x in xytech_locations[1:]: # 1 to end, iterates over xytech's locations
    split_xytech_location(location_x, order_of_xytech_locations)


print('Swapped Locations:')
for location in order_of_xytech_locations:
    print("Baselight's Location And Key Value: ", end='')
    print(location, baselight_data[location], sep=":> ")
    print("Combined Location In The Order It Appears In Xytech File: ", end='')
    print(order_of_xytech_locations[location], end='-----\n\n')


filename = 'output.csv'

# Write data to the CSV file
with open(filename, 'w', newline='') as csvfile:
    writer = csv.writer(csvfile)

    # Manually specify row and column indices for each data item
    writer.writerow(['Producer', 'Operator', 'Job', 'Notes'])
    writer.writerow([xytech_data['producer'], xytech_data['operator'], xytech_data['job'], xytech_data['notes']])
    writer.writerow([])
    writer.writerow(['Show Location', 'Frames to Fix'])

    # A list to store pairs of location and frame
    location_frame_pairs = []

    # Iterate through each location in order_of_xytech_locations
    for location in order_of_xytech_locations:
        # Iterate through each frame for the current location
        for frame in baselight_data[location]:
            # Append a tuple containing the location and frame to the list
            location_frame_pairs.append((order_of_xytech_locations[location], frame))

    sorted_pairs = sorted(location_frame_pairs, key=lambda pair: pair[1]) # Sort the pairs based on the frames

    print("Frames Sorted Into Pairs (Location, Frame)")
    for pair in sorted_pairs:
        print(pair[0], pair[1])

    print("\n\nFrames Sorted Into Ranges (Location, Frame)")

    # Iterate through sorted pairs
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
            writer.writerow([location, prev_frame])
        else:
            print(f"{location}: {prev_frame}-{next_frame}")
            writer.writerow([location, str(prev_frame) + "-" + str(next_frame)])
        
        i += 1


'''
The .strip() method in Python is used to remove leading and trailing whitespace characters (spaces, tabs, newline characters) from a string. It returns a new string with the whitespace characters removed.

string = "  Hello, world!   "
stripped_string = string.strip()
print(stripped_string)  # Output: "Hello, world!"


can also specify characters to remove

string = "###Hello, world!###"
stripped_string = string.strip("#")
print(stripped_string)  # Output: "Hello, world!"

'''

'''
Xytech is a software used for managing various aspects of production, including scheduling, resource allocation, asset management, budgeting, and billing. 
Also used to do work orders, mark down hours, and to manage employee pay.


Avid Media Composer is used for editing videos, color, audio, and etc...

FilmlightBaselight or Black Magic Resolve is used for color grading the videos.

Baselights have their own file storage (different naming convention then others)

Marks for frames that need to be fixed and find the file path.

Were going to write an import export script. We will import all the files that were marked in the timeline with the work order and send it back to the user.
Swap folder names with Baselight in Xytech.
The second thing were doing is computing frame ranges if it has an increment by one.
At the end export a csv file. Ignore the nulls. The Xytech file paths need to be swapped.
Line by line in the folder for framwe range and ingoring nulls.



'/baselightfilesystem1/Dune2/reel1/partA/1920x1080', '2,3,4,31,32,33,67,68,69,70,122,123,155,1023,1111,1112,1160,1201,1202,1203,1204,1205,1211,1212,1213,1214,1215,1302,1303,1310,1500,5000,5001,5002,5111,5122,5133,5144,5155,5166,6200,6201,6209,6212,6219,6233,6234,6267,6269,6271,6278,6282,6288,6289,6290,6292,6293,6294'
'/baselightfilesystem1/Dune2/reel1/VFX/Hydraulx', '1251,1252,1253,1260,1270,1271,1272,6197,6198,6199,8846'
'/baselightfilesystem1/Dune2/pickups/shot_1ab/1920x1080', '5010,5011,5012,5013,5014'
'/baselightfilesystem1/Dune2/reel1/VFX/Framestore', '6188,6189,6190,6191,8847'
'/baselightfilesystem1/Dune2/reel1/partB/1920x1080', '6409,6410,6411,6413,6450,6666,6667,6668,6670,6671,6680,6681,6682,6683,6684,8845,12011,12021,12031,12041,12051,12111,12121,12131,12141,12200,12211'
'/baselightfilesystem1/Dune2/reel1/VFX/AnimalLogic', '6832,6833,6834,6911,6912,6913,6914'
'/baselightfilesystem1/Dune2/pickups/shot_2b/1920x1080', '10001,10002,10008,11113'


Swapped Locations:
Baselight's Location And Key Value: /baselightfilesystem1/Dune2/reel1/partA/1920x1080:> [2, 3, 4, 31, 32, 33, 67, 68, 69, 70, 122, 123, 155, 1023, 1111, 1112, 1160, 1201, 1202, 1203, 1204, 1205, 1211, 1212, 1213, 1214, 1215, 1302, 1303, 1310, 1500, 5000, 5001, 5002, 5111, 5122, 5133, 5144, 5155, 5166, 6200, 6201, 6209, 6212, 6219, 6233, 6234, 6267, 6269, 6271, 6278, 6282, 6288, 6289, 6290, 6292, 6293, 6294]
Combined Location In The Order It Appears In Xytech File: /hpsans13/production/Dune2/reel1/partA/1920x1080-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/reel1/VFX/Hydraulx:> [1251, 1252, 1253, 1260, 1270, 1271, 1272, 6197, 6198, 6199, 8846]
Combined Location In The Order It Appears In Xytech File: /hpsans12/production/Dune2/reel1/VFX/Hydraulx-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/reel1/VFX/Framestore:> [6188, 6189, 6190, 6191, 8847]
Combined Location In The Order It Appears In Xytech File: /hpsans13/production/Dune2/reel1/VFX/Framestore-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/reel1/VFX/AnimalLogic:> [6832, 6833, 6834, 6911, 6912, 6913, 6914]
Combined Location In The Order It Appears In Xytech File: /hpsans14/production/Dune2/reel1/VFX/AnimalLogic-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/reel1/partB/1920x1080:> [6409, 6410, 6411, 6413, 6450, 6666, 6667, 6668, 6670, 6671, 6680, 6681, 6682, 6683, 6684, 8845, 12011, 12021, 12031, 12041, 12051, 12111, 12121, 12131, 12141, 12200, 12211]
Combined Location In The Order It Appears In Xytech File: /hpsans13/production/Dune2/reel1/partB/1920x1080-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/pickups/shot_1ab/1920x1080:> [5010, 5011, 5012, 5013, 5014]
Combined Location In The Order It Appears In Xytech File: /hpsans15/production/Dune2/pickups/shot_1ab/1920x1080-----

Baselight's Location And Key Value: /baselightfilesystem1/Dune2/pickups/shot_2b/1920x1080:> [10001, 10002, 10008, 11113]
Combined Location In The Order It Appears In Xytech File: /hpsans11/production/Dune2/pickups/shot_2b/1920x1080-----


'''