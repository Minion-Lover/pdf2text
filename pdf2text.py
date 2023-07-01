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


doc = ap.Document(file)

file = check_rotation(file)

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
    print(text, 'text____')
    text = re.sub("[^0-9-\n]", "", text).split("\n")
    print(text, 'text+____final')
    print(len(text), 'text_____length')
    boxes = list(filter(None, text))
    print(len(boxes), 'boxes')

    while len(boxes) < 4:
        boxes.append("|---|")
    print(boxes, 'append boxes')

    
    return boxes


def get_driver_text(page, driver):
    if driver == 1:
        page.set_cropbox(fitz.Rect(53, 148, 285, 230))
    else:
        page.set_cropbox(fitz.Rect(293, 150, 545, 224))

    text = page.get_text().rstrip().strip().split("\n")
    print(text, 'text')

    if text == [""]:
        print('if drive')
        return ["Unknown", "Unknown"]

    if any("unknown" in item.lower() for item in text):
        driver = ["Unknown", "Unknown"]
        print('if unkonwn')
    else:
        if len(text) > 8:
            print('if else')
            driver = [" ".join([text[7], text[8]]), ", ".join([text[6]])]
            print(driver, 'Name____DRIVE')
        elif len(text) > 6:
            driver = [" ".join([text[6], text[3]]), ", ".join([text[5]])]
            print(driver, 'Name____DRIVE')
        elif len(text) > 5:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            print(driver, 'Name____DRIVE')   
        elif len(text) > 4:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            print(driver, 'Name____DRIVE')   
        elif len(text) > 3:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            print(driver, 'Name____DRIVE') 
        elif len(text) > 2:
            driver = [" ".join([text[5], text[3]]), ", ".join([text[5]])]
            print(driver, 'Name____DRIVE')   
    if isinstance(driver, int):
        driver = ["----", "----"]  # Assign a default value when driver is an integer
        print(driver, ' driver is integer')
    else:
        for n in range(len(driver)):
            if driver[n].count("-") > 8:
                driver[n] = "----"
                print(driver[n], ' driver[n]')               

    return driver


def get_occupants_text(page):
    page.set_cropbox(fitz.Rect(335, 620, 580, 760))

    text = page.get_text().rstrip().split("\n")
    print(text, 'text_____occupants')

    occupants = [element for element in text if check_for_dash(element)]
    
    occupants = [x + " " + y for x, y in zip(occupants[0::2], occupants[1::2])]
   



    while len(occupants) < 4:
        occupants.append("|---|")
    print(occupants, 'occupants__appened')    

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
            print(case["Occupant 2"], 'case["Occupant 2"]')
    
        if len(occupants) >= 3:
            case["Occupant 3"] = occupants[2]
        if len(occupants) >= 4:
            case["Occupant 4"] = occupants[3]    

        if len(boxes) >= 7:
            print('case 7')
            case7 = case.copy()
            case7["118a"] = boxes[2] if len(boxes) >= 7 and boxes[2] != "----" else "--"
            case7["118b"] = boxes[3] if len(boxes) >= 7 and boxes[3] != "----" else "--"
            case7["119a"] = boxes[4] if len(boxes) >= 7 and boxes[4] != "----" else "--"
            case7["119b"] = boxes[5] if len(boxes) >= 7 and boxes[5] != "----" else "--"
            case_dict[case_count] = case7

        elif len(boxes) >= 6:
            print('case 6')
            case6 = case.copy()
            case6["118a"] = boxes[1] if len(boxes) >= 6  and boxes[1] != "----" else "--"
            case6["118b"] = boxes[2] if len(boxes) >= 6 and boxes[2] != "----" else "--"
            case6["119a"] = boxes[3] if len(boxes)>= 6 and boxes[3] != "----" else "--"
            case6["119b"] = boxes[4] if len(boxes) >= 6 and boxes[4] != "----" else "--"
            case_dict[case_count] = case6

        elif len(boxes) >= 5:
            print('case 5')
            case5 = case.copy()
            case5["118a"] = boxes[0] if len(boxes) >= 5 and boxes[0] != "----" else "--"
            case5["118b"] = boxes[1] if len(boxes) >= 5 and boxes[1] != "----" else "--"
            case5["119a"] = boxes[2] if len(boxes) >= 5 and boxes[2] != "----" else "--"
            case5["119b"] = boxes[3] if len(boxes) >= 5 and boxes[3] != "----" else "--"
            case_dict[case_count] = case5
 
    return case_dict

def check_pdf(page, reader, page_size):
    if page_size == 1:
        page.set_cropbox(fitz.Rect(180, 36, 300, 72))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(738, 144, 765, 300))
    print(page_size)
    pix = page.get_pixmap(dpi=300)
    pix.save("page-0.png")

    image = cv2.imread("page-0.png")
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    pdf_check = reader.readtext(gray, decoder="greedy", detail=0, paragraph=False, rotation_info=[90])

    if any("new jersey" in s.lower() or "new_jersey" in s.lower() or "jersey" in s.lower() for s in pdf_check):
        return True
    else:
        return False


def get_date_ocr(page, reader, page_size):
    if page_size == 1:
        page.set_cropbox(fitz.Rect(70, 100, 130, 135))
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
        page.set_cropbox(fitz.Rect(537, 22, 568, 105))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(635, 540, 730, 570))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/boxes-%i.png" % page.number)

    image = cv2.imread("png/boxes-%i.png" % page.number)
    box_ocr = reader.readtext(
        image,
        decoder="greedy",
        detail=0,
        paragraph=True,
        y_ths=0.1,
        allowlist="ab1234567890-",
        rotation_info=[90],
    )
    processed_boxes = []

    while len(box_ocr) < 4:
        box_ocr.append("---")

    for item in range(4):
        if " " in box_ocr[item]:
            space_index = box_ocr[item].index(" ")
            processed_boxes.append(box_ocr[item][space_index + 1 :][:2])
        else:
            processed_boxes.append("|---|")
            box_ocr[item] = "--"

    return processed_boxes


def get_driver_one_ocr(page, reader, page_size):
    if page_size == 1:
        page.set_cropbox(fitz.Rect(62, 153, 280, 226))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(539, 52, 613, 290))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/driver_1-%i.png" % page.number)

    image = cv2.imread("png/driver_1-%i.png" % page.number)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 127, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    driver_one = reader.readtext(
        thresh, decoder="greedy", detail=0, paragraph=True, x_ths=0.95, rotation_info=[90]
    )
    # Finds "Dri" or "ver" (driver) in the OCRd image. then will go to that index and find the index for "na" (name)
    # Then it grabs the rest of the string as the first name.
    # Does the same for last name.
    if any("Dri" in s for s in driver_one) or any("ver" in s for s in driver_one):
        for i in range(len(driver_one)):
            if "Dri" in driver_one[i] or "ver" in driver_one[i]:
                first_index = driver_one.index(driver_one[i])
                first_name_list = driver_one[first_index].split(" ")

                for i in range(len(first_name_list)):
                    if "na" in first_name_list[i].lower():
                        name_index = first_name_list.index(first_name_list[i])
                        first_name = " ".join(first_name_list[name_index + 1 :])
                        if not first_name:
                            first_name = "--"
                        break
                    else:
                        continue
                break
            else:
                continue

    # LAST NAME
    last_index = 0
    if any("Las" in s for s in driver_one) or any("Les" in s for s in driver_one):
        for i in range(len(driver_one)):
            if "las" in driver_one[i].lower() or "les" in driver_one[i].lower():
                last_index = driver_one.index(driver_one[i])
                last_name_list = driver_one[last_index].split(" ")

                for i in range(len(last_name_list)):
                    if "na" in last_name_list[i].lower():
                        name_index = last_name_list.index(last_name_list[i])
                        last_name = " ".join(last_name_list[name_index + 1 :])
                        if "29" in last_name:
                            last_name = " ".join(
                                [
                                    x
                                    for x in last_name_list[name_index + 1 :]
                                    if x.isupper()
                                ]
                            )
                            if "29" in last_name:
                                last_name_temp = last_name.split(" ")
                                for j in range(len(last_name_temp)):
                                    if "29" in last_name_temp[j]:
                                        last_name_temp.remove(last_name_temp[j])
                                        last_name = " ".join(last_name_temp)
                                        break
                                    else:
                                        continue
                            else:
                                last_name = last_name
                        if not last_name:
                            last_name = "--"
                        break
                    else:
                        continue
                break
            else:
                continue
    street_index = 0
    address = ""
    last_name_results = driver_one[last_index:]
    # Finds Street N(umb)er
    if any("umb" in s for s in last_name_results):
        for i in range(len(last_name_results)):
            if "umb" in last_name_results[i]:
                address_index = last_name_results.index(last_name_results[i])
                address_list = last_name_results[i].split(" ")

                for i in range(len(address_list)):
                    if (
                        "str" in address_list[i].lower()
                        or "eet" in address_list[i].lower()
                    ):
                        street_index = address_list.index(address_list[i])
                        address = " ".join(address_list[street_index + 1 :])
                        if not address:
                            address = "--"
                        break
                    else:
                        continue
                break
            else:
                continue

    address_results = last_name_results[street_index - 2 :]
    if address_results == []: return []
    if address in address_results[0] or "Sex" in address_results[0]:
        address_results = last_name_results[street_index - 1 :]

    for i in range(len(address_results)):
        if "31" in address_results[i]:
            address_results[i] = address_results[i].split("31", 1)[0]

        if "28" in address_results[i] or "23" in address_results[i]:
            if "30" in address_results[i]:
                address_results[i] = address_results[i].split("30", 1)[0]
            city_results = address_results[i].split(" ")

            for n in range(len(city_results)):
                if "28" in city_results[n] or "23" in address_results[i]:
                    city_list = [x for x in city_results if x.isupper()]
                    city = " ".join(city_list)
                    if not city:
                        city = "--"
                    break
        elif "ate" in address_results[i] or "Sta" in address_results[i]:
            state_results = address_results[i].split(" ")
            try:
                state = state_results[1]
                if state == "Zip":
                    state = state_results[2]
                    zip_code = state_results[3]
            except:
                state = "--"
        elif "Zip" in address_results[i]:
            zip_results = address_results[i].split(" ")
            try:
                zip_code = zip_results[1][:5]
            except:
                zip_code = "--"
        driver_info = []

    try:
        driver_info.append(first_name)
    except (UnboundLocalError, NameError):
        driver_info.append("--")
    try:
        driver_info.append(last_name)
    except (UnboundLocalError, NameError):
        driver_info.append("--")
    try:
        driver_info.append(address)
    except (UnboundLocalError, NameError):
        driver_info.append("--")
    try:
        driver_info.append(city)
    except (UnboundLocalError, NameError):
        driver_info.append("--")
    try:
        driver_info.append(state)
    except (UnboundLocalError, NameError):
        driver_info.append("--")
    try:
        driver_info.append(zip_code)
    except (UnboundLocalError, NameError):
        driver_info.append("--")

    while len(driver_info) < 2:
        driver_info.append("---")
    return driver_info


def get_driver_two_ocr(page, reader, page_size):
    if page_size == 1:
        page.set_cropbox(fitz.Rect(297, 150, 545, 224))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(547, 300, 614, 540))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/driver_2-%i.png" % page.number)

    image = cv2.imread("png/driver_2-%i.png" % page.number)
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 127, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]

    driver_two = reader.readtext(
        thresh, decoder="greedy", detail=0, paragraph=True, x_ths=0.3, rotation_info=[90]
    )

    # FIRST NAME
    if any("Dri" in s for s in driver_two) or any("ver" in s for s in driver_two):
        for i in range(len(driver_two)):
            if "Dri" in driver_two[i] or any("ver" in s for s in driver_two[i]):
                first_index = driver_two.index(driver_two[i])
                first_name_list = driver_two[first_index].split(" ")

                for i in range(len(first_name_list)):
                    if "na" in first_name_list[i].lower():
                        name_index = first_name_list.index(first_name_list[i])
                        first_name = " ".join(first_name_list[name_index + 1 :])
                        if not first_name:
                            first_name = "--"
                        break
                    else:
                        continue
                break
            else:
                continue

    # LAST NAME
    last_index = 0
    if any("Las" in s for s in driver_two) or any("Les" in s for s in driver_two):
        for i in range(len(driver_two)):
            if "Las" in driver_two[i] or "Les" in driver_two[i]:
                last_index = driver_two.index(driver_two[i])
                last_name_list = driver_two[last_index].split(" ")

                for i in range(len(last_name_list)):
                    if "na" in last_name_list[i].lower():
                        name_index = last_name_list.index(last_name_list[i])
                        last_name = " ".join(last_name_list[name_index + 1 :])
                        if "59" in last_name:
                            last_name = " ".join(
                                [
                                    x
                                    for x in last_name_list[name_index + 1 :]
                                    if x.isupper()
                                ]
                            )
                            if "59" in last_name:
                                last_name_temp = last_name.split(" ")
                                for j in range(len(last_name_temp)):
                                    if "59" in last_name_temp[j]:
                                        last_name_temp.remove(last_name_temp[j])
                                        last_name = " ".join(last_name_temp)
                                        break
                                    else:
                                        continue
                            else:
                                last_name = last_name
                        if not last_name:
                            last_name = "--"
                        break
                    else:
                        continue
                break
            else:
                continue

    last_name_results = driver_two[last_index:]

    if any("umb" in s for s in last_name_results):
        for i in range(len(last_name_results)):
            if "umb" in last_name_results[i]:
                address_index = last_name_results.index(last_name_results[i])
                address_list = last_name_results[i].split(" ")

                for i in range(len(address_list)):
                    if (
                        "str" in address_list[i].lower()
                        or "eet" in address_list[i].lower()
                    ):
                        street_index = address_list.index(address_list[i])
                        address = " ".join(address_list[street_index + 1 :])
                        if not address:
                            address = "--"
                        break
                    else:
                        continue
                break
            else:
                continue
    try:
        address_results = last_name_results[street_index - 2 :]
        if address_results == []:
            return []
        if address in address_results[0] or "Sex" in address_results[0]:
            address_results = last_name_results[street_index - 1 :]
    except (UnboundLocalError):
        address_results = last_name_results[4:]

    for i in range(len(address_results)):
        if "61" in address_results[i]:
            address_results[i] = address_results[i].split("61", 1)[0]

        if (
            "58" in address_results[i] or "68" in address_results[i]
        ):  # or "23" in address_results[i]:
            if "60" in address_results[i]:
                address_results[i] = address_results[i].split("60", 1)[0]
            city_results = address_results[i].split(" ")

            for n in range(len(city_results)):
                if "58" in city_results[n] or "68" in address_results[i]:

                    # city_index = city_results.index(city_results[n])
                    city_list = [x for x in city_results if x.isupper()]
                    city = " ".join(city_list)
                    if not city:
                        city = "--"
                    break
        elif "ate" in address_results[i] or "Sta" in address_results[i]:
            state_results = address_results[i].split(" ")
            try:
                state = state_results[1]
                if state == "Zip":
                    state = state_results[2]
                    zip_code = state_results[3]
            except:
                state = "--"
        elif "Zip" in address_results[i]:
            zip_results = address_results[i].split(" ")
            try:
                zip_code = zip_results[1][:5]
            except:
                zip_code = "--"

    driver_info = []

    try:
        driver_info.append(first_name)
    except (UnboundLocalError, NameError):
        driver_info.append("---")
    try:
        driver_info.append(last_name)
    except (UnboundLocalError, NameError):
        driver_info.append("---")
    try:
        driver_info.append(address)
    except (UnboundLocalError, NameError):
        driver_info.append("---")
    try:
        driver_info.append(city)
    except (UnboundLocalError, NameError):
        driver_info.append("---")
    try:
        driver_info.append(state)
    except (UnboundLocalError, NameError):
        driver_info.append("---")
    try:
        driver_info.append(zip_code)
    except (UnboundLocalError, NameError):
        driver_info.append("---")

    while len(driver_info) < 2:
        driver_info.append("---")

    return driver_info


def get_occupants_ocr(page, reader, page_size, driver_one, driver_two):
    if page_size == 1:
        page.set_cropbox(fitz.Rect(362, 615, 543, 707))
    elif page_size == 2:
        page.set_cropbox(fitz.Rect(50, 310, 160, 540))

    pix = page.get_pixmap(dpi=400)
    pix.save("png/occupants-%i.png" % page.number)

    image = cv2.imread("png/occupants-%i.png" % page.number)
    occupants = reader.readtext(image, decoder="greedy", detail=0, paragraph=True, rotation_info=[90])

    if any("driver 1" in s.lower() for s in occupants):
        occupants_ocr = reader.readtext(
            image, decoder="greedy", detail=0, paragraph=True, y_ths=0.3, x_ths=30, rotation_info=[90]
        )

        for n in range(len(occupants_ocr)):
            if (
                "decea" in occupants_ocr[n].lower()
                or "ased" in occupants_ocr[n].lower()
                or "dere" in occupants_ocr[n].lower()
            ):
                occupants_ocr.remove(occupants_ocr[n])
        if "driver 1" in occupants_ocr[n].lower():
            occupants_ocr[n] = " ".join(driver_one)
        if "driver 2" in occupants_ocr[n].lower():
            occupants_ocr[n] = " ".join(driver_two)

        while len(occupants_ocr) < 4:
            occupants_ocr.append("|---|")
        return occupants_ocr

    for i in range(len(occupants)):
        if (
            "decea" in occupants[0].lower()
            or "ased" in occupants[0].lower()
            or "dere" in occupants[0].lower()
        ):
            occupants.remove(occupants[0])
    while len(occupants) < 4:
        occupants.append("---")

    return occupants


def process_pdf(page, reader, page_size):
    case_dict = {}

    date = get_date_ocr(page, reader, page_size)
    boxes = get_boxes_ocr(page, reader, page_size)
    driver_one = get_driver_one_ocr(page, reader, page_size)
    driver_two = get_driver_two_ocr(page, reader, page_size)
    occupants = get_occupants_ocr(page, reader, page_size, driver_one, driver_two)

    case_dict = {
        "Date": date,
        "118a": boxes[0],
        "118b": boxes[1],
        "119a": boxes[2],
        "119b": boxes[3],
        "Driver 1": " ".join(driver_one[0:2]),
        "Address 1": " ".join(driver_one[2:]),
        "Driver 2": " ".join(driver_two[0:2]),
        "Address 2": " ".join(driver_two[2:]),
        "Occupant 1": occupants[0],
        "Occupant 2": occupants[1],
        "Occupant 3": occupants[2],
        "Occupant 4": occupants[3],
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
        if check_pdf(page, reader, page_size):
            case_dict[page.number] = process_pdf(page, reader, page_size)
        else:
            pass

    return case_dict

if textpage:  # If there is encoded text within the pdf, it will extract that.
    output = pdf_to_text(pdf)
    
else:  # If there is no text, it will start the OCR.
    output = ocr_pdf(pdf)

# create a new Process object with the name of the uploaded file and the binary data of the file
# process_obj = Process(name=output_name, pdf_data=pdf)

# loop through the output data and create a dictionary for each row
rows = []
for key, value in output.items():
    row = {
        "Name": value['Driver 1'],
        "Address": value['Address 1'],
        "City/State": value['Occupant 1'],  # City/State is not provided in the dictionary
        "118": value['118a'],
        "119": value['119a']
    }
    rows.append(row)
    
import requests

url = "http://0.0.0.0:0/process"

# Define the data to be sent in the request
data = {
    "name": output_name,
    "rows": rows,
    "user_id":user_id
}

print("\n", data)
# Send a POST request with the data
response = requests.post(url, json=data)
