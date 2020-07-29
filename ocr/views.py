from django.shortcuts import render
from django.core.files.storage import FileSystemStorage
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
try:
        import Image
except ImportError:
        from PIL import Image
import pytesseract
import copy
import cv2
import os
import imutils
import numpy as np

import json
from fuzzywuzzy import process

steuerbetragliste = ["STEUER", "BTW", "USt."]
steuerbetragliste2 = ["MWST","MwSt. Satz", "BTW%", "USt.%","BRUTTO", "Rechnungsbetrag", "Brutto", "Totaal", "EC-CASH-Total", "Zwischensumme über Alles", "Summe CHF", "Total (EUR)","ZWISCHENSUMME","ZWISCHENRECHNUNG","NETTO","Netto","ExBtw", "Nettowert", "Betrag EUR", "Betrag", "EUR", "UMSATZ", "Gesamtsumme", "EC_Karte", "Bruttorechnungsbetrag"]
mehrwertsteuersatzliste = ["MWST","MwSt. Satz", "BTW%", "USt.%"]
mehrwertsteuersatzliste2 = ["STEUER", "MwSt.", "BTW", "USt.","BRUTTO", "Rechnungsbetrag", "Brutto", "Totaal", "EC-CASH-Total", "Zwischensumme über Alles", "Summe CHF", "Total (EUR)","ZWISCHENSUMME","ZWISCHENRECHNUNG","NETTO","Netto","ExBtw", "Nettowert", "Betrag EUR", "Betrag", "EUR", "UMSATZ", "Gesamtsumme", "EC_Karte", "Bruttorechnungsbetrag"]
endbruttobetragliste = ["BRUTTO", "Rechnungsbetrag", "Brutto", "Totaal", "EC-CASH-Total", "Zwischensumme über Alles", "Summe CHF", "Total (EUR)", "Betrag EUR", "Betrag", "EUR", "UMSATZ", "Gesamtsumme", "EC_Karte", "Bruttorechnungsbetrag"]
endbruttobetragliste2 = ["STEUER", "MwSt.", "BTW", "USt.","MWST","MwSt. Satz", "BTW%", "USt.%","ZWISCHENSUMME","ZWISCHENRECHNUNG","NETTO","Netto","ExBtw", "Nettowert"]
endnettobetragliste = ["ZWISCHENSUMME","ZWISCHENRECHNUNG","NETTO","Netto","ExBtw", "Nettowert"]
endnettobetragliste2 = ["STEUER", "MwSt.", "BTW", "USt.","MWST","MwSt. Satz", "BTW%", "USt.%","BRUTTO", "Rechnungsbetrag", "Brutto", "Totaal", "EC-CASH-Total", "Zwischensumme über Alles", "Summe CHF", "Total (EUR)", "Betrag EUR", "Betrag", "EUR", "UMSATZ", "Gesamtsumme", "EC_Karte", "Bruttorechnungsbetrag"]
steuerbetrag = ""
mehrwertsteuersatz = ""
endbruttobetrag = ""
endnettobetrag = ""
datum = ""
hilfszahl1 = 0
hilfzahl2 = 0
hilfsergebnis = 0
textfile = []
hilfliste = []
max_length = 0
steuerbetragisFalse = True
mehrwertsteuersatzisFalse = True
endbruttobetragisFalse = True
endnettobetragisFalse = True
datumisFalse = True
airbnbisFalse = True
queryliste = ["","°","^","!","²","§","³","$","%","&","/","{","(","[",")","]","=","}","?","´","´","+","*","~","'","#","<",">","|",",",";",":",".","*","-","+","¢","¥","©","‘","(+)","'¢","*%","@","_","™","—","--","\}","||","’"]


@login_required
def home(request):
    return render(request, 'ocr/home.html', { 'title': 'Startseite' })

@login_required
def upload(request):
    context = {}
    if request.method == 'POST':
        #Upload des originales Bildes
        uploaded_file = request.FILES['document']
        fs = FileSystemStorage()
        #Speichern der hochgeladenen Datei
        filename = fs.save(request.user.get_username()+'/'+uploaded_file.name, uploaded_file)
        rohname = os.path.basename(filename)
        #URL der abgespeicherten Datei, um in upload.html anzeigen zu können
        context['url'] = fs.url(filename)

		#Überprüfung des Dateityps und Löschung, falls es nicht JPG oder PNG ist
        if not rohname.lower().endswith(('.png','.jpg')):
            os.remove('media/'+request.user.get_username()+'/'+uploaded_file.name)
            context['dateityp_fehler'] = 'Dieser Dateityp wird nicht unterstützt.'
            return render(request, 'ocr/upload.html', context)

        #Erstellen einer Kopie für OCR
        #Zuerst wird geprüft, ob temp_img bereits besteht
        #falls ja, dann wird die alte Datei gelöscht und die neue gespeichert
        temp_img = copy.copy(uploaded_file)
        if os.path.exists('media/temp_img.jpg'):
            os.remove('media/temp_img.jpg')
            fs.save('temp_img.jpg', temp_img)

        else:
            fs.save('temp_img.jpg', temp_img)

        #Bearbeitung des Bildes zur besseren Texterkennung
        img_edit()

        #Auslesen des Textes über Tesseract
        erkannter_text = pytesseract.image_to_string(Image.open('media/temp.jpg'))

        #Abspeichern des erkannten Textes in einer TXT-Datei
        handle = open('media/'+request.user.get_username()+'/'+rohname+'_ocr_results.txt', 'a+')
        handle.write(erkannter_text)
        handle.close()

        #Auslesen des erkannten Textes, um diesen in upload.html anzeigen zu können
        #with open('media/'+request.user.get_username()+'/'+rohname+'_ocr_results.txt') as f:
        #    inhalt = f.read()
        #    print(inhalt)
        #f.close()

        #context['ocr_result'] = inhalt
        context['text'] = 'Folgende Informationen wurden erkannt:'



        #Auslesen der relevanten Informationen:

        #Zurücksetzen aller Variablen
        def start():
            global steuerbetrag
            global mehrwertsteuersatz
            global endbruttobetrag
            global endnettobetrag
            global datum
            global hilfszahl1
            global hilfzahl2
            global hilfsergebnis
            global textfile
            global hilfliste
            global max_length
            global steuerbetragisFalse
            global mehrwertsteuersatzisFalse
            global endbruttobetragisFalse
            global endnettobetragisFalse
            global datumisFalse
            global airbnbisFalse
            steuerbetrag = ""
            mehrwertsteuersatz = ""
            endbruttobetrag = ""
            endnettobetrag = ""
            datum = ""
            hilfszahl1 = 0
            hilfzahl2 = 0
            hilfsergebnis = 0
            textfile = []
            hilfliste = []
            max_length = 0
            steuerbetragisFalse = True
            mehrwertsteuersatzisFalse = True
            endbruttobetragisFalse = True
            endnettobetragisFalse = True
            datumisFalse = True
            airbnbisFalse = True


        def get_matches(query, choices, limit=3):
            if query in queryliste:
                return False
            else:
                results = process.extractOne(query, choices)
                if int(results[1])>90 and int(results[1])<=100:
                    return True
                else:
                    return False

        #Überprüft das Datum
        def checkdatum(wert):
            if (wert == 1 or wert == 3) and int(datum[:1]) <= 31 and int(datum[3:4]) <= 12 and (int(datum[6:])>1900 or int(datum[6:])>18):
                #print("Datum kann stimmen")
                #print(datum)
                datumisFalse = False
            elif wert == 2 and int(datum[:4]) >1900 and int(datum[5:6]) <= 12 and int(datum[8:]) <= 31:
                #print("Datum kann stimmen")
                #print(datum)
                datumisFalse = False
            else:
                print("Beim Datum ist ein Fehler aufgetreten")
                print(datum)

        #findet Airbnb endbruttobetrag heraus
        def checkAirbnb(text):
            for c in range(0,len(text)):
                global airbnbisFalse
                if "€" in text[-c]:
                    endbruttobetrag = text[-c].strip("€")
                    print("Bei Airbnb wird nur Endbruttobetrag erkannt: " + endbruttobetrag)
                    airbnbisFalse = False

                    ausgabe =[]
                    ausgabe.append(endbruttobetrag)

                    #Ausgabe als JSON, aber noch ohne POST an externes System
                    y = json.dumps(ausgabe)
                    print(y)

                    context['airbnb'] = endbruttobetrag
                    break
                #else:
                    #print("Endbruttobetrag wurde nicht erkannt")

        def checkFloat(wert, symbol):

            global steuerbetrag
            global mehrwertsteuersatz
            global endbruttobetrag
            global endnettobetrag
            zahlenliste = ["0","1","2","3","4","5","6","7","8","9"]

            if wert[0] =="," or wert[0] ==".":
                wert = wert.replace(",", ".")
                wert = "0" + wert
            if wert[0] not in zahlenliste:
                while(wert[0] not in zahlenliste):
                    wert = wert[1:]
            if symbol == "s":
                steuerbetrag = wert
                steuerbetragisFalse = False
            elif symbol == "m":
                mehrwertsteuersatz = wert
                mehrwertsteuersatzisFalse = False
            elif symbol == "b":
                endbruttobetrag = wert
                endbruttobetragisFalse = False
            elif symbol == "n":
                endnettobetrag = wert
                endnettobetragisFalse = False

        #Prüft ob gefundene Werte richtig sind
        def checkBetrag(mehrwert, steuer, brutto, netto):

            global steuerbetrag
            global mehrwertsteuersatz
            global endbruttobetrag
            global endnettobetrag
            global steuerbetragisFalse
            global mehrwertsteuersatzisFalse
            global endbruttobetragisFalse
            global endnettobetragisFalse


            if not steuerbetragisFalse:
                checkFloat(steuer, "s")

            if not mehrwertsteuersatzisFalse:
                checkFloat(mehrwert, "m")

            if not endbruttobetragisFalse:
                checkFloat(brutto, "b")

            if not endnettobetragisFalse:
                checkFloat(netto, "n")

            if steuerbetragisFalse and endbruttobetragisFalse == False and endnettobetragisFalse == False:
                steuerbetrag = float(endbruttobetrag) - float(endnettobetrag)
                steuerbetragisFalse = False

            if mehrwertsteuersatzisFalse and endbruttobetragisFalse == False and endnettobetragisFalse == False:
                mehrwertsteuersatz = 1 - (float(endbruttobetrag)/float(endnettobetrag))
                mehrwertsteuersatzisFalse = False

            if endbruttobetragisFalse and steuerbetragisFalse == False and endnettobetragisFalse == False:
                endbruttobetrag = endnettobetrag + steuerbetrag
                endbruttobetragisFalse = False

            if endnettobetragisFalse and endbruttobetragisFalse == False and steuerbetragisFalse == False:
                endnettobetrag = endbruttobetrag - steuerbetrag
                endnettobetragisFalse = False

            if endbruttobetragisFalse == False and endnettobetragisFalse == False and steuerbetragisFalse == False and mehrwertsteuersatzisFalse == False and round(float(endnettobetrag) + float(steuerbetrag), 2) == round(float(endbruttobetrag),2):
                print("Alles richtig erkannt")
                steuerbetrag = round(float(steuerbetrag), 2)
                if "%" not in str(mehrwertsteuersatz):
                    mehrwertsteuersatz = round(float(mehrwertsteuersatz), 2)
                    mehrwertsteuersatz = str(mehrwertsteuersatz)[2:] + "%"
                endbruttobetrag = round(float(endbruttobetrag), 2)
                endnettobetrag = round(float(endnettobetrag), 2)
            else:
                print("Bei der Erkennung kam es zu einem unerwarteten Fehler")
                context['fehler'] = 'Bei der Erkennung kam es zu einem unerwarteten Fehler'


            ausgabe =[]
            ausgabe.append(mehrwertsteuersatz)
            ausgabe.append(steuerbetrag)
            ausgabe.append(endnettobetrag)
            ausgabe.append(endbruttobetrag)
            ausgabe.append(datum)
            context['summe'] = endbruttobetrag
            context['mwstsatz'] = mehrwertsteuersatz
            context['mwstwert'] = steuerbetrag
            context['nettobetrag'] = endnettobetrag
            context['datum'] = datum

            #Ausgabe als JSON, aber noch ohne POST an externes System
            y = json.dumps(ausgabe)

            print(y)

        #Überprüft Hilflisten Bereich auf alle verfügbaren Parameter
        def checkHilfliste(hilfliste):
            L1=[]
            for d in range(0,round(len(hilfliste)/2)):
                L1.append(hilfliste[d])
            L2 = []
            for e in range(round(len(hilfliste)/2),len(hilfliste)):
                L2.append(hilfliste[e])
            global steuerbetragisFalse
            global mehrwertsteuersatzisFalse
            global endbruttobetragisFalse
            global endnettobetragisFalse
            global max_lenght
            global steuerbetrag
            global mehrwertsteuersatz
            global endbruttobetrag
            global endnettobetrag
            max_length = len(L1)
            f = 0

            while (f < max_length):

                w = f
                f = f +1

                if mehrwertsteuersatzisFalse:
                    if get_matches(str(L1[w]), mehrwertsteuersatzliste):
                        if "%" in L2[w]:
                            mehrwertsteuersatz = L2[w]
                            L1.remove(L1[w])
                            L2.remove(L2[w])
                        else:
                            mehrwertsteuersatz = L2[w+1]
                            L1.remove(L1[w])
                            L2.remove(L2[w])
                            L2.remove(L2[w])

                        f = 0
                        max_length = max_length - 1
                        mehrwertsteuersatzisFalse = False
                        #print("Mehrwersteuersatz = " + mehrwertsteuersatz)

                if endbruttobetragisFalse:
                    if get_matches(str(L1[w]), endbruttobetragliste):
                        endbruttobetrag = L2[w]
                        L1.remove(L1[w])
                        L2.remove(L2[w])
                        endbruttobetragisFalse = False
                        #print("Endbruttobetrag: " + endbruttobetrag)

                        f = 0
                        max_length = max_length -1

                if endnettobetragisFalse:
                    if get_matches(str(L1[w]), endnettobetragliste):
                        endnettobetrag = L2[w]
                        L1.remove(L1[w])
                        L2.remove(L2[w])
                        endnettobetragisFalse = False
                        #print("Endnettobetrag: " + endnettobetrag)

                        f = 0
                        max_length = max_length -1

                if steuerbetragisFalse:
                    if get_matches(str(L1[w]), steuerbetragliste):
                        steuerbetrag = L2[w]
                        L1.remove(L1[w])
                        L2.remove(L2[w])
                        steuerbetragisFalse = False
                        #print("Steuerbetrag: " + steuerbetrag)

                        f = 0
                        max_length = max_length -1

            del hilfliste [:]

        with open('media/'+request.user.get_username()+'/'+rohname+'_ocr_results.txt', "r") as file:
            global steuerbetrag
            global mehrwertsteuersatz
            global endbruttobetrag
            global endnettobetrag
            global datum
            for line in file:
                data = line.strip().split(" ")
                #print(data)

                for i in range(0,len(data)):
                    textfile.append(data[i])
                    #print(data[i])

            for w in range(0,len(textfile)):
                #print(textfile[w])
                if (len(textfile[w]) == 10 or len(textfile[w]) == 8) and textfile[w][2] == "."and textfile[w][5] == ".":
                    datum = textfile[w]
                    datumisFalse = False
                    checkdatum(1)
                elif (len(textfile[w]) == 10 or len(textfile[w]) == 8) and textfile[w][2] == "-"and textfile[w][5] == "-":
                    datum = textfile[w]
                    datumisFalse = False
                    checkdatum(1)
                elif len(textfile[w]) == 10 and textfile[w][4] == "."and textfile[w][7] == ".":
                    datum = textfile[w]
                    datumisFalse = False
                    checkdatum(2)
                elif len(textfile[w]) == 10 and textfile[w][4] == "-"and textfile[w][7] == "-":
                    datum = textfile[w]
                    datumisFalse = False
                    checkdatum(2)

                if "Airbnb" in textfile[w] or "airbnb" in textfile[w]:
                    checkAirbnb(textfile)
                    break

                if steuerbetragisFalse:
                    if get_matches(str(textfile[w]), steuerbetragliste):

                        #Überprüfen ob im nächsten Feld eine Zahl hinterlegt ist
                        if "1" in textfile[w+1] or "2" in textfile[w+1] or "3" in textfile[w+1] or "4" in textfile[w+1] or "5" in textfile[w+1] or "6" in textfile[w+1] or "7" in textfile[w+1] or "8" in textfile[w+1] or "9" in textfile[w+1]:
                            steuerbetrag = textfile[w+1]
                            #print(steuerbetrag)
                            break

                        for b in range(0,len(steuerbetragliste2)):
                            if steuerbetragliste2[b] in textfile[w+1]:
                                c  = w
                                while(textfile[c]!=""):
                                    hilfliste.append(textfile[c])
                                    c += 1

                        checkHilfliste(hilfliste)


                if mehrwertsteuersatzisFalse:
                    if get_matches(str(textfile[w]), mehrwertsteuersatzliste):
                        #checkMehrwertsteuersatz(textfile)

                        #Überprüfen ob im nächsten Feld eine Zahl hinterlegt ist
                        if "1" in textfile[w+1] or "2" in textfile[w+1] or "3" in textfile[w+1] or "4" in textfile[w+1] or "5" in textfile[w+1] or "6" in textfile[w+1] or "7" in textfile[w+1] or "8" in textfile[w+1] or "9" in textfile[w+1]:
                            mehrwertsteuersatz = textfile[w+1]
                            #print(mehrwertsteuersatz)
                            break

                        for b in range(0,len(mehrwertsteuersatzliste2)):
                            if mehrwertsteuersatzliste2[b] in textfile[w+1]:
                                c  = w
                                while(textfile[c]!=""):
                                    hilfliste.append(textfile[c])
                                    c += 1

                        checkHilfliste(hilfliste)

                if endbruttobetragisFalse:
                    if get_matches(str(textfile[w]), endbruttobetragliste):
                        #Überprüfen ob im nächsten Feld eine Zahl hinterlegt ist
                        if "1" in textfile[w+1] or "2" in textfile[w+1] or "3" in textfile[w+1] or "4" in textfile[w+1] or "5" in textfile[w+1] or "6" in textfile[w+1] or "7" in textfile[w+1] or "8" in textfile[w+1] or "9" in textfile[w+1]:
                            endbruttobetrag = textfile[w+1]
                            #print(endbruttobetrag)
                            break

                        for b in range(0,len(endbruttobetragliste2)):
                            if endbruttobetragliste2[b] in textfile[w+1]:
                                c  = w
                                while(textfile[c]!=""):
                                    hilfliste.append(textfile[c])
                                    c += 1

                        checkHilfliste(hilfliste)

                if endnettobetragisFalse:
                    if get_matches(str(textfile[w]),endnettobetragliste):

                        #Überprüfen ob im nächsten Feld eine Zahl hinterlegt ist
                        if "1" in textfile[w+1] or "2" in textfile[w+1] or "3" in textfile[w+1] or "4" in textfile[w+1] or "5" in textfile[w+1] or "6" in textfile[w+1] or "7" in textfile[w+1] or "8" in textfile[w+1] or "9" in textfile[w+1]:
                            endnettobetrag = textfile[w+1]
                            #print(endnettobetrag)
                            break

                        for b in range(0,len(endnettobetragliste2)):
                            if endnettobetragliste2[b] in textfile[w+1]:
                                c  = w
                                while(textfile[c]!=""):
                                    hilfliste.append(textfile[c])
                                    c += 1

                        checkHilfliste(hilfliste)

            if airbnbisFalse:
                checkBetrag(mehrwertsteuersatz, steuerbetrag, endbruttobetrag, endnettobetrag)
        start()
    return render(request, 'ocr/upload.html', context)

def about(request):
    return render(request, 'ocr/about.html', { 'title': 'About'})

def img_edit():
    image = cv2.imread('media/temp_img.jpg')
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    blurred = cv2.GaussianBlur(gray, (5, 5), 0)
    thresh = cv2.threshold(blurred,0,255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)[1]
    cv2.imwrite('media/temp.jpg', thresh)
