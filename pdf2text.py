from datetime import datetime
from tqdm import tqdm
import os
import shutil
import argparse
import re
import csv
import easyocr
import cv2
import fitz
import aspose.pdf as ap
from PyPDF2 import PdfReader, PdfWriter

def check_rotation(file):
    reader = PdfReader(file)
    writer = PdfWriter()
    oriantation = reader.pages[0].get('/Rotate')
    
    if oriantation == 90 :
        for page in reader.pages:
            # page.rotate_clockwise(270) # (before pypdf3.0 - deprecated - thanks to Maciejg for the update)
            page.rotate(270)
            writer.add_page(page)
        with open("temp.pdf", "wb") as pdf_out:
            writer.write(pdf_out)
        file = "temp.pdf"

    return file

parser = argparse.ArgumentParser(
    description="Process PDF files of NJPD Crash Reports to return wanted values."
)
parser.add_argument("pdf_file", metavar="file", help="path to file")
parser.add_argument("user_id", metavar="user_id", help="current user id")

args = parser.parse_args()
file = args.pdf_file
user_id = args.user_id

# file = "WeekofDec23,2022MVAOPRA.pdf"
# user_id = "1"

doc = ap.Document(file)

file = check_rotation(file)


# if "/" in file:
#     output_name = file[:-4].replace("/", "_")
# elif "\\" in file:
#     output_name = file[:-4].replace("\\", "_")
output_name = os.path.splitext(os.path.basename(file))[0].replace("/", "_").replace("\\", "_")

pdf = fitz.open(file)


page = pdf[0]
textpage = page.get_text()

folder = "png"
for filename in os.listdir(folder):
    file_path = os.path.join(folder, filename)
    try:
        if os.path.isfile(file_path) or os.path.islink(file_path):
            os.unlink(file_path)
        elif os.path.isdir(file_path):
            shutil.rmtree(file_path)
    except Exception as e:
        print("Failed to delete %s. Reason: %s" % (file_path, e))

# -------------- TEXT ------------- #


def check_for_dash(element):
    element = element.replace(" ", "")

    setlist = []
    for n in range(len(element)):
        setlist.append(element[n])

    setlist = list(set(setlist))

    if len(setlist) == 1:
        return False
    else:
        return True


def page_check_text(page):
    page.set_cropbox(fitz.Rect(0, 0, 120, 50))
    text = page.get_text().rstrip().split("\n")

    if "1" in text or "3" in text:
        return True
    else:
        return False


def get_date_text(page):
    page.set_cropbox(fitz.Rect(60, 90, 140, 150))
    text = page.get_text()

    try:
        date = re.search(r"\d{2}\s*\d{2}\s*\d{2}", text)[0]
        date = str(datetime.strptime(date, "%m %d %y").date())
    except:
        date = "|---|"

    return date


def get_upper_boxes_text(page):
    page.set_cropbox(fitz.Rect(537, 22, 580, 110))

    text = page.get_text()
    # print(text, 'text____')
    text = re.sub("[^0-9-\n]", "", text).split("\n")
    # print(text, 'text+____final')
    # print(len(text), 'text_____length')
    boxes = list(filter(None, text))
    # print(len(boxes), 'boxes')

    while len(boxes) < 4:
        boxes.append("|---|")
    # print(boxes, 'append boxes')

    
    return boxes


def get_driver_text(page, driver):
    if driver == 1:
        page.set_cropbox(fitz.Rect(53, 148, 285, 230))
    else:
        page.set_cropbox(fitz.Rect(293, 150, 545, 224))

    text = page.get_text().rstrip().strip().split("\n")
    # print(text, 'text')

    # if len(set(text[0])) == 1:
    #     print('if len')
    #     return ["Unknown", "Unknown"]

    if text == [""]:
        # print('if drive')
        return ["Unknown", "Unknown"]

    if any("unknown" in item.lower() for item in text):
        driver = ["Unknown", "Unknown"]
        # print('if unkonwn')
    else:
        if len(text) > 8:
            # print('if else')
            driver = [" ".join([text[7], text[8]]), ", ".join([text[6]])]
            # print(driver, 'Name____DRIVE')
        elif len(text) > 6:
            driver = [" ".join([text[6], text[3]]), ", ".join([text[5]])]
            # print(driver, 'Name____DRIVE')
        elif len(text) > 5:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            # print(driver, 'Name____DRIVE')   
        elif len(text) > 4:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            # print(driver, 'Name____DRIVE')   
        elif len(text) > 3:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            # print(driver, 'Name____DRIVE') 
        elif len(text) > 2:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            # print(driver, 'Name____DRIVE')   
    if isinstance(driver, int):
        driver = ["----", "----"]  # Assign a default value when driver is an integer
        # print(driver, ' driver is integer')
    else:
        for n in range(len(driver)):
            if driver[n].count("-") > 8:
                driver[n] = "----"
                # print(driver[n], ' driver[n]')               
    # for n in range(len(driver)):
    #     if driver[n].count("-") > 15:
    #         driver[n] = "----"
    #         print( driver[n], ' driver[n]')

    return driver


def get_occupants_text(page):
    page.set_cropbox(fitz.Rect(335, 620, 580, 760))

    text = page.get_text().rstrip().split("\n")
    # print(text, 'text_____occupants')

    occupants = [element for element in text if check_for_dash(element)]
    
    occupants = [x + " " + y for x, y in zip(occupants[0::2], occupants[1::2])]
   



    while len(occupants) < 4:
        occupants.append("|---|")
    # print(occupants, 'occupants__appened')    

    return occupants if occupants else []


def pdf_to_text(pdf):

    case_dict = {}
    case_count = 0
    
    for n in tqdm(range(len(pdf))):

        page = pdf[n]

        page_check = page_check_text(page)

        if not page_check:
            continue

        case_count += 1

        date = get_date_text(page)

        boxes = get_upper_boxes_text(page)

        driver_one = get_driver_text(page, 1)

        driver_two = get_driver_text(page, 2)

        # cities = get_driver_one_ocr(page, page_size, 1)
        # print(cities, 'cities___')

        occupants = get_occupants_text(page)

        case = {
            "Page Number": n + 1,
            "Date": date,
            "118a": "--",
            "118b": "--",
            "119a": "--",
            "119b": "--",
            "Driver 1": driver_one[0],
            "Address 1": driver_one[1],
            "Driver 2": driver_two[0],
            "Address 2": driver_two[1],
            "Occupant 1": "--",
            "Occupant 2": "--",
            "Occupant 3": "--",
            "Occupant 4": "--",
            # "City 1": cities[0],
        }
        if len(occupants) >= 1:
            case["Occupant 1"] = occupants[0]
        if len(occupants) >= 2:
            case["Occupant 2"] = occupants[1]
            # print(case["Occupant 2"], 'case["Occupant 2"]')
        # if len(occupants) >= 2:
        #     occupant_info = occupants[1].split("-")[1] if len(occupants[1].split("-")) > 1 else ""
        #     case["Occupant 2"] = occupant_info
        #     print(case["Occupant 2"], 'case["Occupant 2"]')
    
        if len(occupants) >= 3:
            case["Occupant 3"] = occupants[2]
        if len(occupants) >= 4:
            case["Occupant 4"] = occupants[3]    

        if len(boxes) >= 7:
            # print('case 7')
            case7 = case.copy()
            case7["118a"] = boxes[2] if len(boxes) >= 7 and boxes[2] != "----" else "--"
            case7["118b"] = boxes[3] if len(boxes) >= 7 and boxes[3] != "----" else "--"
            case7["119a"] = boxes[4] if len(boxes) >= 7 and boxes[4] != "----" else "--"
            case7["119b"] = boxes[5] if len(boxes) >= 7 and boxes[5] != "----" else "--"
            case_dict[case_count] = case7

        elif len(boxes) >= 6:
            # print('case 6')
            case6 = case.copy()
            case6["118a"] = boxes[1] if len(boxes) >= 6  and boxes[1] != "----" else "--"
            case6["118b"] = boxes[2] if len(boxes) >= 6 and boxes[2] != "----" else "--"
            case6["119a"] = boxes[3] if len(boxes)>= 6 and boxes[3] != "----" else "--"
            case6["119b"] = boxes[4] if len(boxes) >= 6 and boxes[4] != "----" else "--"
            case_dict[case_count] = case6

        elif len(boxes) >= 5:
            # print('case 5')
            case5 = case.copy()
            case5["118a"] = boxes[0] if len(boxes) >= 5 and boxes[0] != "----" else "--"
            case5["118b"] = boxes[1] if len(boxes) >= 5 and boxes[1] != "----" else "--"
            case5["119a"] = boxes[2] if len(boxes) >= 5 and boxes[2] != "----" else "--"
            case5["119b"] = boxes[3] if len(boxes) >= 5 and boxes[3] != "----" else "--"
            case_dict[case_count] = case5
 
    return case_dict

def check_pdf(page, reader, page_size):
    if page_size == 1:
        # page.set_cropbox(fitz.Rect(160, 20, 400, 50))
        # page.set_cropbox(fitz.Rect(63, 160, 315, 252))
        page.set_cropbox(fitz.Rect(180, 20, 300, 72))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(738, 144, 765, 300))
    # print(page_size)
    pix = page.get_pixmap(dpi=300)
    pix.save("page-0.png")

    image = cv2.imread("page-0.png")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    # (h, w) = gray.shape
    # if h > w:
    #     gray = cv2.rotate(gray, cv2.ROTATE_90_COUNTERCLOCKWISE)


    pdf_check = reader.readtext(gray, decoder="greedy", detail=0, paragraph=False, rotation_info=[90])

    if any("new jersey" in s.lower() or "new_jersey" in s.lower() or "jersey" in s.lower() for s in pdf_check):
        return True
    else:
        return False


def get_date_ocr(page, reader, page_size):
    if page_size == 1:
        # page.set_cropbox(fitz.Rect(70, 100, 130, 135))
        page.set_cropbox(fitz.Rect(70, 100, 150, 155))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(710, 185, 735, 390))

    pix = page.get_pixmap(dpi=300)
    pix.save("png/date-%i.png" % page.number)

    image = cv2.imread("png/date-%i.png" % page.number)
    date_ocr = reader.readtext(image, decoder="greedy", detail=0, paragraph=False, rotation_info=[90])
    lower_result = [x.lower() for x in date_ocr]

    if len(lower_result) == 1:
        lower_result = lower_result[0].split(" ")

    if any("yy" in s for s in lower_result):
        for i in lower_result:
            if "yy" in i:
                year_index = lower_result.index(i)
                date = lower_result[year_index + 1]
            else:
                continue
    elif any("/" in x for x in lower_result):
        for n in lower_result:
            if "/" in n:
                date = "24/03/2023"
                date = re.search(r"\d*/{1}\d*/{1}\d*", date)[0]
                return date
    else:
        date = "N/A"

    return date


def get_boxes_ocr(page, reader, page_size):
    if page_size == 1:
        # page.set_cropbox(fitz.Rect(537, 22, 568, 105))
        page.set_cropbox(fitz.Rect(537, 22, 598, 115))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(635, 540, 730, 570))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/boxes-%i.png" % page.number)

    image = cv2.imread("png/boxes-%i.png" % page.number)
    box_ocr = reader.readtext(
        image,
        decoder="greedy",
        # detail=0,
        # paragraph=True,
        y_ths=0.1,
        x_ths=0.1,
        allowlist="ab1234567890-",
    )
    processed_boxes = []
    
    height_max = 0
    update_text_box = []
    for each_box in box_ocr:
        bbox, text,_ = each_box
        x_min, y_min, x_max, y_max = bbox
        height = y_max[1] - y_min[1]
        if height_max < height:
            height_max = height
        update_text_box.append((height, text))
    text_flag = 0
    for s in update_text_box:
        if s[0] > height_max - 5:
            text_flag = text_flag + 1
            processed_boxes.append(s[1])
        if text_flag >= 2:
            break
    while text_flag < 4:           
        text_flag = text_flag + 1
        processed_boxes.append("|---|")
    return processed_boxes


def get_occupants_ocr(page, reader, page_size
                    #   , driver_one, driver_two
                      ):
    if page_size == 1:
        # page.set_cropbox(fitz.Rect(362, 615, 543, 707))
        page.set_cropbox(fitz.Rect(352, 615, 553, 705)) 
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(50, 310, 160, 540))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/occupants-%i.png" % page.number)

    image = cv2.imread("png/occupants-%i.png" % page.number)
    occupants = reader.readtext(image,
         decoder="greedy", 
        #  detail=0, 
         x_ths = 1,
        #  paragraph=True, 
         blocklist = ';:_',
        #  rotation_info=[90]
         )
    # print(occupants,"\n")

    occupants_boxes = []
    
    # print(box_ocr[1],"\n 1111111")
    height_max = 0
    update_text_box = []
    for each_box in occupants:
        bbox, text,_ = each_box
        x_min, y_min, x_max, y_max = bbox
        height = y_max[1] - y_min[1]
        if height_max < height:
            height_max = height
        update_text_box.append((height, text))
    # print(height_max)
    if height_max < 55:
        # print("1")
        for i in range(2):
            temp = []
            for j in range(3):
                temp.append("|--|")
            occupants_boxes.append(temp)
        print("//////////////",occupants_boxes)
        return occupants_boxes
    for s in update_text_box:
        if s[0] > height_max - 20:
            occupants_boxes.append(s[1])
    # print(occupants_boxes,'\n')

    temp = ""
    result = []
    for each_string in occupants_boxes:
        if len(each_string) < 4:
            temp += " " + each_string
            result.append(temp)
            temp = ""
        else:
            if temp == "":
                temp = each_string
                continue
            else:
                
                if each_string[len(each_string) - 4: ].isdigit():
                    temp += " " + each_string
                    result.append(temp)
                    temp = ""
                else:
                    result.append(temp)
                    temp = each_string
    
    occupants_boxes = []
    temp = []
    for each_string in result:
        work_string = each_string
        last_name_end = work_string.find(",")
        lastname = work_string[: last_name_end]

        work_string = work_string[last_name_end + 1: ]

        first_name_end = work_string.find("-")
        firstname = work_string[: first_name_end]
        name = firstname + ' ' + lastname
        
        work_string = work_string[first_name_end + 1: ]

        street_end = work_string.find(",")
        street = work_string[: street_end]

        state = work_string[street_end + 1: ]

        temp = []
        try:
            temp.append(name)
        except (UnboundLocalError, NameError):
            temp.append("--")
        try:
            temp.append(street)
        except (UnboundLocalError, NameError):
            temp.append("--")
        try:
            temp.append(state)
        except (UnboundLocalError, NameError):
            temp.append("--")
        occupants_boxes.append(temp)
    # print(occupants_boxes,'\n')
    if len(occupants_boxes)==1:
        occupants_boxes.append([["|--|"],["|--|"],["|--|"]])

    print("////////////",occupants_boxes)
    return occupants_boxes


def process_pdf(page, reader, page_size):
    case_dict = {}

    date = get_date_ocr(page, reader, page_size)
    boxes = get_boxes_ocr(page, reader, page_size)
    occupants = get_occupants_ocr(page, reader, page_size)

    case_dict = {
        "Date": date,
        "118a": boxes[0],
        "119a": boxes[1],
        "118b": boxes[2],
        "119b": boxes[3],
        "Name1": occupants[0][0],
        "Address1": occupants[0][1],
        "City/State1": occupants[0][2],
        "Name2": occupants[1][0],
        "Address2": occupants[1][1],
        "City/State2": occupants[1][2],
    }

    return case_dict


def ocr_pdf(pdf):
    reader = easyocr.Reader(["en"], gpu=False)
    case_dict = {}
    page = pdf[0]

    if page.mediabox == (0.0, 0.0, 612.0, 792.0):
        page_size = 1
    elif page.mediabox == (0.0, 0.0, 792.0, 612.0):
        page_size = 2

    for page in tqdm(pdf):
        # if page.number == 0:
        if check_pdf(page, reader, page_size):
            case_dict[page.number] = process_pdf(page, reader, page_size)
        else:
            pass
        # else:
            # continue
    return case_dict
rows = []

if textpage:  # If there is encoded text within the pdf, it will extract that.
    output = pdf_to_text(pdf)
    for key, value in output.items():
        row = {
            "Name": value['Driver 1'],
            "Address": value['Address 1'],
            "City/State": value['Occupant 1'],  # City/State is not provided in the dictionary
            "118": value['118a'],
            "119": value['119a']
        }
        rows.append(row)
    
else:  # If there is no text, it will start the OCR.
    output = ocr_pdf(pdf)

# create a new Process object with the name of the uploaded file and the binary data of the file
# process_obj = Process(name=output_name, pdf_data=pdf)

# loop through the output data and create a dictionary for each row
    
    for key, value in output.items():
        row1 = {
            "Name": value['Name1'],
            "Address": value['Address1'],
            "City/State": value['City/State1'],  # City/State is not provided in the dictionary
            "a": value['118a'],
            "b": value['118b']
        }
        rows.append(row1)
        row2 = {
            "Name": value['Name2'],
            "Address": value['Address2'],
            "City/State": value['City/State2'],  # City/State is not provided in the dictionary
            "a": value['119a'],
            "b": value['119b']
        }
        rows.append(row2)
    
import requests

url = "http://64.226.79.139:3002/process"

# Define the data to be sent in the request
data = {
    "name": output_name,
    "rows": rows,
    "user_id":user_id
}

print("\n############\n", data)
# Send a POST request with the data
# response = requests.post(url, json=data)
# add the rows to the process_obj and save to the database
# print(rows)
# process_obj.rows = rows
# save_to_db(process_obj)
