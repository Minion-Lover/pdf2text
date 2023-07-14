from tqdm import tqdm
import os
import shutil
import argparse
import re
import pandas as pd
import easyocr
import cv2
import fitz
import aspose.pdf as ap
from difflib import SequenceMatcher



parser = argparse.ArgumentParser(
    description="Process PDF files of NJPD Crash Reports to return wanted values."
)
parser.add_argument("pdf_file", metavar="file", help="path to file")

args = parser.parse_args()
file = args.pdf_file

def create_folder(folder_path):
    if not os.path.exists(folder_path):
        os.makedirs(folder_path)
        print("Folder created successfully!")
    else:
        print("Folder already exists.")

folder_path = "png"
create_folder(folder_path)

doc = ap.Document(file)



output_name = os.path.splitext(os.path.basename(file))[0].replace("/", "_").replace("\\", "_")

pdf = fitz.open(file)


page = pdf[0]

rotation = page.rotation
page_style = 0
if rotation == 0:
    page_style = 0
    pdfwidth = page.rect.width
    pdfheight = page.rect.height
    barheight = pdfheight - 792
elif rotation == 90:
    for i in range(pdf.page_count):
        page = pdf.load_page(i)
        page.set_rotation(0)
    pdfwidth = page.rect.width
    pdfheight = page.rect.height
    barheight = pdfheight - 792


elif rotation == 180:
    page.set_rotation(0)
    pdfwidth = page.rect.width
    pdfheight = page.rect.height
    barheight = pdfheight - 792

elif rotation == 270:
    page_style = 1
    pdfwidth = page.rect.height
    pdfheight = page.rect.width
    barwidth = pdfwidth - 792

# pdfwidth = page.rect.width
# pdfheight = page.rect.height
# print(pdfwidth,'-',pdfheight, '-', page.rotation)
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

#----------------IMAGE---------------#

def check_pdf(page, reader):
    if page_style == 0:
        page.set_cropbox(fitz.Rect(0, 0, 72, 72+barheight/2))  
    elif page_style == 1:
        page.set_cropbox(fitz.Rect(pdfwidth-72-barwidth/2, 0, pdfwidth, 72))
    pix = page.get_pixmap(dpi=300)
    pix.save("png/pagecheck.png")
    image = cv2.imread(f"png/pagecheck.png")
    image = cv2.resize(image, None, fx = 4, fy = 4)

    pdf_check = reader.readtext(image, decoder="greedy", detail=0, paragraph=False)
    # print(pdf_check)

    if any("95" in s or "96" in s or "97" in s or "01" in s.lower() for s in pdf_check):
        return True
    else:
        return False
First_name = '26 Driver\'s First Name Initial Last Name'
Second_name = '56 Driver\'s First Name Initial Last Name'
First_street = '27 Number Street'
Second_street = '57 Number Street'
First_city = '28 City State'
Second_city = '58 City State'
First_eyes = '30 Eyes DL Class Restrictions'
Second_eyes = '60 Eyes DL Class Restrictions'

def get_data_one_ocr(page, reader):
    if page_style == 0:
        page.set_cropbox(fitz.Rect(0, 135+barheight/2, pdfwidth/2-4.5, 243+barheight/2))
    elif page_style == 1:
        page.set_cropbox(fitz.Rect(pdfwidth-243-barwidth/2, 0, pdfwidth-135-barwidth/2, pdfheight/2-4.5))

    pix = page.get_pixmap(dpi=300)
    pix.save("png/data_one-%i.png" % page.number)

    image = cv2.imread("png/data_one-%i.png" % page.number)
    image = cv2.resize(image, None, fx = 2, fy = 2)
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    data_ocr = reader.readtext(gray, 
                               decoder="greedy", 
                               detail=0, 
                               paragraph=False,
                            #    allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890.,-[]' ",
                            #    blocklist = '|',
                               width_ths =50,)
  
    # for x in data_ocr:      print(x, '\n')

    name_index = 0
    street_index = 0
    city_index = 0
    last_index = 0

    if any("driver" in s.lower() or "orivor" in s.lower() or "first" in s.lower() or "driv" in s.lower() or "name" in s.lower()  or "last" in s.lower() or "sex" in s.lower() or "26." in s.lower() or "26 " in s.lower() or " namo" in s.lower() for s in data_ocr):
        for i in data_ocr:
            if "driver" in i.lower() or "orivor" in i.lower() or "first" in i.lower() or "driv" in i.lower()  or "name" in i.lower() or "last" in i.lower() or "sex" in i.lower() or "26." in i.lower() or "26 " in i.lower() or " namo" in i.lower() and SequenceMatcher(None, First_name, i).ratio() > 0.5:
                name_index = data_ocr.index(i)
                break
            else:
                continue
    else:
        name = "--"
    if any("number" in s.lower() or "numb" in s.lower() or "nump" in s.lower() or "street" in s.lower() or "stroot" in s.lower() or "ber" in s.lower() or "27." in s or "27 " in s for s in data_ocr):
        for i in data_ocr:
            if "number" in i.lower() or "numb" in i.lower() or "nump" in i.lower() or "street" in i.lower() or "stroot" in i.lower() or "ber" in i.lower() or "27." in i or "27 " in i and SequenceMatcher(None, First_street, i).ratio() > 0.5:
                street_index = data_ocr.index(i)
                if street_index <= name_index: continue
                break
            else:
                continue
    else:
        street = "--"
    if any("city" in s.lower() or "state" in s.lower() or "slate" in s.lower() or "oty" in s.lower() or "chy" in s.lower() or "cly" in s.lower() or "otv" in s.lower() or "ohv" in s.lower() or " statc" in s.lower() or " stare" in s.lower() or " stale" in s.lower() or "104" in s or "zip" in s.lower() or "cily" in s.lower() or "28." in s or "28 " in s for s in data_ocr):
        for i in data_ocr:
            if "city" in i.lower() or "state" in i.lower() or "slate" in i.lower() or "oty" in i.lower() or "chy" in i.lower() or "cly" in i.lower() or "otv" in i.lower() or "ohv" in i.lower() or " statc" in i.lower() or " stare" in i.lower() or "stale" in i.lower() or "104" in i or "zip" in i.lower() or "cily" in i.lower() or "28." in i or "28 " in i and SequenceMatcher(None, First_city, i).ratio() > 0.5:
                city_index = data_ocr.index(i)
                if city_index <= street_index: continue
                break
            else:
                continue
    else:
        city = "--"
    if any("eye" in s.lower() or "eve" in s.lower() or "cve" in s.lower() or "eyo" in s.lower() or "evo" in s.lower() or "class" in s.lower() or "30 " in s or "30." in s for s in data_ocr):
        for i in data_ocr:
            if "eye" in i.lower() or "eve" in i.lower() or "cve" in i.lower() or "eyo" in i.lower() or "evo" in i.lower() or "class" in i.lower() or "30 " in i or "30." in i and SequenceMatcher(None, First_eyes, i).ratio() > 0.5:
                last_index = data_ocr.index(i)
                if last_index <= city_index: continue
                break
            else:
                continue

    name_index = max(0, name_index)
    street_index = max(name_index, street_index)
    city_index = max(street_index, city_index)
    last_index = max(city_index, last_index)
    # print(name_index,'///',street_index,'///',city_index,'///',last_index)
    temp_name = '|---|'
    temp_street = '|---|'
    temp_city = '|---|'
    for i in range(len(data_ocr)):
        if i > name_index and i < street_index:
            if len(data_ocr[i]) > len(temp_name) and len(data_ocr[i]) < 45:
                temp_name = remove_non_name(data_ocr[i])
        if i > street_index and i < city_index:
            if len(data_ocr[i]) > len(temp_street):
                temp_street = check_first_street(data_ocr[i])
        if i > city_index and i < last_index:
            if len(data_ocr[i]) > len(temp_city):
                temp_city = check_first_city(data_ocr[i])
    print("\n\n", temp_name, '-----', temp_street, '------',temp_city)
    return [temp_name, temp_street, temp_city]

def get_data_two_ocr(page, reader):
    if page_style == 0:
        page.set_cropbox(fitz.Rect(pdfwidth/2-4.5, 135+barheight/2, pdfwidth, 243+barheight/2))
    elif page_style == 1:
        page.set_cropbox(fitz.Rect(pdfwidth-243-barwidth/2, pdfheight/2-4.5, pdfwidth-135-barwidth/2, pdfheight))
    pix = page.get_pixmap(dpi=300)
    pix.save("png/data_two-%i.png" % page.number)

    image = cv2.imread("png/data_two-%i.png" % page.number)
    image = cv2.resize(image, None, fx = 2, fy = 2)
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    data_ocr = reader.readtext(gray, 
                               decoder="greedy", 
                               detail=0, 
                               paragraph=False,
                            #    allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890.,-[]' ",
                            #    blocklist = '|',
                               width_ths =50,)
    # for x in data_ocr:
    #     print(x, '\n')

    name_index = 0
    street_index = 0
    city_index = 0
    last_index = 0

    if any("driver" in s.lower() or "first" in s.lower() or "driv" in s.lower() or "name" in s.lower()  or "last" in s.lower() or "sex" in s.lower() or "56." in s.lower() or "56 " in s.lower() or " namo" in s.lower() for s in data_ocr):
        for i in data_ocr:
            if "driver" in i.lower() or "first" in i.lower() or "driv" in i.lower() or "name" in i.lower() or "last" in i.lower() or "sex" in i.lower() or "56." in i.lower() or "56 " in i.lower() or " namo" in i.lower() and SequenceMatcher(None, Second_name, i).ratio() > 0.5:
                name_index = data_ocr.index(i)
                break
            else:
                continue
    else:
        name = "--"
    if any("number" in s.lower() or "numb" in s.lower() or "nump" in s.lower() or "street" in s.lower() or "stroot" in s.lower() or "ber" in s.lower() or "57." in s or "57 " in s for s in data_ocr):
        for i in data_ocr:
            if "number" in i.lower() or "numb" in i.lower() or "nump" in i.lower() or "street" in i.lower() or "stroot" in i.lower() or "ber" in i.lower() or "57." in i or "57 " in i and SequenceMatcher(None, Second_street, i).ratio() > 0.5:
                street_index = data_ocr.index(i)
                if street_index <= name_index: continue
                break
            else:
                continue
    else:
        street = "--"
    if any("city" in s.lower() or "state" in s.lower() or "oty" in s.lower() or "chy" in s.lower() or "otv" in s.lower() or "ohv" in s.lower() or "zip" in s.lower() or "cily" in s.lower() or "58." in s or "58 " in s for s in data_ocr):
        for i in data_ocr:
            if "city" in i.lower() or "state" in i.lower() or "oty" in i.lower() or "chy" in i.lower() or "otv" in i.lower() or "ohv" in i.lower() or "zip" in i.lower() or "cily" in i.lower() or "58." in i or "58 " in i and SequenceMatcher(None, Second_city, i).ratio() > 0.5:
                city_index = data_ocr.index(i)
                if city_index <= street_index: continue
                break
            else:
                continue
    else:
        city = "--"
    if any("eye" in s.lower() or "eve" in s.lower()  or "eyo" in s.lower() or "evo" in s.lower() or "class" in s.lower() or "60 " in s or "60." in s for s in data_ocr):
        for i in data_ocr:
            if "eye" in i.lower() or "eve" in i.lower() or "eyo" in i.lower() or "evo" in i.lower() or "class" in i.lower() or "60 " in i or "60." in i and SequenceMatcher(None, Second_eyes, i).ratio() > 0.5:
                last_index = data_ocr.index(i)
                if last_index <= city_index: continue
                break
            else:
                continue

    name_index = max(0, name_index)
    street_index = max(name_index, street_index)
    city_index = max(street_index, city_index)
    last_index = max(city_index, last_index)
    # print(name_index,'///',street_index,'///',city_index,'///',last_index)
    temp_name = '|---|'
    temp_street = '|---|'
    temp_city = '|---|'
    for i in range(len(data_ocr)):
        if i > name_index and i < street_index:
            if len(data_ocr[i]) > len(temp_name) and len(data_ocr[i]) < 45:
                temp_name = remove_non_name(data_ocr[i])
        if i > street_index and i < city_index:
            if len(data_ocr[i]) > len(temp_street):
                temp_street = check_second_street(data_ocr[i])
        if i > city_index and i < last_index:
            if len(data_ocr[i]) > len(temp_city):
                temp_city = check_second_city(data_ocr[i])
    print("\n\n", temp_name, '-----',temp_street, '------',temp_city)
    return [temp_name, temp_street, temp_city]

def get_value(page, reader):
    if page_style == 0:
        page.set_cropbox(fitz.Rect(540, 0, pdfwidth, 135+barheight/2))
    elif page_style == 1:
        page.set_cropbox(fitz.Rect(pdfwidth-140-barwidth/2, 540, pdfwidth, pdfheight))

    pix = page.get_pixmap(dpi=300)
    pix.save("png/data_value-%i.png" % page.number)

    image = cv2.imread("png/data_value-%i.png" % page.number)
    image = cv2.resize(image, None, fx = 2, fy = 2)
    gray = cv2.cvtColor(image,cv2.COLOR_BGR2GRAY)
    data_ocr = reader.readtext(gray, 
                               decoder="greedy", 
                               detail=0, 
                               paragraph=False,
                            #    allowlist = "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz1234567890.,-[]' ",
                            #    blocklist = '|',
                               width_ths =0.1,
                               height_ths = 20,
                               )
    # print(data_ocr)
    data_temp = []
    for string in data_ocr:
        string = string.replace('T1', '11').replace('t1', '11').replace('I1', '11').replace('Ii', '11').replace('I', '1').replace('i', '1').replace('T18', '118').replace('t18', '118').replace('T19', '119').replace('t19', '119').replace('11B', '118').replace('11E', '118').replace('11S', '119').replace('1186', '118b').replace('1196', '119b').replace('170', '120').replace('11E', '118').replace('11S', '119').replace('1186', '118b').replace('1196', '119b').replace('170', '120').replace('113', '118').replace('13a', '18a').replace('13b', '18b').replace('116', '118').replace('110', '118').replace('48a', '118a').replace('48b', '118b').replace('49a', '119a').replace('49b', '119b')
        data_temp.append(string)
    # print('\n####',data_temp)
    _118a_index = 0
    _118b_index = 0
    _119a_index = 0
    _119b_index = 0
    _120a_index = 0

    if any("118a" in s or "118" in s or "11" in s or "18" in s or "18a" in s for s in data_temp):
        for i in data_temp:
            if "118a" in i or "118" in i or "11" in i or "18" in i or "18a" in i :
                _118a_index = data_temp.index(i)
                break
            else:
                continue
    else:
        _118a = "|---|"
        _118a_index = 0

    if any("118b" in s or "118" in s or "18" in s or "11" in s or "18b" in s for s in data_temp):
        for i in data_temp:
            if "118b" in i or "118" in i or "18" in i or "11" in i or "18b" in i:
                if data_temp.index(i) <= _118a_index:
                    continue
                _118b_index = max(data_temp.index(i),_118a_index)
                break
            else:
                continue
    else:
        _118b = "|---|"
        _118b_index = _118a_index+1

    if any("119a" in s or "119" in s or "11" in s or "19" in s or "19a" in s or "9a" in s for s in data_temp):
        for i in data_temp:
            if "119a" in i or "119" in i or "11" in i or "19" in i or "19a" in i or "9a" in i:
                if data_temp.index(i) <= _118b_index:
                    continue
                _119a_index = max(data_temp.index(i),_118b_index)
                break
            else:
                continue
    else:
        _119a = "|---|"
        _119a_index = _118b_index+1

    if any("119b" in s or "119" in s or "19" in s or "11" in s or "19b" in s or "9b" in s for s in data_temp):
        for i in data_temp:
            if "119b" in i or "119" in i or "11" in i or "19" in i or "19b" in i or "9b" in i:
                if data_temp.index(i) <= _119a_index:
                    continue
                _119b_index = max(data_temp.index(i),_119a_index)
                break
            else:
                continue
    else:
        _119b = "|---|"
        _119b_index = _119a_index+1

    if any("120a" in s or "120" in s or "20" in s or "20a" in s for s in data_temp):
        for i in data_temp:
            if "120a" in i or "120" in i or "20" in i or "20a" in i:
                if data_temp.index(i) <= _119b_index:
                    continue
                _120a_index = max(data_temp.index(i),_119b_index)
                break
            else:
                continue
    else:
        _120a_index = len(data_temp)
    
    _118a = "|---|"
    _118b = "|---|"
    _119a = "|---|"
    _119b = "|---|"
    # print("\n\n", '-----',_118a_index, '------',_118b_index, '-----',_119a_index, '------',_119b_index, '------',_120a_index)

    for i in range(len(data_temp)):
        if i > _118a_index and i < _118b_index:
            if make_num(data_temp[i]) != '':
                    _118a = make_num(data_temp[i])
        if i > _118b_index and i < _119a_index:
            if make_num(data_temp[i]) != '':
                    _118b = make_num(data_temp[i])
        if i > _119a_index and i < _119b_index:
            if make_num(data_temp[i]) != '':
                    _119a = make_num(data_temp[i])
        if i > _119b_index and i < _120a_index:
            if make_num(data_temp[i]) != '':
                    _119b = make_num(data_temp[i])

    print("\n\n", _118a, '------',_118b, '-----',_119a, '------',_119b)
    return [_118a,_118b,_119a,_119b]



def make_num(text):
    clean_string = re.sub(r'[^0-9 ]', '', text)
    if len(clean_string) == 1: return ''
    if len(clean_string) >= 3: return ''
    if str(clean_string) == '0 ': return ''
    if str(clean_string) == ' 0': return ''
    if str(clean_string) == '1 ': return ''
    if str(clean_string) == ' 1': return ''
    if str(clean_string) == '11': return ''
    return clean_string

def insert_spaces(text):
    # Use regex to insert space before each uppercase letter (except the first letter)
    modified_text = re.sub(r'(?<!^)(?=[A-Z])', ' ', text)
    return modified_text

def remove_non_name(text):
    clean_string = re.sub(r'[^a-zA-Z ]', '', text)
    clean_string = re.sub(r'\s+', ' ', clean_string.strip())
    chunks = clean_string.split(' ')
    result = ''
    for string in chunks:
        # print(string,'#',remove_end_chars(string),'#/#')
        result = ' '.join([result, remove_end_chars(string)])
    result = re.sub(r'\s+', ' ', result.strip())
    clean_string = result
    # clean_string = insert_spaces(clean_string)

    if clean_string.endswith('Mo') or clean_string.endswith('Fo') or clean_string.endswith('LM') or clean_string.endswith('LF'):
        clean_string = clean_string[:-2]
    elif clean_string.endswith('LMK') or clean_string.endswith('LMi') or clean_string.endswith('Loo') or clean_string.endswith('MHz') or clean_string.endswith('Mtz') or clean_string.endswith('Mzu') or clean_string.endswith('hzn'):
        clean_string = clean_string[:-3]
    elif clean_string.endswith('LMko') or clean_string.endswith('MHzn'):
        clean_string = clean_string[:-4]
    elif clean_string.endswith('M') or clean_string.endswith('F'):
        clean_string = clean_string[:-1]
    
    return clean_string

def remove_end_chars(string):
    if len(string) > 2:
        return string.strip()
    else:
        return string[:-2].strip()        
def check_first_street(text):
    text = text.replace("_", " ")
    clean_string = re.sub(r'[^a-zA-Z0-9# ]', '', text)
    clean_string = re.sub(r'\s+', ' ', clean_string.strip())
    # if clean_string.startswith('103 1') or clean_string.startswith('108 1') or clean_string.startswith('103 7') or clean_string.startswith('108 7'):
    #     clean_string = clean_string[5:]
    if clean_string.startswith('103 ') or clean_string.startswith('108 ') or clean_string.startswith('708 ') or clean_string.startswith('703 '):
        clean_string = clean_string[4:]
    return clean_string

def check_second_street(text):
    text = text.replace("_", " ")
    clean_string = re.sub(r'[^a-zA-Z0-9# ]', '', text)
    clean_string = re.sub(r'\s+', ' ', clean_string.strip())
    return clean_string

def check_city(text):
    text = text.replace(" NJj ", " NJ ").replace("NJ", " NJ").replace("NBWARR", "NEWARK").replace("NBWARK", "NEWARK").replace("NEWARR", "NEWARK")


def check_first_city(text):
    text = text.replace("_", " ")
    clean_string = re.sub(r'[^a-zA-Z0-9-, ]', '', text)
    check_city(clean_string)
    clean_string = re.sub(r'\s+', ' ', clean_string.strip())

    if clean_string.startswith('104  1') or clean_string.startswith('108  1') or clean_string.startswith('T03  7') or clean_string.startswith('T03  1') or clean_string.startswith('T08  7') or clean_string.startswith('T08  1') or clean_string.startswith('103  1') or clean_string.startswith('703  1'):
        clean_string = clean_string[7:]
    if clean_string.startswith('104 1') or clean_string.startswith('108 1') or clean_string.startswith('T03 7') or clean_string.startswith('T03 1') or clean_string.startswith('T08 7') or clean_string.startswith('T08 1') or clean_string.startswith('103 1') or clean_string.startswith('703 1'):
        clean_string = clean_string[6:]
    elif clean_string.startswith('01 1') or clean_string.startswith('02 1') or clean_string.startswith('03 1') or clean_string.startswith('04 1') or clean_string.startswith('05 1') or clean_string.startswith('06 1') or clean_string.startswith('07 1') or clean_string.startswith('08 1') or clean_string.startswith('09 1') or clean_string.startswith('104 ') or clean_string.startswith('108 ') or clean_string.startswith('N5 7'):
        clean_string = clean_string[5:]
    elif clean_string.startswith('104 ') or clean_string.startswith('108 '):
        clean_string = clean_string[6:]
    elif clean_string.startswith('01 ') or clean_string.startswith('02 ') or clean_string.startswith('03 ') or clean_string.startswith('04 ') or clean_string.startswith('05 ') or clean_string.startswith('06 ') or clean_string.startswith('07 ') or clean_string.startswith('08 ') or clean_string.startswith('09 ') or clean_string.startswith('00 '):
        clean_string = clean_string[4:]
    return clean_string

def check_second_city(text):
    text = text.replace("_", " ")
    clean_string = re.sub(r'[^a-zA-Z0-9-, ]', '', text)
    check_city(clean_string)
    clean_string = re.sub(r'\s+', ' ', clean_string.strip())
    return clean_string




def process_pdf(page, reader):
    case_dict = {}

    data_one = get_data_one_ocr(page, reader)
    data_two = get_data_two_ocr(page, reader)
    value = get_value(page, reader)


    case_dict = {
        "118a": value[0],
        "118b": value[1],
        "119a": value[2],
        "119b": value[3],
        "Name1": data_one[0],
        "Address1": data_one[1],
        "City/State1": data_one[2],
        "Name2": data_two[0],
        "Address2": data_two[1],
        "City/State2": data_two[2],
    }

    return case_dict


def ocr_pdf(pdf):
    reader = easyocr.Reader(["en"], gpu=False)
    case_dict = {}
    page = pdf[0]

    for page in tqdm(pdf):
        if check_pdf(page, reader):
            case_dict[page.number] = process_pdf(page, reader)
        else:
            pass
    return case_dict
rows = []

def _main():
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


if __name__ == "__main__":
    _main()

    my_df = pd.DataFrame(rows)
    my_df.to_csv(f'{output_name}.csv', index=False, header=False)

