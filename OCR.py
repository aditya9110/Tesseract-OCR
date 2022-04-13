import pytesseract
from pdf2image import convert_from_path
from cv2 import cv2
import os
import streamlit as st
from tkinter import *
from tkinter import filedialog
from tkinter import messagebox

# converts pdf to list of images
def pdf_to_img(pdf):
    pdf_pages = convert_from_path(pdf, dpi=350, poppler_path=r'C:\Program Files\poppler-0.68.0\bin')
    i = 1
    img_list = []
    for page in pdf_pages:
        page.save('page' + str(i) + '.jpg', 'JPEG')
        img_list.append('page' + str(i) + '.jpg')
        i += 1
    print('PDF to Image Conversion Successful!')
    return img_list

# each image is processed, contours are plotted and sorted
def bounding_boxes(img_list, show_boxes):
    boxes = {}
    for curr_img in img_list:
        img = cv2.imread(curr_img)
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        blur = cv2.GaussianBlur(gray, ksize=(9, 9), sigmaX=0)
        # _, thresh = cv2.threshold(blur, 127, 255, cv2.THRESH_BINARY)
        thresh = cv2.adaptiveThreshold(blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 30)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilate = cv2.dilate(thresh, kernel, iterations=4)
        contours, _ = cv2.findContours(dilate, mode=cv2.RETR_EXTERNAL, method=cv2.CHAIN_APPROX_SIMPLE)

        temp = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)
            # print(x, y, w, h)
            if cv2.contourArea(contour) < 10000:
                continue
            temp.append([x, y, w, h])
            if show_boxes:
                cv2.rectangle(img, (x, y), (x + w, y + h), color=(255, 0, 255), thickness=3)
        if show_boxes:
            img = cv2.resize(img, (500, 700), interpolation=cv2.INTER_AREA)
            st.image(image=img, caption=curr_img)
            # cv2.imshow(curr_img, img)
            # cv2.waitKey(0)
        boxes[curr_img] = temp
    print('Contours saved Successfully!')
    return boxes

# text is extracted from each contours stored
def extract_text(boxes):
    pytesseract.pytesseract.tesseract_cmd = r'C:\Program Files\Tesseract-OCR\tesseract.exe'
    text = ''
    for key in boxes:
        img = cv2.imread(key)
        for x, y, w, h in boxes[key]:
            cropped_image = img[y:y + h, x:x + w]
            _, thresh = cv2.threshold(cropped_image, 127, 255, cv2.THRESH_BINARY)
            text += str(pytesseract.image_to_string(thresh, config='--psm 6'))
    print('Text Extraction Completed!')
    return text

# base function
def ocr(filename, show_boxes):
    # FILEOPENOPTIONS = dict(defaultextension='.pdf', initialdir='/', filetypes=[('pdf file', '*.pdf')], title='Select File')
    # filename = filedialog.askopenfilename(**FILEOPENOPTIONS)
    # print(filename)

    if filename:
        img_list = pdf_to_img(filename)
        # print(img_list)
        boxes = bounding_boxes(img_list, show_boxes)
        if not show_boxes:
            text = extract_text(boxes)
            save_here = filedialog.askdirectory(initialdir='/', title='Select Directory')
            if save_here:
                with open(os.path.join(save_here, 'extracted_text.txt'), 'w') as file:
                    file.write(text)
                messagebox.showinfo(title='Success', message='Text stored successfully!')
            else:
                messagebox.showwarning(title='Required', message='Please select a save location.')
    else:
        messagebox.showwarning(title='Required', message='Please select a PDF file!')


# main code
st.title('Text Extraction using OCR')
uploaded_file = st.file_uploader(label='Upload PDF', type='pdf')

if uploaded_file:
    filename = uploaded_file.name
    row0col1, row0col2 = st.columns([1, 1])
    with row0col1:
        st.button(label='Run OCR', on_click=ocr(filename, 0))
    with row0col2:
        st.button(label='Bounding Box', on_click=ocr(filename, 1))


main = Tk()
main.title('OCR')
main.geometry('250x200')

ocr_btn = Button(main, text='Run OCR', command=lambda: ocr(0))
ocr_btn.place(relwidth=0.4, relheight=0.17, x=75, y=40)
box_btn = Button(main, text='Bounding Box', command=lambda: ocr(1))
box_btn.place(relwidth=0.4, relheight=0.17, x=75, y=110)

main.resizable(False, False)
main.mainloop()
