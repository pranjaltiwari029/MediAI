import pytesseract as tess
tess.pytesseract.tesseract_cmd=r'C:\Program Files\Tesseract-OCR\tesseract.exe'
import PIL.Image
import cv2
from pytesseract import Output


myconfig= r"--psm 12 --oem 3"

text=tess.image_to_string(PIL.Image.open("images/text.png"),config=myconfig)
print(text)


# level-2
# img=cv2.imread("images/logo.png")
# height,width,_=img.shape

# boxes=tess.image_to_boxes(img,config=myconfig)


# for box in boxes.splitlines():
#     box=box.split(" ")
#     img=cv2.rectangle(img,(int(box[1]),height -int (box[2])),(int(box[3]),height - int(box[4])),(0,255,0),2)

# cv2.imshow("img",img)
# cv2.waitKey(0)  
    
# #level -3

# img=cv2.imread("images/logo.png")
# height,width,_=img.shape

# data= tess.image_to_data(img,config=myconfig,output_type='dict')

# print(data)
# print(data.keys())
# print(data['text'])

# amount_boxes=len(data['text'])
# for i in range(amount_boxes):
#     if float(data['conf'][i])> 80:
#         (x,y,width,height)= (data['left'][i],data['top'][i],data['width'][i], data['height'][i])
#         img=cv2.rectangle(img,(x,y),(x+width, y+height), (0,255,0), 2)
#         img=cv2.putText(img,data['text'][i],(x,y+height+20),cv2.FONT_HERSHEY_SIMPLEX,0.7,(0,255,0),2,cv2.LINE_AA)
    

# cv2.imshow("img",img)
# cv2.waitKey(0)