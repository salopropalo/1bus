# coding^utf8
import copy
import re
import socket
import math
import xlwt
import openpyxl
from openpyxl.styles import Font
import datetime
from reportlab.pdfgen import canvas
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.pdfbase import pdfmetrics
from PyPDF2 import PdfMerger
import os


class rashet:
    def __init__(self, atr, fname, PP, number):
        self.index = 0
        self.N_zak = atr[0]
        self.N_proj = atr[1]
        self.Name_proj = atr[2]
        self.fname = fname      #Имя файла для расчета
        self.spisok_filov = []
        self.spis_kompl = {'profil': [], 'st_izd': []}
        self.spisok_dla_mater = {}  # словарь для расчета материалов
        self.Proiz = PP     # Выбранное производство, 1-Кама, 0-Солярис
        self.nom_shet = number

    def zapusk(self):
        print('Начало')
        #Создаем словарь для записи комплектующих
        # nom_shet = int(re.findall(r'\w+', open('nom_rashet.txt', "r").readlines()[-1])[0]) + 1
        line = '№' + str(self.nom_shet) + '\n' + '' + str(socket.gethostname())    # строка с данными о компьютере и дате расчета

        # словарь для контрольной ведомости
        KtrSlvr = InOut(self.fname, 'k').zapusk()

        # получаем список для запуска
        di = InOut(self.fname, 'n').zapusk()
        # print(di)
        sklad = {}  # словарь для создания контрольной ведомости
        self.index = 0

        for i in di:
            RabVed = {}      # Словарь для раб. ведомости
            SpisKomplekt = []  # список для направляющих, сухарей, фланцев.
            self.spisok_dla_mater[i] = {'seria': 'B', 'material': 'Al', 'nominal': 630, 'dlina': 0,
                                        'Nstik': 0, 'Nsekc': 0, 'Nkon_zag': 0, 'Nflanc': 0, 'Lsvar_izd': 0}

            for input_data in di[i]:  # начинаем перебор построчно
                self.spisok_dla_mater[i]['material'] = input_data[2]
                self.spisok_dla_mater[i]['nominal'] = input_data[4]
                self.spisok_dla_mater[i]['seria'] = input_data[0]
                data = calc(input_data, self.Proiz).calc_nom()
                itog = calculation(data, input_data, self.index, RabVed, SpisKomplekt,
                                   self.spis_kompl, self.spisok_dla_mater[i]).choice()

                if itog[0] == False:
                    print('Ошибка: нестандартная секция')
                    itog[2]['категория'] = 'спецификация'
                    sklad[self.index] = itog[2]
                else:
                    self.index = itog[1]
                    RabVed = itog[2]
                    self.komplekt = itog[3]

                self.spisok_dla_mater[i] = copy.deepcopy(itog[4])
            RabVed = line_raskroi.techno(self.komplekts(SpisKomplekt, RabVed))
            self.spisok_filov.append(writing_to_exl([self.N_zak, self.N_proj, self.Name_proj, self.Proiz], i, RabVed, line, 'vedomost').setting_exl())

        sklad = InOut([sklad, KtrSlvr], 'o').zapusk()
        '''делаем файл эксель с контр.вед. и получим имя файла и список'''
        ret = writing_to_exl([self.N_zak, self.N_proj, self.Name_proj, self.Proiz], False, sklad, line, 'upakovka').setting_exl()
        print('ret', ret)
        self.spisok_filov.append(ret[0])        # добавляем в список файлов для удаления имя контрольной ведомсти

        pdf_creator = to_pdf_reportlab(ret[1], self.N_zak)
        for sss in pdf_creator.pdf_files:
            self.spisok_filov.append(sss)

        return [self.spisok_filov, self.spisok_dla_mater]

    def komplekts(self, spisok, itog):
        ''' Модуль eto нужен исключительно для счета направляющих и сухарей '''
        print('РАСЧЕТ НАПРАВЛЯЮЩИХ И СУХАРЕЙ')
        # print(spisok)
        spisok_strok = sorting('0', spisok, False, 5, False, None).addition()
        # print(spisok_strok)

        for i in spisok_strok:
            dat = calc(['B', '55', i[1], i[0], i[2], '', i[3], '', '', i[4]], self.Proiz).calc_nom()
            self.index += 1
            kol = int(i[4])
            det = Detali(0, dat, '', kol, [0, 0], [0, 0, 0], self.spis_kompl)
            det = getattr(det, i[3])()  # создаем список
            det.insert(0, '-')          # добавляем в список
            det.insert(0, self.index)   # добавляем в список
            det.append(kol)             # добавляем в конец списка
            #print('det', det)
            itog[det[0]] = {'Серия': det[2], 'ip': det[3], 'Материал': det[4], 'In': det[5],
                                 'Кол. пров.': det[6], 'Наименование': det[7], 'Обозначение': det[8], 'Разм.L': det[9],
                                 'Разм.L1': det[10], 'Разм.A': det[11], 'Разм.B': det[12], 'Разм.C': det[13],
                                 'количество': det[14], 'тип': '', 'категория': 'ведомость'}
        return itog


class calculation:
    def __init__(self, data, input_data, index, itog, komplekt, spis_kompl, spisok_dla_mater):
        self.dat = data                                                     # обработанный словарь вводных данных
        self.input_data = input_data                                        # начальный список вводных данных
        self.index = index                                                  # номер счетчика
        self.itog = itog                                                    # итоговый список деталей и сборок
        self.tip = re.findall(r'\d', str(self.dat['тип']))                  # ТИП список [1, 1]
        self.os = re.findall(r'\d+', self.dat['размер'])                    # список размеров по осям
        self.length_OS = self.listsum(self.os)                              # длина секции по осям
        self.kol_os = len(self.os)                                          # вычисляем количество осей
        self.komplekt = komplekt                                            # счетчик комплектующих
        self.spis_kompl = spis_kompl                                        # словарь со списками комплектующих
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.X = '-'
        self.Y = '-'
        self.L = '-'
        self.L1 = '-'
        self.spisok_dla_mater = spisok_dla_mater                            # для расчета материалов

    def listsum(self, numList):
        ''' Модуль для разделения в размерах размеры секции от прочих параметров '''
        theSum = 0

        if self.dat['Обозначение'] in ['tsv', 'ом']:
            numList = re.findall(r'[^\s]+', re.sub(r'[()]', ' ', self.dat['размер']))[0]

        for i in numList:
            theSum = theSum + int(i)

        return theSum

    def choice(self):
        print('НАЧАЛО РАСЧЕТА СЕКЦИИ: ', self.dat['Материал'], self.dat['Кол. пров.'],
              self.dat['Обозначение'], self.dat['In'], self.dat['размер'])

        section = {'п': 'p', 'уг': 'ug', 'ув': 'uv', 'зг': 'z_g', 'зв': 'z_v', 'кп': 'k_p', 'кл': 'k_l',
                   'ом': 'om', 'омф': 'omf', 'пф': 'p', 'згф': 'z_g', 'звф': 'z_v', 'увф': 'uv', 'угф': 'ug',
                   'тв': 'tv', 'тс': 'ts', 'pt': 'p', 'pf': 'p', 'pfk': 'p', 'ug': 'ug', 'ugf': 'ug',
                   'uv': 'uv', 'uvf': 'uv', 'kp': 'k_p', 'kl': 'k_l', 'kpfuv': 'k_p', 'klfuv': 'k_l',
                   'kpfug': 'k_p', 'klfug': 'k_l',
                   'zv': 'z_v', 'zvf': 'z_v',
                   'zg': 'z_g', 'zgf': 'z_g', 'tv': 'tv', 'tg': 'tg', 'tsv': 'ts', 'sb': 'sb',
                   'сб': 'sb', 'pr': 'om', 'prf': 'omf', 'kz': 'kz', 'pn': 'pn', 'om': 'bom',
                   'omf': 'bom', 'ks': 'ks', 'ksb': 'ksb', 'pp': 'pp', 'sk': 'sk'}

        if str(self.dat['Обозначение']) not in section:
            znach = False
        else:
            znach = getattr(calculation, section[str(self.dat['Обозначение'])])(self)  # запускаем выбранную секцию

        if znach == True:
            print('ЗАВЕРШЕНИЕ РАСЧЕТА СЕКЦИИ')
            return [True, self.index, self.itog, self.komplekt, self.spisok_dla_mater]
        else:
            print('Чтото пошло не так rashet_sekcii 160')
            return [False, self.index, self.dat, self.komplekt, self.spisok_dla_mater]

    def welded_part(self, svar_det):
        print('РАСЧЕТ СВАРНОЙ ДЕТАЛИ', '| Обознач:', svar_det[0])
        self.index += 1
        index = self.index
        #print(svar_det)
        kol = int(svar_det[2]) * int(self.dat['количество'])
        #one_symbol = re.findall(r'\w+', svar_det[0])[0]
        last_symbol = re.findall(r'\w+', svar_det[0])[-1]
        W_line1 = []
        nominal = self.dat['In']

        # if one_symbol == 'К':
        #     oboznach = 'Крышка СБ'
        #     nominal = '-'
        # elif one_symbol == 'КВ':
        #     oboznach = 'Крышка с выступом СБ'
        #     nominal = '-'
        # elif one_symbol == 'С':
        #     oboznach = 'Стенка СБ'
        #     nominal = self.dat['In']
        # elif one_symbol == 'Ш':
        #     oboznach = 'Шина СБ'
        #     nominal = self.dat['In']
        # else:
        #     oboznach = 'Сварная деталь СБ'
        #     nominal = self.dat['In']

        if last_symbol == 'З':
            svar_det[0] = svar_det[0] + ' (Зеркальная)'

        A = '-'
        B = '-'
        C = '-'
        X = '-'
        Y = '-'
        L = '-'
        L1 = '-'

        if self.dat['Обозначение'] in ['тв', 'tv']:
            if svar_det[0] in ['С-СД14', 'С-СД11']:
                if self.dat['In'] in [3200, 4000, 5000]:
                    C = str(float(svar_det[3][2][0]) - float(self.dat['расстояние от оси до корпуса'])
                            - float(self.dat['ширина стенки']) - 1)
                else:
                    C = str(float(svar_det[3][2][0]) - float(self.dat['расстояние от оси до корпуса'])
                            - float(self.dat['ширина стенки']) / 2)
            elif svar_det[0] in ['Ш-СД22', 'Ш-СД22-З', 'Ш-СД21', 'Ш-СД21-З', 'Ш-СД15', 'Ш-СД15-З', 'Ш-СД16',
                                 'Ш-СД16-З']:
                if self.dat['In'] in [3200, 4000, 5000]:
                    C = str(float(svar_det[3][2][0]) - float(self.dat['расстояние от оси до шины'])
                            - float(self.dat['ширина шины']) - 3)
                else:
                    C = str(float(svar_det[3][2][0]) - float(self.dat['расстояние от оси до шины'])
                            - float(self.dat['ширина шины']) / 2)
            else:
                C = '-'
            L = str('*'.join(self.os))
        elif self.dat['Обозначение'] in ['тс', 'tsv']:
            L = self.dat['Обозначение'] + re.findall(r'[^\s]+', re.sub(r'[()]', ' ', self.dat['размер']))[0]
            C = '-'
        elif self.dat['Обозначение'] in ['ом', 'pr', 'омф', 'prf']:

            if int(self.tip[0]) in [1, 2]:
                A = str(svar_det[5][0])
            elif int(self.tip[0]) in [3, 4]:
                A = str(svar_det[5][0])
                B = str(svar_det[5][1])
            elif int(self.tip[0]) in [5, 6]:
                A = str(svar_det[5][0])
                B = str(svar_det[5][1])
                C = str(svar_det[5][1])

            del svar_det[5]
            #print(self.os)
            L = str(float(self.os[0]) - float(self.dat['расстояние от оси до шины']) * 2)
        elif self.dat['Обозначение'] in ['уг', 'ug']:
            C = self.C
        else:
            C = '-'

        if self.dat['Обозначение'] in ['п', 'уг', 'ув', 'зг', 'зв', 'кп', 'кл', 'згф', 'звф', 'увф', 'угф', 'тв', 'тс',
                                       'pt', 'ug', 'uv', 'zg', 'zv', 'kp', 'kl', 'zgf', 'zvf', 'uvf', 'ugf', 'tv',
                                       'tsv', 'sk']:
            nom_two = [A, B, C]
            nom_one = 0
            # print(len(svar_det))

            for i in range(3, len(svar_det)):
                if svar_det[i][0] in ['u', 'ugol', 'ugol1', 'ugol2', 'ugol1_2', 'ugol_2', 'ugol2-z']:
                    result = self.detail(svar_det[i] + self.os, '')
                    W_line1.append(result)
                    continue
                else:
                    result = self.detail(svar_det[i], '')
                    nom_two[nom_one] = result[8]
                    W_line1.append(result)
                    nom_one += 1

            A = nom_two[0]
            B = nom_two[1]
            C = nom_two[2]
            # print(A, B, C)

        else:   # для ОМ
            nom_one = 0

            for i in range(3, len(svar_det)):
                result = self.detail(svar_det[i], 's')
                W_line1.append(result)
                nom_one += 1

        W_line = [[index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], nominal,
                   self.dat['Кол. пров.'], svar_det[1], svar_det[0], L, L1, A, B, C, kol,
                   'ведомость']]
        W_line = W_line + W_line1
        #print('W_line', W_line)
        return W_line

    def detail(self, detal, coating):
        """ detal  это список атрибутов детали: [Обозначение, количество, раземр по осям]
            coating это атрибут покрытия (окрашенно "s", или не окрашено)."""
        print('РАСЧЕТ ДЕТАЛИ', '| Обознач:', str(detal[0]))

        if detal[0] in ['n', 'fl_100', 'fl_130', 'zts', 'sux', 'mfazcentr', 'torcentr', 'fl']:
            self.komplekt.append([self.dat['Кол. пров.'], self.dat['Материал'], self.dat['In'],
                                  detal[0], detal[1] * int(self.dat['количество'])])
            return 0
        else:
            #print(self.index)
            self.index = self.index + 1
            kol = detal[1] * self.dat['количество']
            print('detal', detal)
            itog = getattr(Detali(detal[2], self.dat, coating, kol, self.tip,
                                  [self.A, self.B, self.C], self.spis_kompl), detal[0])()
            # print('itog', itog)
            itog.insert(0, self.index)
            itog.append(kol)
            itog.append('ведомость')
            #print('ИТОГ: ', itog)
            return itog

    # Вывод на печать
    def prints(self, itog):
        print('ЗАПИСЬ В СПИСОК')
        for i in itog:
            self.itog[i[0]] = {'Серия': i[1], 'ip': i[2], 'Материал': i[3], 'In': i[4], 'Кол. пров.': i[5],
                               'Наименование': i[6], 'Обозначение': i[7], 'Разм.L': i[8], 'Разм.L1': i[9],
                               'Разм.A': i[10], 'Разм.B': i[11], 'Разм.C': i[12], 'количество': i[13],
                               'тип': self.dat['тип'], 'стандарт': self.dat['стандарт'],
                               'категория': i[14]}

    # раысчет стыков
    def sb(self):
        #print(self.index)
        self.index += 1
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'sb',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]
        detali = [['ss', 2, self.os],
                  ['tp', self.dat['количество токопроводящих пластин'], self.os],
                  ['vtulka', self.dat['количество втулок'], self.os],
                  ['ksb', 2, self.os],
                  ['dp', self.dat['количество демпферов'], self.os],
                  ['izol_k', 2, self.os],
                  ['izol_s', self.dat['количество средних изоляторов'], self.os]]

        if self.dat['In'] in [3200, 4000, 5000]:
            detali[5][1] = detali[5][1] * 2
            detali[6][1] = detali[6][1] * 2
        elif self.dat['In'] in [3200, 4000, 5000]:
            detali[5][1] = detali[5][1] * 3
            detali[6][1] = detali[6][1] * 3

        self.spisok_dla_mater['Nstik'] = self.spisok_dla_mater['Nstik'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        for j in detali:
            itog_det = self.detail(j, '')
            itog.append(itog_det)
        self.prints(itog)
        return True

    # прямые и фланцы
    def p(self):
        #print('Расчет прямой секции:')
        self.L = self.os[0]
        self.index = self.index + 1

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество']) * int(self.L) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        if (self.index) == 500:
            self.dat['тип'] = 0.5
        elif int(self.L) == 1000:
            self.dat['тип'] = 1.0
        elif int(self.L) == 1500:
            self.dat['тип'] = 1.5
        elif int(self.L) == 2000:
            self.dat['тип'] = 2.0
        elif int(self.L) == 2500:
            self.dat['тип'] = 2.5
        elif int(self.L) == 3000:
            self.dat['тип'] = 3.0
        elif int(self.L) > 500 and int(self.L) < 1000:
            self.dat['тип'] = 0.9
        elif int(self.L) > 1000 and int(self.L) < 1500:
            self.dat['тип'] = 1.4
        elif int(self.L) > 1500 and int(self.L) < 2000:
            self.dat['тип'] = 1.9
        elif int(self.L) > 2000 and int(self.L) < 2500:
            self.dat['тип'] = 2.4
        elif int(self.L) > 2500 and int(self.L) < 3000:
            self.dat['тип'] = 2.9

        self.B = int(self.dat['межфазное расстояние фланца'])

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'pt',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]
#B
        if self.dat['Серия'] in ['Е3', 'B']:

            if str(self.dat['Кол. пров.']) in ['4', '3+1']:
                detali = [['kv', 2, self.os[0]], ['c', 2, self.os[0]], ['s1', 2, self.os[0]], ['s2', 2, self.os[0]],
                          ['n', 4], ['sux', 4]]

                if self.dat['Обозначение'] in ['пф', 'pf', 'pfk']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    itog[0][7] = 'pf'
                    detali[2][0] = 's17'
                    detali[3][0] = 's18'
                    detali[4][1] = 2
                    if self.dat['межфазное расстояние фланца'] in [100, '100']:
                        detali.append(['fl_100', 2])
                    else:
                        detali.append(['fl_130', 2])

                if self.dat['In'] in [2500]:
                    detali.pop(0)
                    detali.insert(0, ['k', 2, self.os[0]])
                elif self.dat['In'] in [2600, 3200, 4000, 5000]:
                    detali.pop(0)
                    detali.insert(0, ['k', 2, self.os[0]])
                    for i in [1, 2, 3]:
                        detali[i][1] = 4
                    detali.insert(1, ['kc', 1, self.os[0]])
                elif self.dat['In'] in [6400]:
                    detali.pop(0)
                    detali.insert(0, ['k', 2, self.os[0]])
                    for i in range(1, 4):
                        detali[i][1] = 6
                    detali.insert(1, ['kc', 2, self.os[0]])

            else:   # 3-х проводной
                detali = [['k', 2, self.os[0]], ['c', 2, self.os[0]], ['s1', 2, self.os[0]], ['s', 1, self.os[0]],
                          ['n', 4], ['sux', 4]]

                if self.dat['Обозначение'] in ['пф', 'pf', 'pfk']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    itog[0][7] = 'pf'
                    detali[2][0] = 's17'
                    detali[4][1] = 2
                    if self.dat['межфазное расстояние фланца'] in [100, '100']:
                        detali.append(['fl_100', 2])
                    else:
                        detali.append(['fl_130', 2])
#CR
        elif self.dat['Серия'] in ['CR1', 'CR2']:

            if str(self.dat['Кол. пров.']) in ['4', '3+1']:
                detali = [['s_01', 4, self.os[0]], ['torcentr', 2], ['mfazcentr', round(int(self.L) / 400, 0)]]

                if self.dat['Обозначение'] in ['пф', 'pf', 'pfk']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    itog[0][7] = 'pf'
                    detali[0][0] = 's36'
                    detali[0][1] = 2
                    detali.append(['s37', 2, self.os[0]])
                    if self.dat['межфазное расстояние фланца'] in [100, '100']:
                        detali.append(['fl_100', 2])
                    else:
                        detali.append(['fl_130', 2])

                if self.dat['In'] in [3200, 4000, 5000]:
                    detali.insert(0, ['s_01', 8, self.os[0]])
                elif self.dat['In'] in [6400]:
                    detali.insert(0, ['s_01', 12, self.os[0]])

            else:  # 3-х проводной
                detali = [['s_01', 3, self.os[0]], ['torcentr', 2], ['mfazcentr', round(int(self.L) / 0.4)]]

                # нет чертежей для пф для заливки
                if self.dat['Обозначение'] in ['пф', 'pf', 'pfk']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                    itog[0][7] = 'pf'
                    detali[2][0] = 's17'
                    detali[4][1] = 2
                    if self.dat['межфазное расстояние фланца'] in [100, '100']:
                        detali.append(['fl_100', 2])
                    else:
                        detali.append(['fl_130', 2])

        for i in detali:
            itog_det = self.detail(i, 's_01')
            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)
        self.prints(itog)

        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    # сортировка словаря
    def sort(self, dict_list):
        dict_list_sort = {}
        for k in sorted(dict_list.keys()):
            dict_list_sort[k] = dict_list[k]
        return dict_list_sort

    def ug(self):
        self.A = self.os[0]
        self.B = self.os[1]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B)) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        # вычисляем угол горизонтального угла
        # print("self.os", self.os, len(self.os))
        if self.dat['Обозначение'] in ['ugf', 'угф'] and len(self.os) == 3:
            self.os.append(90)
        elif self.dat['Обозначение'] in ['ug', 'уг'] and len(self.os) == 2:
            self.os.append(90)

        self.C = int(self.os[-1])
        self.index = self.index + 1
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'ug',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        if str(self.dat['Кол. пров.']) in ['4', '3+1']:
            if self.C != 90:
                svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                      ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                      ['С-СД15', 'Стенка СБ', 1, ['c4', 1, self.A], ['c4', 1, self.B]],
                                      ['С-СД16', 'Стенка СБ', 1, ['c3', 1, self.A], ['c3', 1, self.B]]]
            else:
                svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                      ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                      ['С-СД12', 'Стенка СБ', 1, ['cB', 1, self.A], ['cB', 1, self.B], ['u', 1, 0]],
                                      ['С-СД2', 'Стенка СБ', 1, ['cA', 1, self.A], ['cA', 1, self.B], ['u', 1, 0]]]

            detali = [['n', 4], ['sux', 4],
                      ['s5', 1, [self.A, self.B]],
                      ['s6', 1, [self.A, self.B]],
                      ['s7', 1, [self.A, self.B]],
                      ['s8', 1, [self.A, self.B]]]

            if self.dat['In'] in [2600, 3200, 4000, 5000]:

                if self.C != 90:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД15', 'Стенка СБ', 2, ['c4', 2, self.A], ['c4', 2, self.B]],
                                          ['С-СД16', 'Стенка СБ', 2, ['c3', 2, self.A], ['c3', 2, self.B]],
                                          ['К-СД14', 1, ['kc1', 1, self.A], ['kc1', 1, self.B]]]
                else:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД12', 'Стенка СБ', 2, ['cB', 2, self.A], ['cB', 2, self.B], ['u', 2, 0]],
                                          ['С-СД2', 'Стенка СБ', 2, ['cA', 2, self.A], ['cA', 2, self.B], ['u', 2, 0]],
                                          ['К-СД14', 'Крышка СБ', 1, ['kc1', 1, self.A], ['kc1', 1, self.B]]]

                for i in [2, 3, 4, 5]:
                    detali[i][1] = 2

            elif self.dat['In'] in [4000, 5000]:

                if self.C != 90:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД15', 'Стенка СБ', 2, ['c4', 2, self.A], ['c4', 2, self.B]],
                                          ['С-СД16', 'Стенка СБ', 2, ['c3', 2, self.A], ['c3', 2, self.B]],
                                          ['К-СД14', 'Крышка СБ', 1, ['kc1', 1, self.A], ['kc1', 1, self.B]]]
                else:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД12', 'Стенка СБ', 2, ['cB', 2, self.A], ['cB', 2, self.B], ['u', 2, 0]],
                                          ['С-СД2', 'Стенка СБ', 2, ['cA', 2, self.A], ['cA', 2, self.B], ['u', 2, 0]],
                                          ['К-СД14', 'Крышка СБ', 1, ['kc1', 1, self.A], ['kc1', 1, self.B]]]

                for i in [2, 3, 4, 5]:
                    detali[i][1] = 2

            elif self.dat['In'] in [6400]:

                if self.C != 90:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД15', 'Стенка СБ', 3, ['c4', 3, self.A], ['c4', 3, self.B]],
                                          ['С-СД16', 'Стенка СБ', 3, ['c3', 3, self.A], ['c3', 3, self.B]],
                                          ['К-СД14', 'Крышка СБ', 2, ['kc1', 2, self.A], ['kc1', 2, self.B]]]
                else:
                    svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                          ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.B], ['k2', 1, self.A]],
                                          ['С-СД12', 'Стенка СБ', 3, ['cB', 3, self.A], ['cB', 3, self.B], ['u', 3, 0]],
                                          ['С-СД2', 'Стенка СБ', 3, ['cA', 3, self.A], ['cA', 3, self.B], ['u', 3, 0]],
                                          ['К-СД14', 'Крышка СБ', 2, ['kc1', 2, self.A], ['kc1', 2, self.B]]]

                for i in [2, 3, 4, 5]:
                    detali[i][1] = 3

            if self.os[0] == self.os[1] and self.dat['Обозначение'] not in ['угф', 'ugf']:
                #print(' Симетричные оси')
                svar_det_one_floor.pop(0)           # удаляем первую крышку К-СД1
                svar_det_one_floor[0][2] *= 2       # умножаем на 2 К-СД1
                svar_det_one_floor[0][3][1] *= 2    # умножаем на 2 к1
                svar_det_one_floor[0][4][1] *= 2    # умножаем на 2 к2
                svar_det_one_floor[1].pop(3)        # удаляем стенку с3 в С-СД1
                svar_det_one_floor[1][3][1] *= 2    # умножаем на 2 c3
                svar_det_one_floor[2].pop(3)        # удаляем стенку сА в С-СД2
                svar_det_one_floor[2][3][1] *= 2    # умножаем на 2 c3

            if self.dat['Обозначение'] in ['угф', 'ugf']:
                self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                itog[0][7] = 'ugf'
                #print('УГФ')
                svar_det_one_floor[0][3][0] = 'k2f'
                svar_det_one_floor[1][4][0] = 'k1f'
                svar_det_one_floor[2][3][0] = 'cBf'
                svar_det_one_floor[3][3][0] = 'cAf'

                if len(svar_det_one_floor) == 5:    # для двухэтажек

                    for i in svar_det_one_floor:
                        print(i)
                    svar_det_one_floor[4][3][0] = 'kc1f'
                dictionary = {2: 's19', 3: 's20', 4: 's21', 5: 's22'}

                for i in dictionary:
                    detali[i][0] = dictionary[i]

                if self.dat['межфазное расстояние фланца'] in [100, '100']:
                    detali.append(['fl_100', 2])
                else:
                    detali.append(['fl_130', 2])
                #print(detali)

#CR
            if self.dat['Серия'] in ['CR1', 'CR2']:

                if self.dat['Обозначение'] in ['угф', 'ugf']:
                    detali = [['s23', 1, [self.A, self.B, 1]],
                              ['s24', 1, [self.A, self.B, 2]],
                              ['s25', 1, [self.A, self.B, 3]],
                              ['s26', 1, [self.A, self.B, 4]],
                              ['torcentr', 2], ['mfazcentr', round((int(self.os[0]) + int(self.os[1])) / 200, 0)]]
                else:
                    detali = [['s41', 1, [self.A, self.B, 1]],
                              ['s41', 1, [self.A, self.B, 2]],
                              ['s41', 1, [self.A, self.B, 3]],
                              ['s41', 1, [self.A, self.B, 4]],
                              ['torcentr', 2], ['mfazcentr', round((int(self.os[0]) + int(self.os[1])) / 200, 0)]]

        else:
            svar_det_one_floor = [['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.A], ['k2', 1, self.B]],
                                  ['К-СД1', 'Крышка СБ', 1, ['k1', 1, self.os[1]], ['k2', 1, self.A]],
                                  ['С-СД12', 'Стенка СБ', 1, ['cB', 1, self.A], ['cB', 1, self.B], ['u', 1, 0]],
                                  ['С-СД2', 'Стенка СБ', 1, ['cA', 1, self.A], ['cA', 1, self.B], ['u', 1, 0]]]
            detali = [['n', 4], ['sux', 4],
                      ['s5', 1, [self.A, self.B]],
                      ['s38', 1, [self.A, self.B]],
                      ['s8', 1, [self.A, self.B]]]

        if self.dat['Серия'] in ['CR1', 'CR2']:
            print('CR1 нет сварных деталей!!!')
        else:

            for i in svar_det_one_floor:
                itog_svar = self.welded_part(i)

                for j in itog_svar:
                    itog.append(j)

        for j in detali:
            itog_det = self.detail(j, '')

            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)

        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def uv(self):
        self.A = self.os[0]
        self.B = self.os[1]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B)) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'uv',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        # CR
        if self.dat['Серия'] in ['CR1', 'CR2']:

            if self.dat['Обозначение'] in ["uvf", "увф"]:
                detali = [['torcentr', 2], ['mfazcentr', round((int(self.os[0]) + int(self.os[1])) / 200, 0)]]
                svar_det = [['Ш-СД31', 'Шина СБ', 4, ['s', 4, [self.A, 'x']], ['s', 4, [self.B, 'y']]]]
            else:
                detali = [['torcentr', 2], ['mfazcentr', round((int(self.os[0]) + int(self.os[1])) / 200, 0)]]
                svar_det = [['Ш-СД31', 'Шина СБ', 4, ['s', 4, [self.A, 'x']], ['s', 4, [self.B, 'y']]]]

            for i in svar_det:
                itog_svar = self.welded_part(i)

                for j in itog_svar:
                    itog.append(j)

            for j in detali:
                itog_det = self.detail(j, '')

                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            self.prints(itog)
            return True
        #B
        else:
            def one(x, y):

                if self.dat['Обозначение'] in ['увф', 'uvf']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                    itog[0][7] = 'uvf'
                    detali = [['n', 2], ['sux', 4]]

                    if self.dat['межфазное расстояние фланца'] in [100, '100']:
                        detali.append(['fl_100', 2])
                    else:
                        detali.append(['fl_130', 2])


                    svar_det_one_floor = [['К-СД2', 'Крышка СБ', 1, ['k3f', 1, x], ['k3', 1, y]],
                                          ['К-СД3', 'Крышка СБ', 1, ['k4f', 1, x], ['k4', 1, y]],
                                          ['С-СД3', 'Стенка СБ', 1, ['c1f', 1, x], ['c2', 1, y]],
                                          ['С-СД3', 'Стенка СБ', 1, ['c1', 1, y], ['c2f', 1, x]],
                                          ['Ш-СД17', 'Шина СБ', 1, ['s36', 1, x], ['s3', 1, y]],
                                          ['Ш-СД17-З', 'Шина СБ', 1, ['s36', 1, x], ['s3', 1, y]],
                                          ['Ш-СД18', 'Шина СБ', 1, ['s37', 1, x], ['s4', 1, y]],
                                          ['Ш-СД18-З', 'Шина СБ', 1, ['s37', 1, x], ['s4', 1, y]]]
                else:
                    detali = [['n', 4], ['sux', 4]]
                    svar_det_one_floor = [['К-СД2', 'Крышка СБ', 1, ['k3', 1, x], ['k3', 1, y]],
                                          ['К-СД3', 'Крышка СБ', 1, ['k4', 1, x], ['k4', 1, y]],
                                          ['С-СД3', 'Стенка СБ', 1, ['c1', 1, x], ['c2', 1, y]],
                                          ['С-СД3', 'Стенка СБ', 1, ['c1', 1, y], ['c2', 1, x]],
                                          ['Ш-СД1', 'Шина СБ', 1, ['s3', 1, x], ['s3a', 1, y]],
                                          ['Ш-СД1-З', 'Шина СБ', 1, ['s3', 1, x], ['s3a', 1, y]],
                                          ['Ш-СД2', 'Шина СБ', 1, ['s4', 1, x], ['s4a', 1, y]],
                                          ['Ш-СД2-З', 'Шина СБ', 1, ['s4', 1, x], ['s4a', 1, y]]]

                for j in detali:
                    itog_det = self.detail(j, '')

                    if itog_det == 0:  # только что рассчитывали сухарь, направляющую или фланец
                        continue
                    else:
                        itog.append(itog_det)

                return svar_det_one_floor

            def one_3(x, y):
                detali = [['n', 4], ['sux', 4]]
                for j in detali:
                    itog_det = self.detail(j, '')
                    if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                        continue
                    else:
                        itog.append(itog_det)

                svar_det_one_floor = [['К-СД2', 'Крышка СБ', 1, ['k3', 1, x], ['k3', 1, y]],
                                      ['К-СД3', 'Крышка СБ', 1, ['k4', 1, x], ['k4', 1, y]],
                                      ['С-СД3', 'Стенка СБ', 1, ['c1', 1, x], ['c2', 1, y]],
                                      ['С-СД3', 'Стенка СБ', 1, ['c1', 1, y], ['c2', 1, x]],
                                      ['Ш-СД1', 'Шина СБ', 1, ['s3', 1, x], ['s3a', 1, y]],
                                      ['Ш-СД31', 'Шина СБ', 1, ['s', 1, x], ['sa', 1, y]],
                                      ['Ш-СД1-З', 'Шина СБ', 1, ['s3', 1, x], ['s3a', 1, y]]]

                return svar_det_one_floor

            # если оси одинаковые
            def ayna(svar_det_one_floor):

                if x == y and self.dat['Обозначение'] not in ['увф', 'uvf']:
                    svar_det_one_floor.pop(3)       # С-СД3
                    svar_det_one_floor[2][2] *= 2
                    svar_det_one_floor[2][3][1] *= 2
                    svar_det_one_floor[2][4][1] *= 2

                    svar_det_one_floor[0].pop(3)    # К-СД2
                    svar_det_one_floor[0][3][1] = 2

                    svar_det_one_floor[1].pop(3)    # К-СД3
                    svar_det_one_floor[1][3][1] = 2
                    return svar_det_one_floor
                else:
                    return svar_det_one_floor

            if str(self.dat['Кол. пров.']) in ['4', '3+1']:

                if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                    svar_det_one_floor = one(self.A, self.B)

                    for i in svar_det_one_floor:
                        itog_svar = self.welded_part(i)

                        for j in itog_svar:
                            itog.append(j)

                elif self.dat['In'] in [2600, 3200, 4000, 5000]:
                    # первый этаж
                    x = int(self.A) + self.dat['разница между этажами']
                    y = int(self.B) + self.dat['разница между этажами']
                    svar_det_one_floor = one(x, y)
                    svar_det_one_floor[1][0] = 'К-СД13'

                    if self.dat['Обозначение'] in ['увф', 'uvf']:
                        self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                        itog[0][7] = 'uvf'
                        svar_det_one_floor[1][3][0] = 'kc2f'
                    else:
                        svar_det_one_floor[1][3][0] = 'kc2'

                    svar_det_one_floor[1][4][0] = 'kc2'
                    svar_det_one_floor = ayna(svar_det_one_floor)
                    #   второй этаж
                    x = int(self.A) - self.dat['разница между этажами']
                    y = int(self.B) - self.dat['разница между этажами']
                    svar_det_two_floor = one(x, y)
                    svar_det_two_floor = ayna(svar_det_two_floor)
                    svar_det_two_floor.pop(0)
                    svar_det = svar_det_one_floor + svar_det_two_floor

                    for i in svar_det:
                        itog_svar = self.welded_part(i)

                        for j in itog_svar:
                            itog.append(j)

                #   elif self.dat['In'] in [6400]:
                else:
                    # первый этаж
                    x = int(self.A) + self.dat['разница между этажами']
                    y = int(self.B) + self.dat['разница между этажами']
                    svar_det_one_floor = one(x, y)
                    svar_det_one_floor[1][0] = 'К-СД13'

                    if self.dat['Обозначение'] in ['увф', 'uvf']:
                        self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                        itog[0][7] = 'uvf'
                        svar_det_one_floor[1][3][0] = 'kc2f'
                    else:
                        svar_det_one_floor[1][3][0] = 'kc2'

                    svar_det_one_floor[1][3][0] = 'kc2'
                    svar_det_one_floor[1][4][0] = 'kc2'
                    #   второй этаж
                    svar_det_two_floor = one(self.A, self.B)
                    svar_det_two_floor[1][0] = 'К-СД13'

                    if self.dat['Обозначение'] in ['увф', 'uvf']:
                        self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
                        itog[0][7] = 'uvf'
                        svar_det_one_floor[1][3][0] = 'kc2f'
                    else:
                        svar_det_one_floor[1][3][0] = 'kc2'

                    svar_det_two_floor[1][3][0] = 'kc2'
                    svar_det_two_floor[1][4][0] = 'kc2'
                    svar_det_two_floor.pop(0)
                    #   третий этаж
                    x = int(self.A) - self.dat['разница между этажами']
                    y = int(self.B) - self.dat['разница между этажами']
                    svar_det_three_floor = one(x, y)
                    svar_det_three_floor.pop(0)
                    svar_det = svar_det_one_floor + svar_det_two_floor + svar_det_three_floor
                    for i in svar_det:
                        itog_svar = self.welded_part(i)
                        for j in itog_svar:
                            itog.append(j)
            else:               # 3-х проводной
                svar_det_one_floor = one_3(self.A, self.B)

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)

            self.prints(itog)
            line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
            return True

    def z_g(self):      #!!!!! не доделан 3-х проводной

        self.A = self.os[0]
        self.B = self.os[1]
        self.C = self.os[2]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        self.index = self.index + 1
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'zg',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        if str(self.dat['Кол. пров.']) in ['4', '3+1']:
            svar_det_one_floor = [['К-СД4', 'Крышка СБ', 1, ['k2', 1, self.A], ['k7', 1, self.B], ['k2', 1, self.C]],
                                  ['К-СД5', 'Крышка СБ', 1, ['k1', 1, self.A], ['k8', 1, self.B], ['k1', 1, self.C]],
                                  ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.A], ['u', 2, 0], ['cC', 1, self.B], ['cA', 1, self.C]],
                                  ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.C], ['u', 2, 0], ['cC', 1, self.B], ['cA', 1, self.A]]]
                                  #['С-СД4', 1, ['c3', 1, self.os[0]], ['c3a', 1, self.os[1]], ['u', 1], ['cA', 1, self.os[2]]],
                                  #['С-СД4', 1, ['c3', 1, self.os[2]], ['c3a', 1, self.os[1]], ['u', 1], ['cA', 1, self.os[0]]]]

            if self.dat['Серия'] in ['CR1', 'CR']:
                detali = [['torcentr', 2], ['mfazcentr', round((int(self.os[0]) + int(self.os[1]) +
                                                                int(self.os[2])) / 200, 0)],
                          ['s46_1', 1, [self.A, self.B, self.C]],
                          ['s46_2', 1, [self.A, self.B, self.C]],
                          ['s46_3', 1, [self.A, self.B, self.C]],
                          ['s46_4', 1, [self.A, self.B, self.C]]]
            else:
                detali = [['n', 4], ['sux', 4],
                          ['s13', 1, [self.A, self.B, self.C]],
                          ['s14', 1, [self.A, self.B, self.C]],
                          ['s15', 1, [self.A, self.B, self.C]],
                          ['s16', 1, [self.A, self.B, self.C]]]

            if self.dat['In'] in [2000, 2500]:
                svar_det_one_floor[2] = ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.A], ['u', 2, 0], ['cC', 1, self.B], ['cA', 1, self.C]]
                svar_det_one_floor[3] = ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.C], ['u', 2, 0], ['cC', 1, self.B], ['cA', 1, self.A]]
            elif self.dat['In'] in [2600, 3200]:
                svar_det_one_floor[2] = ['С-СД13', 'Стенка СБ', 2, ['cB', 2, self.A],  ['u', 2, 0], ['cC', 2, self.B], ['cA', 2, self.C]]
                svar_det_one_floor[3] = ['С-СД13', 'Стенка СБ', 2, ['cB', 2, self.C],  ['u', 2, 0], ['cC', 2, self.B], ['cA', 2, self.A]]
                svar_det_one_floor.append(['К-СД16', 'Крышка СБ', 1, ['kc1', 1, self.A], ['kc4', 1, self.B], ['kc1', 1, self.C]])
                for i in [2, 3, 4, 5]:
                    detali[i][1] = 2
            elif self.dat['In'] in [4000, 5000]:
                svar_det_one_floor[2] = ['С-СД13', 'Стенка СБ', 2, ['cB', 2, self.A], ['u', 2, 0], ['cC', 2, self.B], ['cA', 2, self.C]]
                svar_det_one_floor[3] = ['С-СД13', 'Стенка СБ', 2, ['cB', 2, self.C], ['u', 2, 0], ['cC', 2, self.B], ['cA', 2, self.A]]
                svar_det_one_floor.append(['К-СД16', 'Крышка СБ', 1, ['kc1', 1, self.A], ['kc4', 1, self.B], ['kc1', 1, self.C]])
                for i in [2, 3, 4, 5]:
                    detali[i][1] = 2
            elif self.dat['In'] in [6400]:
                svar_det_one_floor[2] = ['С-СД13', 'Стенка СБ', 3, ['cB', 3, self.A],  ['u', 3, 0], ['cC', 3, self.B], ['cA', 3, self.C]]
                svar_det_one_floor[3] = ['С-СД13', 'Стенка СБ', 3, ['cB', 3, self.C],  ['u', 3, 0], ['cC', 3, self.B], ['cA', 3, self.A]]
                svar_det_one_floor.append(['К-СД16', 'Крышка СБ', 3, ['kc1', 3, self.A], ['kc4', 3, self.B], ['kc1', 3, self.C]])
                for i in [2, 3, 4, 5]:
                    detali[i][1] = 3

            '''if self.os[0] == self.os[2] and self.dat['Обозначение'] not in ['згф', 'zgf']:
                svar_det_one_floor.pop(3)           # удаляем первую крышку К-СД4
                svar_det_one_floor[2][1] *= 2       # умножаем на 2 К-СД1
                svar_det_one_floor[2][2][1] *= 2    # умножаем на 2 с3
                svar_det_one_floor[2][3][1] *= 2    # умножаем на 2 с2а
                svar_det_one_floor[2][4][1] *= 2    # умножаем на 2 сВ'''

            if self.dat['Обозначение'] in ['згф', 'zgf']:
                self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                itog[0][7] = 'zgf'
                svar_det_one_floor[0][3][0] = 'k2f'
                svar_det_one_floor[1][3][0] = 'k1f'
                svar_det_one_floor[2][3][0] = 'cBf'
                svar_det_one_floor[3][6][0] = 'cAf'
                dictionary = {2: 's27', 3: 's28', 4: 's29', 5: 's30'}
                for i in dictionary:
                    detali[i][0] = dictionary[i]

                if self.dat['межфазное расстояние фланца'] in [100, '100']:
                    detali.append(['fl_100', 2])
                else:
                    detali.append(['fl_130', 2])

        else:   # 3-х проводной
            svar_det_one_floor = [['К-СД4', 'Крышка СБ', 1, ['k2', 1, self.A], ['k7', 1, self.B], ['k2', 1, self.C]],
                                  ['К-СД5', 'Крышка СБ', 1, ['k1', 1, self.A], ['k8', 1, self.B], ['k1', 1, self.C]],
                                  ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.A], ['u', 2, 0], ['cC', 1, self.B],
                                   ['cA', 1, self.C]],
                                  ['С-СД13', 'Стенка СБ', 1, ['cB', 1, self.C], ['u', 2, 0], ['cC', 1, self.B],
                                   ['cA', 1, self.A]]]
            detali = [['n', 4], ['sux', 4],
                      ['s13', 1, [self.A, self.B, self.C]],
                      ['s14', 1, [self.A, self.B, self.C]],
                      ['s15', 1, [self.A, self.B, self.C]],
                      ['s16', 1, [self.A, self.B, self.C]]]

        if self.dat['Серия'] in ['CR1', 'CR']:
            print('Нет сварных детлей')
        else:

            for i in svar_det_one_floor:

                itog_svar = self.welded_part(i)
                for j in itog_svar:
                    itog.append(j)

        for j in detali:
            itog_det = self.detail(j, '')
            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def z_v(self):

        self.A = self.os[0]
        self.B = self.os[1]
        self.C = self.os[2]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B) + int(self.C)) / 1000,0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        self.index = self.index + 1
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'zv',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        def one(x, y, z):
            detali = [['n', 4], ['sux', 4]]
            svar_det_one_floor = [['К-СД6', 'Крышка СБ', 1, ['k3', 1, x], ['k9', 1, y], ['k4', 1, z]],
                                  ['К-СД6', 'Крышка СБ', 1, ['k3', 1, z], ['k9', 1, y], ['k4', 1, x]],
                                  ['С-СД5', 'Стенка СБ', 1, ['c2', 1, x], ['c7', 1, y], ['c2', 1, z]],
                                  ['С-СД6', 'Стенка СБ', 1, ['c1', 1, x], ['c8', 1, y], ['c1', 1, z]],
                                  ['Ш-СД3', 'Шина СБ', 1, ['s3', 1, x], ['s', 1, y], ['s3', 1, z]],
                                  ['Ш-СД3-З', 'Шина СБ', 1, ['s3', 1, x], ['s', 1, y], ['s3', 1, z]],
                                  ['Ш-СД4', 'Шина СБ', 1, ['s4', 1, x], ['s', 1, y], ['s4', 1, z]],
                                  ['Ш-СД4-З', 'Шина СБ', 1, ['s4', 1, x], ['s', 1, y], ['s4', 1, z]]]

            if self.dat['Обозначение'] in ['звф', 'zvf']:
                self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                itog[0][7] = 'zvf'
                detali = [['n', 4], ['sux', 4], ['fl', 2]]
                svar_det_one_floor = [['К-СД6', 'Крышка СБ', 1, ['k3f', 1, x], ['k9', 1, y], ['k4', 1, z]],
                                      ['К-СД6-З', 'Крышка СБ', 1, ['k3', 1, z], ['k9', 1, y], ['k4f', 1, x]],
                                      ['С-СД5', 'Стенка СБ', 1, ['c2f', 1, x], ['c7', 1, y], ['c2', 1, z]],
                                      ['С-СД6', 'Стенка СБ', 1, ['c1f', 1, x], ['c8', 1, y], ['c1', 1, z]],
                                      ['Ш-СД19', 'Шина СБ', 1, ['s37', 1, x], ['s', 1, y], ['s3', 1, z]],
                                      ['Ш-СД20', 'Шина СБ', 1, ['s36', 1, x], ['s', 1, y], ['s3', 1, z]],
                                      ['Ш-СД19-З', 'Шина СБ', 1, ['s37', 1, x], ['s', 1, y], ['s4', 1, z]],
                                      ['Ш-СД20-З', 'Шина СБ', 1, ['s36', 1, x], ['s', 1, y], ['s4', 1, z]]]

            for j in detali:
                itog_det = self.detail(j, '')
                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            return svar_det_one_floor

        def one_3(x, y, z):
            detali = [['n', 4], ['sux', 4]]

            for j in detali:
                itog_det = self.detail(j, '')
                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            svar_det_one_floor = [['К-СД6', 'Крышка СБ', 1, ['k3', 1, x], ['k9', 1, y], ['k4', 1, z]],
                                  ['К-СД6', 'Крышка СБ', 1, ['k3', 1, z], ['k9', 1, y], ['k4', 1, x]],
                                  ['С-СД5', 'Стенка СБ', 1, ['c2', 1, x], ['c7', 1, y], ['c2', 1, z]],
                                  ['С-СД6', 'Стенка СБ', 1, ['c1', 1, x], ['c8', 1, y], ['c1', 1, z]],
                                  ['Ш-СД3', 'Шина СБ', 1, ['s3', 1, x], ['s', 1, y], ['s3', 1, z]],
                                  ['Ш-СД3-З', 'Шина СБ', 1, ['s3', 1, x], ['s', 1, y], ['s3', 1, z]],
                                  ['Ш-СД30', 'Шина СБ', 1, ['s_3', 1, x], ['s', 1, y], ['s_3', 1, z]]]

            return svar_det_one_floor

        if str(self.dat['Кол. пров.']) in ['4', '3+1']:

            if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                svar_det_one_floor = one(self.A, self.B, self.C)

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

            elif self.dat['In'] in [2600, 3200, 4000, 5000]:
                # первый этаж
                x = int(self.os[0]) + self.dat['разница между этажами']
                z = int(self.os[2]) - self.dat['разница между этажами']
                svar_det_one_floor = one(x, self.B, z)

                if self.dat['Обозначение'] in ['звф', 'zvf']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    itog[0][7] = 'zvf'
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2f', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]
                else:
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]

                #   второй этаж
                x = int(self.os[0]) - self.dat['разница между этажами']
                z = int(self.os[2]) + self.dat['разница между этажами']
                svar_det_two_floor = one(x, self.B, z)
                svar_det_two_floor.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor

                for i in svar_det:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

            #   elif self.dat['In'] in [6400]:
            else:
                # первый этаж
                x = int(self.os[0]) + self.dat['разница между этажами']
                z = int(self.os[2]) - self.dat['разница между этажами']
                svar_det_one_floor = one(x, self.B, z)

                if self.dat['Обозначение'] in ['звф', 'zvf']:
                    self.spisok_dla_mater['Nflanc'] = self.spisok_dla_mater['Nflanc'] + int(self.dat['количество'])
                    itog[0][7] = 'zvf'
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2f', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]
                else:
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]

                #   второй этаж
                svar_det_two_floor = one(self.A, self.B, self.C)

                if self.dat['Обозначение'] == 'звф':
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2f', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]
                else:
                    svar_det_one_floor[1] = ['К-СД15', 'Крышка СБ', 1, ['kc2', 1, x], ['kc5', 1, self.B], ['kc2a', 1, z]]

                svar_det_two_floor.pop(0)
                #   третий этаж
                x = int(self.os[0]) - self.dat['разница между этажами']
                z = int(self.os[2]) + self.dat['разница между этажами']
                svar_det_three_floor = one(x, self.B, z)
                svar_det_three_floor.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor + svar_det_three_floor

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)
        else:
            x = self.A
            y = self.B
            z = self.C
            svar_det_one_floor = one_3(x, y, z)

            for i in svar_det_one_floor:
                itog_svar = self.welded_part(i)

                for j in itog_svar:
                    itog.append(j)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def k_p(self):

        self.A = self.os[0]
        self.B = self.os[1]
        self.C = self.os[2]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'kp',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        def one(x, y, z):


            if self.dat['Обозначение'] in ['kpfuv']:
                itog[0][7] = 'kpfuv'
                detali = [['n', 2], ['sux', 4]]

                if self.dat['межфазное расстояние фланца'] in [100, '100']:
                    detali.append(['fl_100', 2])
                else:
                    detali.append(['fl_130', 2])

                svar_det_one_floor = [['К-СД9', 'Крышка СБ', 1, ['k3f', 1, x], ['k13', 1, y], ['k2', 1, z]],
                                      ['К-СД10', 'Крышка СБ', 1, ['k4f', 1, x], ['k16', 1, y], ['k1', 1, z]],
                                      ['С-СД9', 'Стенка СБ', 1, ['c2f', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                      ['С-СД10', 'Стенка СБ', 1, ['c1f', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                      ['Ш-СД39', 'Шина СБ', 1, ['s36', 1, x], ['s12', 1, [y, z]]],
                                      ['Ш-СД40', 'Шина СБ', 1, ['s36', 1, x], ['s11', 1, [y, z]]],
                                      ['Ш-СД41', 'Шина СБ', 1, ['s37', 1, x], ['s10', 1, [y, z]]],
                                      ['Ш-СД42', 'Шина СБ', 1, ['s37', 1, x], ['s9', 1, [y, z]]]]
            else:
                detali = [['n', 4], ['sux', 4]]
                svar_det_one_floor = [['К-СД9', 'Крышка СБ', 1, ['k3', 1, x], ['k13', 1, y], ['k2', 1, z]],
                                      ['К-СД10', 'Крышка СБ', 1, ['k4', 1, x], ['k16', 1, y], ['k1', 1, z]],
                                      ['С-СД9', 'Стенка СБ', 1, ['c2', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                      ['С-СД10', 'Стенка СБ', 1, ['c1', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                      ['Ш-СД11', 'Шина СБ', 1, ['s3', 1, x], ['s12', 1, [y, z]]],
                                      ['Ш-СД12', 'Шина СБ', 1, ['s3', 1, x], ['s11', 1, [y, z]]],
                                      ['Ш-СД13', 'Шина СБ', 1, ['s4', 1, x], ['s10', 1, [y, z]]],
                                      ['Ш-СД14', 'Шина СБ', 1, ['s4', 1, x], ['s9', 1, [y, z]]]]

            for j in detali:
                itog_det = self.detail(j, '')

                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            return svar_det_one_floor

        def one_3(x, y, z):
            detali = [['n', 4], ['sux', 4]]

            for j in detali:
                itog_det = self.detail(j, '')

                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            svar_det_one_floor = [['К-СД9', 'Крышка СБ', 1, ['k3', 1, x], ['k13', 1, y], ['k2', 1, z]],
                                  ['К-СД10', 'Крышка СБ', 1, ['k4', 1, x], ['k16', 1, y], ['k1', 1, z]],
                                  ['С-СД9', 'Стенка СБ', 1, ['c2', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                  ['С-СД10', 'Стенка СБ', 1, ['c1', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                  ['Ш-СД11', 'Шина СБ', 1, ['s3', 1, x], ['s12', 1, [y, z]]],
                                  ['Ш-СД32', 'Шина СБ', 1, ['s_3', 1, x], ['s38', 1, [y, z]]],  # нужен новый чертеж
                                  ['Ш-СД14', 'Шина СБ', 1, ['s3', 1, x], ['s9', 1, [y, z]]]]
            return svar_det_one_floor

        if str(self.dat['Кол. пров.']) in ['4', '3+1']:

            if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                x = self.os[0]
                y = self.os[1]
                z = self.os[2]
                svar_det_one_floor = one(x, y, z)

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

            elif self.dat['In'] in [2600, 3200, 4000, 5000]:
                x = int(self.os[0]) + self.dat['разница между этажами']
                y = int(self.os[1]) + self.dat['разница между этажами']
                z = self.os[2]
                svar_det_one_floor = one(x, y, z)
                svar_det_one_floor[1] = ['К-СД12', 'Крышка СБ', 1, ['kc2', 1, x], ['kc9', 1, y], ['kc1', 1, z]]

                x = int(self.os[0]) - self.dat['разница между этажами']
                y = int(self.os[1]) - self.dat['разница между этажами']
                z = self.os[2]
                svar_det_two_floor = one(x, y, z)
                svar_det_two_floor.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor

                for i in svar_det:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

            elif self.dat['In'] in [6400]:
                x = int(self.os[0]) + self.dat['разница между этажами']
                y = int(self.os[1]) + self.dat['разница между этажами']
                z = int(self.os[2])
                svar_det_one_floor = one(x, y, z)
                svar_det_one_floor[1] = ['К-СД12', 'Крышка СБ', 1, ['kc2', 1, x], ['kc9', 1, y], ['kc1', 1, z]]

                x = int(self.os[0])
                y = int(self.os[1])
                z = int(self.os[2])
                svar_det_two_floor = one(x, y, z)
                svar_det_one_floor[1] = ['К-СД12', 'Крышка СБ', 1, ['kc2', 1, x], ['kc9', 1, y], ['kc1', 1, z]]

                x = int(self.os[0]) - self.dat['разница между этажами']
                y = int(self.os[1]) - self.dat['разница между этажами']
                z = int(self.os[2])
                svar_det_two_three = one(x, y, z)
                svar_det_two_three.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor + svar_det_two_three

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

        # для 3-проводного шинопровода
        else:

            if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                x = self.os[0]
                y = self.os[1]
                z = self.os[2]
                svar_det_one_floor = one_3(x, y, z)

                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)

                    for j in itog_svar:
                        itog.append(j)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def k_l(self):

        self.A = self.os[0]
        self.B = self.os[1]
        self.C = self.os[2]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество']) * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество']) * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)

        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'kl',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        def one(x, y, z):

            if self.dat['Обозначение'] in ['klfuv']:
                itog[0][7] = 'klfuv'
                detali = [['n', 2], ['sux', 4]]

                if self.dat['межфазное расстояние фланца'] in [100, '100']:
                    detali.append(['fl_100', 2])
                else:
                    detali.append(['fl_130', 2])

                svar_det_one_floor = [['К-СД7', 'Крышка СБ', 1, ['k3f', 1, x], ['k14', 1, y], ['k2', 1, z]],
                                      ['К-СД8', 'Крышка СБ', 1, ['k4f', 1, x], ['k15', 1, y], ['k1', 1, z]],
                                      ['С-СД7', 'Стенка СБ', 1, ['c1f', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                      ['С-СД8', 'Стенка СБ', 1, ['c2f', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                      ['Ш-СД37', 'Шина СБ', 1, ['s36', 1, x], ['s9', 1, [y, z]]],
                                      ['Ш-СД38', 'Шина СБ', 1, ['s37', 1, x], ['s10', 1, [y, z]]],
                                      ['Ш-СД39', 'Шина СБ', 1, ['s37', 1, x], ['s11', 1, [y, z]]],
                                      ['Ш-СД40', 'Шина СБ', 1, ['s36', 1, x], ['s12', 1, [y, z]]]]
            else:
                detali = [['n', 4], ['sux', 4]]
                svar_det_one_floor = [['К-СД7', 'Крышка СБ', 1, ['k3', 1, x], ['k14', 1, y], ['k1', 1, z]],
                                      ['К-СД8', 'Крышка СБ', 1, ['k4', 1, x], ['k15', 1, y], ['k2', 1, z]],
                                      ['С-СД7', 'Стенка СБ', 1, ['c1', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                      ['С-СД8', 'Стенка СБ', 1, ['c2', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                      ['Ш-СД7', 'Шина СБ', 1, ['s3', 1, x], ['s12', 1, [y, z]]],
                                      ['Ш-СД8', 'Шина СБ', 1, ['s3', 1, x], ['s11', 1, [y, z]]],
                                      ['Ш-СД9', 'Шина СБ', 1, ['s4', 1, x], ['s10', 1, [y, z]]],
                                      ['Ш-СД10', 'Шина СБ', 1, ['s4', 1, x], ['s9', 1, [y, z]]]]
            for j in detali:
                itog_det = self.detail(j, '')
                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)

            return svar_det_one_floor

        def one_3(x, y, z):
            detali = [['n', 4], ['sux', 4]]
            for j in detali:
                itog_det = self.detail(j, '')
                if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                    continue
                else:
                    itog.append(itog_det)
            svar_det_one_floor = [['К-СД7', 'Крышка СБ', 1, ['k3', 1, x], ['k14', 1, y], ['k1', 1, z]],
                                  ['К-СД8', 'Крышка СБ', 1, ['k4', 1, x], ['k15', 1, y], ['k2', 1, z]],
                                  ['С-СД7', 'Стенка СБ', 1, ['c1', 1, x], ['c2a', 1, y], ['u', 1, 0], ['cB', 1, z]],
                                  ['С-СД8', 'Стенка СБ', 1, ['c2', 1, x], ['c1a', 1, y], ['u', 1, 0], ['cA', 1, z]],
                                  ['Ш-СД7', 'Шина СБ', 1, ['s3', 1, x], ['s12', 1, [y, z]]],
                                  ['Ш-СД29', 'Шина СБ', 1, ['s_3', 1, x], ['s38', 1, [y, z]]],
                                  ['Ш-СД10', 'Шина СБ', 1, ['s4', 1, x], ['s9', 1, [y, z]]]]
            return svar_det_one_floor

        if str(self.dat['Кол. пров.']) in ['4', '3+1']:
            if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                x = self.os[0]
                y = self.os[1]
                z = self.os[2]
                svar_det_one_floor = one(x, y, z)
                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)

            elif self.dat['In'] in [2600, 3200, 4000, 5000]:
                x = int(self.os[0]) + self.dat['разница между этажами']
                y = int(self.os[1]) + self.dat['разница между этажами']
                z = self.os[2]
                svar_det_one_floor = one(x, y, z)
                svar_det_one_floor[1] = ['КС-СД11', 'Крышка СБ', 1, ['kc2', 1, x], ['kc8', 1, y], ['kc1', 1, z]]

                x = int(self.os[0]) - self.dat['разница между этажами']
                y = int(self.os[1]) - self.dat['разница между этажами']
                z = self.os[2]
                svar_det_two_floor = one(x, y, z)
                svar_det_two_floor.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor
                for i in svar_det:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)

            elif self.dat['In'] in [6400]:
                x = int(self.os[0]) + self.dat['разница между этажами']
                y = int(self.os[1]) + self.dat['разница между этажами']
                z = int(self.os[2])
                svar_det_one_floor = one(x, y, z)
                svar_det_one_floor[1] = ['К-СД11', 'Крышка СБ', 1, ['kc2', 1, x], ['kc8', 1, y], ['kc1', 1, z]]

                x = int(self.os[0])
                y = int(self.os[1])
                z = int(self.os[2])
                svar_det_two_floor = one(x, y, z)
                svar_det_one_floor[1] = ['К-СД11', 'Крышка СБ', 1, ['kc2', 1, x], ['kc8', 1, y], ['kc1', 1, z]]

                x = int(self.os[0]) - self.dat['разница между этажами']
                y = int(self.os[1]) - self.dat['разница между этажами']
                z = int(self.os[2])
                svar_det_two_three = one(x, y, z)
                svar_det_two_three.pop(0)
                svar_det = svar_det_one_floor + svar_det_two_floor + svar_det_two_three
                for i in svar_det:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)
        else:
            if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
                x = self.os[0]
                y = self.os[1]
                z = self.os[2]
                svar_det_one_floor = one_3(x, y, z)
                for i in svar_det_one_floor:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)
        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def nestandart(self):
        print('Ошибка: нестандартная секция')
        self.dat['категория'] = 'спецификация'
        self.dat['стандарт'] = 'нестандарт'
        return False

    def om(self):
        self.L = self.os[0]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество']) * int(self.L) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])

        # print('os', self.os)

        #print('Секция отбора мощности')
        def tipiz(os, calc, nominal):

            if self.tip == []:
                self.dat['Разм.L'] = self.dat['размер']
                calculation.nestandart(self)
                return False

            elif int(self.tip[0]) in [1, 2]:

                if len(os) <= 1:
                    A = int(os[0]) / 2
                else:
                    A = int(os[1])

                L = int(os[0])
                B = '-'
                C = '-'

                if nominal == 2500:

                    if int(self.tip[0]) in [1]:
                        detali = [['k', 1, L], ['k18', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['k18', 1, L], ['k18', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]

                else:

                    if int(self.tip[0]) in [1]:
                        detali = [['kv', 1, L], ['kv18', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['kv18', 1, L], ['kv18', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]

                if int(self.tip[0]) in [1]:
                    svar_det = [['Ш-СД33', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 1, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 + 98)]],
                                ['Ш-СД34', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 1, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 - 46)]],
                                ['Ш-СД34', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 1, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 - 46)]],
                                ['Ш-СД33', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 1, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 + 98)]]]
                else:
                    svar_det = [['Ш-СД33-01', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 2, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 + 98)]],
                                ['Ш-СД34-01', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 2, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 - 46)]],
                                ['Ш-СД34-01', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 2, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 - 46)]],
                                ['Ш-СД33-01', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 2, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 + 98)]]]

                return [detali, svar_det, A, B, C]

            #else:
                #calculation.nestandart(self)
                #return False

            elif int(self.tip[0]) in [3, 4]:

                if len(os[0]) <= 1:

                    if int(os[0]) == 2000:
                        A = 500
                        B = 1000
                    elif int(os[0]) == 2500:
                        A = 750
                        B = 1000
                    else:
                        A = 1000
                        B = 1000

                else:
                    A = int(os[1])
                    B = int(os[2])


                #if int(self.L) in [1000, 1500, 2000, 2500, 3000]:
                L = int(os[0])
                C = '-'

                if nominal == 2500:
                    if int(self.tip[0]) in [3]:
                        detali = [['k', 1, L], ['k18_01', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['k18_01', 1, L], ['k18_01', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                else:
                    if int(self.tip[0]) in [3]:
                        detali = [['kv', 1, L], ['kv18_01', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['kv18_01', 1, L], ['kv18_01', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]

                if int(self.tip[0]) in [3]:
                    svar_det = [['Ш-СД33-02', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 2, 0],
                                 [float(L - A - B - calc['расстояние от оси до шины'] - 20 + 98), B]],
                                ['Ш-СД34-02', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 2, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 - 46 - B), B]],
                                ['Ш-СД34-02', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 2, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 - 46), B]],
                                ['Ш-СД33-02', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 2, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 + 98), B]]]
                else:
                    svar_det = [['Ш-СД33-03', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 4, 0],
                                 [float(L - A - B - calc['расстояние от оси до шины'] - 20 + 98), B]],
                                ['Ш-СД34-03', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 4, 0],
                                 [float(L - A - calc['расстояние от оси до шины'] - 20 - 46 - B), B]],
                                ['Ш-СД34-03', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 4, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 - 46), B]],
                                ['Ш-СД33-03', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 4, 0],
                                 [float(A - calc['расстояние от оси до шины'] - 20 + 98), B]]]

                return [detali, svar_det, A, B, C]

            elif int(self.tip[0]) in [5, 6]:

                if len(os) <= 1:
                    A = 500
                    B = 1000
                    C = 1000
                else:
                    A = int(os[1])
                    B = int(os[2])
                    C = int(os[3])

                if int(self.L) in [3000]:
                    L = int(os[0])

                    if nominal == 2500:

                        if int(self.tip[0]) in [5]:
                            detali = [['k', 1, L], ['k18_02', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                        else:
                            detali = [['k18_02', 1, L], ['k18_02', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]

                    else:

                        if int(self.tip[0]) in [5]:
                            detali = [['kv', 1, L], ['kv18_02', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]
                        else:
                            detali = [['kv18_02', 1, L], ['kv18_02', 1, L], ['c', 2, L], ['n', 4], ['sux', 4]]

                    if int(self.tip[0]) in [5]:
                        svar_det = [['Ш-СД33-04', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 3, 0],
                                     [float(L - A - B - C - calc['расстояние от оси до шины'] - 20 + 98), B, C]],
                                    ['Ш-СД34-04', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 3, 0],
                                     [float(L - A - B - C - calc['расстояние от оси до шины'] - 20 - 46), B, C]],
                                    ['Ш-СД34-04', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 3, 0],
                                     [float(A - calc['расстояние от оси до шины'] - 20 - 46), B, C]],
                                    ['Ш-СД33-04', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 3, 0],
                                     [float(A - calc['расстояние от оси до шины'] - 20 + 98), B, C]]]
                    else:
                        svar_det = [['Ш-СД33-05', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 6, 0],
                                     [float(L - A - B - C - calc['расстояние от оси до шины'] - 20 + 98), B, C]],
                                    ['Ш-СД34-05', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 6, 0],
                                     [float(L - A - B - C - calc['расстояние от оси до шины'] - 20 - 46), B, C]],
                                    ['Ш-СД34-05', 'Шина СБ', 1, ['s2_01', 1, L], ['stp09v', 6, 0],
                                     [float(A - calc['расстояние от оси до шины'] - 20 - 46), B, C]],
                                    ['Ш-СД33-05', 'Шина СБ', 1, ['s1_01', 1, L], ['stp09v', 6, 0],
                                     [float(A - calc['расстояние от оси до шины'] - 20 + 98), B, C]]]

                    return [detali, svar_det, A, B, C]

            else:
                calculation.nestandart(self)
                return False

        itogo = tipiz(self.os, self.dat, self.dat['In'])

        if itogo == False:
            return False

        detali = itogo[0]
        svar_detali = itogo[1]

        self.A = itogo[2]
        self.B = itogo[3]
        self.C = itogo[4]
        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'],
                 'pr' + self.dat['тип'],
                 self.L, self.L1, self.A, self.B,
                 self.C, self.dat['количество'], 'спецификация']]

        for i in svar_detali:
            itog_svar = self.welded_part(i)

            for j in itog_svar:
                itog.append(j)

        for i in detali:
            itog_det = self.detail(i, 's')

            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def omf(self):    # Не доделано
        self.L = self.dat['размер']

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * int(re.findall(r'\d+', self.L)[0]) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        #print('Секция отбора мощности с фиксированным выводом')
        def tipiz(os, calc, nominal, tip):

            if int(tip[0]) in [1]:

                if len(re.findall(r'\d+', self.L)) > 1:
                    A = int(re.findall(r'\d+', self.L)[1])
                    B = '-'
                    C = '-'
                elif re.findall(r'\d+', self.L)[0] in [1500, 2000, 2500, 3000]:
                    A = 400
                    B = '-'
                    C = '-'

                else:
                    calculation.nestandart(self)
                    return False

                if nominal == 2500:
                    detali = [['k', 1, os], ['k20', 1, os], ['k21', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]
                else:
                    detali = [['kv', 1, os], ['kv20', 1, os], ['kv21', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]

                svar_det = [['Ш-СД35', 'Шина СБ', 1, ['s1', 1, os], ['stp026v', 1, 0], [A]],
                            ['Ш-СД36', 'Шина СБ', 1, ['s2_01', 1, os], ['stp09v', 1, 0], [A]],
                            ['Ш-СД36-З', 'Шина СБ', 1, ['s2_01', 1, os], ['stp09v', 1, 0], [A]],
                            ['Ш-СД35-З', 'Шина СБ', 1, ['s1_01', 1, os], ['stp09v', 1, 0], [A]]]
                return [detali, svar_det, A, B, C]

            elif int(tip[0]) in [3, 4]:

                if len(re.findall(r'\d+', self.L)) > 1:
                    A = int(re.findall(r'\d+', self.L)[1])
                    B = int(re.findall(r'\d+', self.L)[2])
                    C = '-'
                elif len(re.findall(r'\d+', self.L)) == 1:

                    if int(self.L) in [1000, 1500, 2000, 2500, 3000]:
                        C = '-'

                        if int(os) == 2000:
                            A = 500
                            B = 1000
                        elif int(os) == 2500:
                            A = 750
                            B = 1000
                        else:
                            A = 1000
                            B = 1000

                else:
                    calculation.nestandart(self)
                    return False

                if nominal == 2500:
                    if int(tip[0]) in [3]:
                        detali = [['k', 1, os], ['k18_01', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['k18_01', 1, os], ['k18_01', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]
                else:
                    if int(tip[0]) in [3]:
                        detali = [['kv', 1, os], ['kv18_01', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]
                    else:
                        detali = [['kv18_01', 1, os], ['kv18_01', 1, os], ['c', 2, os], ['n', 4], ['sux', 4]]

                svar_det = [['Ш-СД33', 'Шина СБ', 1, ['s1_01', 1, os], ['stp09v', 1, 0], [float(os - A - B - calc['расстояние от оси до шины'] - 20 + 98), B]],
                            ['Ш-СД34', 'Шина СБ', 1, ['s2_01', 1, os], ['stp09v', 1, 0], [float(os - A - calc['расстояние от оси до шины'] - 20 - 46 - B), B]],
                            ['Ш-СД34', 'Шина СБ', 1, ['s2_01', 1, os], ['stp09v', 1, 0], [float(A - calc['расстояние от оси до шины'] - 20 - 46), B]],
                            ['Ш-СД33', 'Шина СБ', 1, ['s1_01', 1, os], ['stp09v', 1, 0], [float(A - calc['расстояние от оси до шины'] - 20 + 98), B]]]
                return [detali, svar_det, A, B, C]

            else:
                calculation.nestandart(self)
                return False

        itogo = tipiz(int(self.os[0]), self.dat, self.dat['In'], self.tip)
        # print(itogo, self.tip)

        if itogo == False:
            return False

        detali = itogo[0]
        svar_detali = itogo[1]

        self.A = itogo[2]
        self.B = itogo[3]
        self.C = itogo[4]
        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'],
                 str(self.dat['Обозначение'] + str('.'.join(self.tip))).upper(), self.L, self.L1, self.A, self.B,
                 self.C, self.dat['количество'], 'спецификация']]


        for i in svar_detali:
            itog_svar = self.welded_part(i)

            for j in itog_svar:
                itog.append(j)

        for i in detali:
            itog_det = self.detail(i, 's')
            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return False

    def tv(self):  # не закончено

        self.A = x = self.os[0]
        self.B = y = self.os[1]
        self.C = z = self.os[2]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        #print(self.index)
        self.index += 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'tv',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        if self.dat['In'] in [630, 800, 1000, 1250, 1600, 2000, 2500]:
            detali = [['k', 1, [x, y]], ['n', 8], ['sux', 8]]
            svar_det = [['К-СД3', 'Крышка СБ', 1, ['k4', 1, x], ['k4', 1, z]],
                        ['К-СД3', 'Крышка СБ', 1, ['k4', 1, y], ['k4', 1, z]],
                        ['С-СД11', 'Стенка СБ', 1, ['ct', 1, [x, y]], ['ctz', 1, z]],
                        ['С-СД11', 'Стенка СБ', 1, ['ct', 1, [y, x]], ['ctz', 1, z]],
                        ['Ш-СД15', 'Шина СБ', 1, ['s2t', 1, [x, y]], ['s4t', 1, z]],
                        ['Ш-СД15-З', 'Шина СБ', 1, ['s2t', 1, [y, x]], ['s4t', 1, z]],
                        ['Ш-СД16', 'Шина СБ', 1, ['s1t', 1, [x, y]], ['s3t', 1, z]],
                        ['Ш-СД16-З', 'Шина СБ', 1, ['s1t', 1, [y, x]], ['s3t', 1, z]]]

        elif self.dat['In'] in [2600, 3200, 4000, 5000]:
            detali = [['k', 2, [x, y]], ['n', 8], ['sux', 8]]
            svar_det = [['К-СД3', 'Крышка СБ', 1, ['k4t', 1, x], ['k4t', 1, z]],
                        ['К-СД3', 'Крышка СБ', 1, ['k4t', 1, y], ['k4t', 1, z]],
                        ['С-СД14', 'Стенка СБ', 1, ['ct', 2, [x, y]], ['ctz', 2, z]],
                        ['С-СД14', 'Стенка СБ', 1, ['ct', 2, [y, x]], ['ctz', 2, z]],
                        ['Ш-СД22', 'Шина СБ', 1, ['s2t', 2, [x, y]], ['s4t', 2, z]],
                        ['Ш-СД22-З', 'Шина СБ', 1, ['s2t', 2, [y, x]], ['s4t', 2, z]],
                        ['Ш-СД21', 'Шина СБ', 1, ['s1t', 2, [x, y]], ['s3t', 2, z]],
                        ['Ш-СД21-З', 'Шина СБ', 1, ['s1t', 2, [y, x]], ['s3t', 2, z]]]

        else:   # 6400
            detali = [['k', 1, [x, y]], ['n', 8], ['sux', 8]]
            svar_det = [['К-СД3', 'Крышка СБ', 1, ['k4', 1, x], ['k4', 1, z]],
                        ['С-СД11', 'Стенка СБ', 1, ['ct', 1, [x, y]], ['ctz', 1, z]],
                        ['С-СД11', 'Стенка СБ', 1, ['ct', 1, [y, x]], ['ctz', 1, z]],
                        ['Ш-СД15', 'Шина СБ', 1, ['s2t', 1, [x, y]], ['s4t', 1, z]],
                        ['Ш-СД15-З', 'Шина СБ', 1, ['s2t', 1, [y, x]], ['s4t', 1, z]],
                        ['Ш-СД16', 'Шина СБ', 1, ['s1t', 1, [x, y]], ['s3t', 1, z]],
                        ['Ш-СД16-З', 'Шина СБ', 1, ['s1t', 1, [y, x]], ['s3t', 1, z]]]

        for i in svar_det:
            itog_svar = self.welded_part(i)
            for j in itog_svar:
                itog.append(j)

        for i in detali:
            itog_det = self.detail(i, '')
            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)
        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def tg(self):

        '''self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество']) * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество']) * (int(self.A) + int(self.B) + int(self.C)) / 1000, 0)'''

        self.nestandart()
        return False

    # Секция компенсации
    def sk(self):
        self.A = self.os[0]

        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество'])
                                               * int(self.A) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['Lsvar_izd'] = round(self.spisok_dla_mater['Lsvar_izd'] + int(self.dat['количество'])
                                                   * int(self.A) / 1000, 0)
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']
        self.spisok_dla_mater['Nflanc'] = (self.spisok_dla_mater['Nflanc'] + int(self.dat['количество']) *2)

        self.index = self.index + 1

        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'sk',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        # CR  нестандарт не производим
        if self.dat['Серия'] in ['CR1', 'CR2']:
            self.nestandart()
            self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])

        #B
        else:

            if str(self.dat['Кол. пров.']) in ['4', '3+1'] and self.dat['In'] < 2600:
                detali = [['n', 4], ['sux', 4], ['c', 4, self.A], ['k', 4, self.A], ['sk_tr', 4, 0],
                          ['A000_125', 1, 0], ['A000_125_01', 1, 0], ['A000_125_02', 1, 0], ['A000_125_03', 1, 0]]
                svar_det = [['000 777', 'Шина средняя Ск', 2, ['A000_120', 4, 0]],
                            ['000 776', 'Шина крайняя Ск', 2, ['A000_119', 4, 0]],
                            ['k_pe', 'Шина PE в сборе', 1, ['A000_128', 2, 0]],
                            ['ksm', 'Кожух СК -01', 1, ['lvn', 2, 0], ['klb', 2, 0]],
                            ['km', 'Каркас кожуха-01', 1, ['ugol2', 2, 0], ['ugol1', 2, 0], ['ugol2_z', 2, 0],
                             ['ugol', 2, 0]],
                            ['kcb', 'Кожух СК-02', 1, ['lvb', 2, 0], ['lbm', 2, 0]],
                            ['kb', 'Каркас кожуха-02', 1, ['ugol2', 2, 0], ['ugol1_2', 2, 0], ['ugol2_z', 2, 0],
                             ['ugol_2', 2, 0]],
                            ['000 124', 'Компенсационная шина СБ', 5, ['A000_108', 5 * 7, 0]]]

                if self.dat['In'] in [2500]:
                    svar_det[7][3][1] = 5 * 9

                for j in detali:
                    itog_det = self.detail(j, '')
                    if itog_det == 0:  # только что расчитывали сухарь, направляющую или фланец
                        continue
                    else:
                        itog.append(itog_det)

                for i in svar_det:
                    itog_svar = self.welded_part(i)
                    for j in itog_svar:
                        itog.append(j)

            # нестандарт. на двух этажные и трех этажные документы не разработаны на три и пять проводнико не разработано
            else:
                self.nestandart()
                self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])

            self.prints(itog)
            line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
            return True

    def ts(self):
        print('5. Расчет трансформаторной секции:')

        tip1 = int(self.tip[0])
        tip2 = int(self.tip[1])
        text1 = re.findall(r'[^\s]+', re.sub(r'[()]', ' ', self.dat['размер']))
        #print('text1', text1)
        vivod = int(text1[2])
        #print('vivod', vivod)
        self.A = A = int(re.findall(r'[^-*+]+', text1[1])[0])
        self.B = B = int(re.findall(r'[^-*+]+', text1[1])[1])
        self.C = C = int(re.findall(r'[^-*+]+', text1[1])[2])
        self.L1 = L1 = int(re.findall(r'[^-*+]+', text1[1])[3])
        #print(str('L1=' + str(L1)), str('A=' + str(A)), str('B=' + str(B)), str('C=' + str(C)))

        A1 = C + B + A + L1
        A2 = B + C + L1
        A3 = C + L1
        A4 = L1
        # проверяем длину корпуса, достаточна ли она
        if int(text1[0]) < A1:
            razmer = A1 + 80
            #print('Длина по осии Х изменена на', razmer, 'мм.')
        else:
            razmer = text1[0]

        self.L = razmer
        self.spisok_dla_mater['dlina'] = round(self.spisok_dla_mater['dlina'] + int(self.dat['количество']) * int(self.L) / 1000, 0)
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        #print('Длина по X:', razmer, ' Тип:', str(str(tip1) + '.' + str(tip2)))
        os = [razmer, L1, A, B, C, tip1, tip2]

        trans_v = {1: {'A': A1, 'B': A2, 'C': A3, 'N': A4},
                   2: {'A': A1, 'B': A2, 'N': A3, 'C': A4},
                   3: {'A': A1, 'N': A2, 'B': A3, 'C': A4},
                   4: {'N': A1, 'A': A2, 'B': A3, 'C': A4},
                   5: {'C': A1, 'B': A2, 'A': A3, 'N': A4},
                   6: {'C': A1, 'B': A2, 'N': A3, 'A': A4},
                   7: {'C': A1, 'N': A2, 'B': A3, 'A': A4},
                   8: {'N': A1, 'C': A2, 'B': A3, 'A': A4}}

        ctp_v = {1: ['A', 'B', 'C', 'N'],
                 2: ['N', 'A', 'B', 'C'],
                 3: ['C', 'B', 'A', 'N'],
                 4: ['N', 'C', 'B', 'A']}
        detali = [['kv', 1, os], ['k19', 1, os], ['c', 2, os], ['n', 2], ['sux', 4], ['zts', 1], ['A000_774_01', 2, os],
                  ['A000_774_02', 2, os]]
        svar_det = [['Ш-СД25', 'Шина СБ', 1, ['s3', 1, trans_v[tip1][ctp_v[tip2][0]]], ['s33', 1, vivod]],
                    ['Ш-СД26', 'Шина СБ', 1, ['s4', 1, trans_v[tip1][ctp_v[tip2][1]]], ['s33', 1, vivod]],
                    ['Ш-СД27', 'Шина СБ', 1, ['s4', 1, trans_v[tip1][ctp_v[tip2][2]]], ['s33', 1, vivod]],
                    ['Ш-СД28', 'Шина СБ', 1, ['s3', 1, trans_v[tip1][ctp_v[tip2][3]]], ['s33', 1, vivod]]]

        if self.dat['In'] in [2500]:
            detali[0][0] = 'k'
        elif self.dat['In'] in [3200, 4000, 5000]:
            detali = [['kv', 1, os], ['k19', 1, os], ['c', 4, os], ['n', 2], ['sux', 4], ['zts', 1],
                      ['A000_774_01', 2, os], ['A000_774_02', 2, os]]
            svar_det = [['Ш-СД25', 'Шина СБ', 2, ['s3', 2, trans_v[tip1][ctp_v[tip2][0]]], ['s33', 1, vivod], ['s33i', 1, vivod]],
                        ['Ш-СД26', 'Шина СБ', 2, ['s4', 2, trans_v[tip1][ctp_v[tip2][1]]], ['s33', 1, vivod], ['s33i', 1, vivod]],
                        ['Ш-СД27', 'Шина СБ', 2, ['s4', 2, trans_v[tip1][ctp_v[tip2][2]]], ['s33', 1, vivod], ['s33i', 1, vivod]],
                        ['Ш-СД28', 'Шина СБ', 2, ['s3', 2, trans_v[tip1][ctp_v[tip2][3]]], ['s33', 1, vivod], ['s33i', 1, vivod]]]

        self.index = self.index + 1
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'ts',
                 self.L, self.L1, self.A, self.B,
                 self.C, self.dat['количество'], 'спецификация']]

        for i in svar_det:
            itog_svar = self.welded_part(i)

            for j in itog_svar:
                itog.append(j)

        for i in detali:
            itog_det = self.detail(i, 's')

            if itog_det == 0:   # только что расчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)

        self.prints(itog)
        return True

    def kz(self):
        print('5. Расчет концевой заглушки:')
        self.index = self.index + 1
        self.A = 138
        self.B = 152
        detali = [['lb', 2, self.os], ['lv', 2, self.os], ['lt', 1, self.os]]

        if self.dat['In'] in [630]:
            self.C = 117
        elif self.dat['In'] in [800]:
            self.C = 132
        elif self.dat['In'] in [1000]:
            self.C = 157
        elif self.dat['In'] in [1250]:
            self.C = 187
        elif self.dat['In'] in [1600]:
            self.C = 237
        elif self.dat['In'] in [2000, 2500]:
            self.C = 277
        elif self.dat['In'] in [2600, 3200]:
            self.C = 403
        elif self.dat['In'] in [4000, 5000]:
            self.C = 483
        elif self.dat['In'] in [6400]:
            self.C = '-'

        self.spisok_dla_mater['Nkon_zag'] = self.spisok_dla_mater['Nkon_zag'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

        print('index концевая заглушка', self.index)
        itog = [[self.index, self.dat['Серия'], self.dat['ip'], self.dat['Материал'], self.dat['In'],
                 self.dat['Кол. пров.'], self.dat['Наименование'], 'kz',
                 self.L, self.L1, self.A, self.B, self.C,
                 self.dat['количество'], 'спецификация']]

        for i in detali:
            itog_det = self.detail(i, 's')
            if itog_det == 0:  # только что рассчитывали сухарь, направляющую или фланец
                continue
            else:
                itog.append(itog_det)
        self.prints(itog)

        line_raskroi.komlektuyushie(self.dat, self.length_OS, self.spis_kompl).standart_izdel()
        return True

    def pn(self):   # Перевод нейтрали
        self.nestandart()
        self.spisok_dla_mater['Nsekc'] = self.spisok_dla_mater['Nsekc'] + int(self.dat['количество'])
        self.spisok_dla_mater['KolProv'] = self.dat['Кол. пров.']

    def bom(self):
        self.nestandart()

    def ks(self):   # Крепежная скоба
        self.nestandart()

    def ksb(self):  # Крышка стыка
        self.nestandart()

    def pp(self):   # Пружинный подвес
        self.nestandart()


class Detali:
    def __init__(self, os, input_data, coating, kol, tip, ABC, spis_kompl):
        self.name = input_data['Обозначение']    # Обозначение
        self.os = os  # Размер по осям
        self.material = input_data['Материал']
        self.seria = input_data['Серия']
        self.ip = input_data['ip']
        self.nominal = int(input_data['In'])  # вычислили номинал
        self.H_stenka = input_data['ширина стенки']  # ширина стенки
        self.H = input_data['ширина шины']  # ширина шины
        self.H_paketa = input_data['толщина пакета']  # толщина пакета
        self.S_sh = input_data['толщина шины']  # Толщина шины по умолчанию 6 мм.
        # расстояние развертки двойного гиба
        self.L1_sh_m = input_data['малый гиб']  # развертка малого гиба
        self.L1_sh_b = input_data['большой гиб']  # развертка большого гиба
        self.stp_L1 = input_data['СТП край вывод']
        self.stp_L2 = input_data['СТП центр вывод']
        self.L1Edge = input_data['фланец край']  # развертка крайней шины фланца
        self.L1Centre = input_data['фланец центр']  # развертка средней шины гиба
        self.StpEdge = input_data['СТП край']
        self.SptCentre = input_data['СТП центр']
        self.S_stenka = input_data['толщина стенки']
        self.S_sh_izol = input_data['толщина изоляции']
        self.H_krishka = input_data['ширина крышки']
        self.S_krishka = input_data['толщина крышки']
        self.S_krishka_sred = input_data['толщина крышки средней']
        self.R_sh = input_data['расстояние от оси до шины']
        self.R_kor = input_data['расстояние от оси до корпуса']
        # переменные для работы
        self.oboznachenie = ''
        self.naimenovanie = ''
        self.L = '-'
        self.L1 = '-'
        self.A = ABC[0]  #
        self.B = ABC[1]  #
        self.C = ABC[2]  #
        self.X = '-'
        self.Y = '-'
        self.Z = '-'
        self.a = []  # Возврать результата
        self.Nprov = input_data['Кол. пров.']
        self.Ka = input_data['K']       # К-фактор для гибов
        self.R = input_data['R']
        self.coating = coating          # цвет открашивания профиля
        self.kolN = kol                  # количество деталей в расчете
        self.tip = tip
        self.spis_kompl = spis_kompl        # словарь со списком комплектующих

    # Лист боковой
    def lb(self):
        nominal = {'630': 113, '800': 128, '1000': 153, '1250': 183,
                   '1600': 233, '2000': 273, '2500': 273, '2600': 299,
                   '3200': 399, '4000': 479, '5000': 479, '6400': '-'}
        self.A = 150
        self.B = nominal[str(self.nominal)]
        self.C = '-'
        self.oboznachenie = 'ЛБ'
        self.naimenovanie = 'Лист боковой'
        self.print_rezult()
        return self.a

    # Лист Верхний
    def lv(self):
        self.A = 150
        self.B = 138
        self.C = '-'
        self.oboznachenie = 'ЛВ'
        self.naimenovanie = 'Лист верхний'
        self.print_rezult()
        return self.a

    # Лист торцевой
    def lt(self):
        nominal = {'630': 117, '800': 132, '1000': 153, '1250': 187,
                   '1600': 237, '2000': 277, '2500': 277, '2600': 303, '3200': 403, '4000': 483, '5000': 483, '6400': '-'}
        self.A = 138
        self.B = nominal[str(self.nominal)]
        self.C = '-'
        self.oboznachenie = 'ЛТ'
        self.naimenovanie = 'Лист торцевой'
        self.print_rezult()
        return self.a

    # заглушки  !!! для 2500 неверная !!!
    def A000_774_01(self):
        if self.material == 'Al':
            nominal = {'630': [70, 56, 42], '800': [85, 71, 57], '1000': [110, 96, 82], '1250': [140, 126, 112],
                       '1600': [190, 176, 162], '2000': [230, 216, 202], '2500': [240, 220, 202],
                       '2600': [240, 220, 202], '3200': [0, 0, 0],
                       '4000': [230, 216, 202], '5000': [230, 216, 202]}
        else:
            nominal = {'800': [70, 56, 42], '1000': [85, 71, 57], '1250': [110, 96, 82], '1600': [140, 126, 112],
                       '2000': [190, 176, 162], '2500': [200, 180, 162], '3200': [0, 0, 0]}
        self.A = nominal[str(self.nominal)][0]
        self.B = nominal[str(self.nominal)][1]
        self.C = nominal[str(self.nominal)][2]
        self.oboznachenie = '000 774-01'
        self.naimenovanie = 'Заглушка для шины ТМ'
        self.print_rezult()
        return self.a

    # заглушки  !!! для 2500 неверная !!!
    def A000_774_02(self):
        if self.material == 'Al':
            nominal = {'630': [70, 56, 42], '800': [85, 71, 57], '1000': [110, 96, 82], '1250': [140, 126, 112],
                       '1600': [190, 176, 162], '2000': [230, 216, 202], '2500': [240, 220, 202],
                       '2600': [240, 220, 202], '3200': [0, 0, 0],
                       '4000': [230, 216, 202], '5000': [230, 216, 202]}
        else:
            nominal = {'800': [70, 56, 42], '1000': [85, 71, 57], '1250': [110, 96, 82], '1600': [140, 126, 112],
                       '2000': [190, 176, 162], '2500': [200, 180, 162], '3200': [0, 0, 0]}
        self.A = nominal[str(self.nominal)][0]
        self.B = nominal[str(self.nominal)][1]
        self.C = nominal[str(self.nominal)][2]
        self.oboznachenie = '000 774-02'
        self.naimenovanie = 'Заглушка для шины ТМ'
        self.print_rezult()
        return self.a

    # Уголок
    def u(self):
        self.L = float(self.H_stenka)
        self.oboznachenie = 'У'
        self.naimenovanie = 'Уголок_25х25х3'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    # фланец
    def fl_100(self):
        if self.material == 'Al':  # алюминий
            L = {'630': [182, 200], '800': [200, 200], '1000': [226, 200], '1250': [249, 200], '1600': [305, 200],
                 '2000': [351, 200], '2500': [351, 200], '3200': [504, 200], '3201': [504, 200], '2600': [504, 200],
                 '4000': [596, 200], '5000': [596, 200], '6400': [763, 200]}
        else:   # если медный проводник
            L = {'630': ['X', 'Y'], '800': [182, 200], '1000': [200, 200], '1250': [226, 200], '1600': [249, 200], '2000': [305, 200],
                 '2500': [305, 200], '3200': ['X', 'Y'], '3201': ['X', 'Y'], '4000': [504, 200],
                 '5000': [504, 200], '6400': ['X', 'Y']}

        self.A = L[str(self.nominal)][0]
        self.B = L[str(self.nominal)][1]
        self.oboznachenie = '000 170'
        self.naimenovanie = 'Фланец'
        self.print_rezult()
        return self.a

    # фланец
    def fl_130(self):
        if self.material == 'Al':  # алюминий
            L = {'630': [182, 245], '800': [200, 245], '1000': [226, 245], '1250': [249, 245], '1600': [305, 245],
                 '2000': [351, 245], '2500': [351, 245], '3200': [504, 245], '3201': [504, 245], '2600': [504, 245],
                 '4000': [596, 245], '5000': [596, 245], '6400': [763, 245]}
        else:  # если медный проводник
            L = {'630': ['X', 'Y'], '800': [182, 245], '1000': [200, 245], '1250': [226, 245], '1600': [249, 245],
                 '2000': [305, 245],
                 '2500': [305, 245], '3200': ['X', 'Y'], '3201': ['X', 'Y'], '4000': [504, 245],
                 '5000': [504, 245], '6400': ['X', 'Y']}

        self.A = L[str(self.nominal)][0]
        self.B = L[str(self.nominal)][1]
        self.oboznachenie = '000 170'
        self.naimenovanie = 'Фланец'
        self.print_rezult()
        return self.a

    # Токопроводящая пластина
    def tp(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.oboznachenie = 'ТП'
        self.naimenovanie = 'Пластина токопроводящая'
        if self.material == 'Al':  # алюминий
            L = {'250': 30, '400': 68, '630': 66, '800': 80, '1000': 108, '1250': 138, '1600': 185, '2000': 226,
                 '2500': 226, '2600': 226, '3200': 360, '3201': 360,
                 '4000': 434, '5000': 434, '6400': 654, '2501': 2500}
            if str(self.nominal) == '2500' or str(self.nominal) == '5000':
                self.profil(['профиль', self.naimenovanie + ' 2500', self.oboznachenie + '_2500', '90 90'], L[str(self.nominal)])
            else:
                self.profil(['профиль', self.naimenovanie, self.oboznachenie, '90 90'], L[str(self.nominal)])
        else:
            L = {'630': 66, '800': 66, '1000': 80, '1250': 108, '1600': 138, '2000': 185, '2500': 185, '3200': 234,
                 '4000': 360, '5000': 360, '6400': 540}
            if str(self.nominal) == '2500' or str(self.nominal) == '5000':
                self.profil(['профиль', self.naimenovanie + ' медная 2500', self.oboznachenie + '_2500', '90 90'], L[str(self.nominal)])
            else:
                self.profil(['профиль', self.naimenovanie + ' медная', self.oboznachenie, '90 90'], L[str(self.nominal)])
        self.L = L[str(self.nominal)]
        self.print_rezult()
        return self.a

    def vtulka(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.nominal != 2500 or self.nominal != 6400:
            self.L = 72
        else:
            self.L = 86
        self.oboznachenie = 'В'
        self.naimenovanie = 'Втулка'
        self.print_rezult()
        return self.a

    def ksb(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.oboznachenie = 'КСБ'
        self.naimenovanie = 'Крышка стыка'
        self.print_rezult()
        return self.a

    def dp(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.oboznachenie = 'Д'
        self.naimenovanie = 'Демпфер'
        self.print_rezult()
        return self.a

    def izol_k(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.oboznachenie = 'ИК'
        self.naimenovanie = 'Изолятор крайний'
        self.print_rezult()
        return self.a

    def izol_s(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.oboznachenie = 'ИС'
        self.naimenovanie = 'Изолятор средний'
        self.print_rezult()
        return self.a

    # Стенка стыка
    def ss(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'

        if self.nominal <= 2500:
            self.L = self.H_stenka + self.S_krishka * 2
        elif self.nominal >= 3200 and self.nominal < 6400:
            self.L = self.H_stenka * 2 + 3 + self.S_krishka * 2
        else:   # для 6400
            self.L = self.H_stenka * 3 + 6 + self.S_krishka * 2

        self.oboznachenie = 'СС'
        self.naimenovanie = 'Стенка стыка'
        self.profil(['профиль', 'Стенка стыка (Заготовка)', self.oboznachenie, '90 90'], self.L)
        self.print_rezult()
        return self.a

    # Сухарь
    def sux(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = 20
        self.oboznachenie = 'СУ'
        self.naimenovanie = 'Сухарь'
        self.print_rezult()
        self.profil(['профиль', 'Сухарь (Заготовка)', self.oboznachenie, '90 90'], self.L)
        return self.a

    # Направляющая
    def n(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'

        if self.nominal <= 2500:
            self.L = self.H_stenka + self.S_krishka * 2
        elif self.nominal > 2500 and self.nominal < 6400:
            self.L = self.H_stenka * 2 + 3 + self.S_krishka * 2
        else:   # для 6400
            self.L = self.H_stenka * 3 + 6 + self.S_krishka * 2

        self.oboznachenie = 'Н'
        self.naimenovanie = 'Направляющая'

        if self.nominal in [2500, 5000]:
            s = ['профиль', self.naimenovanie + '2500(Заготовка)', self.oboznachenie + '_2500', '90 90']
        else:
            s = ['профиль', self.naimenovanie, self.oboznachenie, '90 90']

        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    # Заглушка для трансформаторной секции
    def zts(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.material == 'Al':  # алюминий
            L = {'630': 109, '800': 124, '1000': 149, '1250': 179, '1600': 229, '2000': 269, '2500': 269, '3200': 395,
                 '4000': 475, '5000': 475, '6400': 681}
        else:
            L = {'630': 109, '800': 124, '1000': 149, '1250': 149, '1600': 179, '2000': 229, '2500': 229, '3200': 295,
                 '4000': 395, '5000': 395, '6400': 561}
        self.L1 = '-'
        self.L = L[str(self.nominal)]
        self.oboznachenie = 'З-ТС'
        self.naimenovanie = 'Заглушка'
        self.print_rezult()
        return self.a

    # Центователи для CR1
    def torcentr(self):
        self.L = float(self.H) + 40
        self.L1 = 100
        self.oboznachenie = 'ТЦ'
        self.naimenovanie = 'Торцевой центрователь'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def mfazcentr(self):
        self.L = 40
        self.L1 = 90
        self.oboznachenie = 'МЦ'
        self.naimenovanie = 'Межфазный центрователь'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    # вывод ОМФ
    def stp026v(self):
        self.L = 363.4
        self.L1 = 236
        self.oboznachenie = 'СТП 026 В'
        self.naimenovanie = 'Вывод ОМФ крайний'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    # вывод ОМФ
    def stp027v(self):
        self.L = 256.4
        self.L1 = 236
        self.oboznachenie = 'СТП 027 В'
        self.naimenovanie = 'Вывод ОМФ средний'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    # для секции компенсации
    def sk_tr(self):
        self.L = 515.8
        self.oboznachenie = 'Ск-Тр'
        self.naimenovanie = 'Скоба транспортировочная'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def A000_125(self):
        self.oboznachenie = '000 125'
        self.naimenovanie = 'Фланец СК'
        if self.nominal == 630:
            self.A = '189'  #
            self.B = '140'  #
            self.C = '48'  #
        elif self.nominal == 800:
            self.A = '204'  #
            self.B = '140'  #
            self.C = '63'  #
        elif self.nominal == 1000:
            self.A = '219'  #
            self.B = '140'  #
            self.C = '88'  #
        elif self.nominal == 1250:
            self.A = '249'  #
            self.B = '140'  #
            self.C = '118'  #
        elif self.nominal == 1600:
            self.A = '299'  #
            self.B = '140'  #
            self.C = '168'  #
        elif self.nominal == 2000:
            self.A = '339'  #
            self.B = '140'  #
            self.C = '208'  #
        elif self.nominal == 2500:
            self.A = '339'  #
            self.B = '145'  #
            self.C = '208'  #
        self.print_rezult()
        return self.a

    def A000_125_01(self):
        self.oboznachenie = '000 125-01'
        self.naimenovanie = 'Фланец СК'
        if self.nominal == 630:
            self.A = '189'  #
            self.B = '140'  #
            self.C = '48'  #
        elif self.nominal == 800:
            self.A = '204'  #
            self.B = '140'  #
            self.C = '63'  #
        elif self.nominal == 1000:
            self.A = '219'  #
            self.B = '140'  #
            self.C = '88'  #
        elif self.nominal == 1250:
            self.A = '249'  #
            self.B = '140'  #
            self.C = '118'  #
        elif self.nominal == 1600:
            self.A = '299'  #
            self.B = '140'  #
            self.C = '168'  #
        elif self.nominal == 2000:
            self.A = '339'  #
            self.B = '140'  #
            self.C = '208'  #
        elif self.nominal == 2500:
            self.A = '339'  #
            self.B = '145'  #
            self.C = '208'  #
        self.print_rezult()
        return self.a

    def A000_125_02(self):
        self.oboznachenie = '000 125-02'
        self.naimenovanie = 'Фланец СК'
        if self.nominal == 630:
            self.A = '208'  #
            self.B = '149'  #
            self.C = '48'  #
        elif self.nominal == 800:
            self.A = '223'  #
            self.B = '149'  #
            self.C = '66'  #
        elif self.nominal == 1000:
            self.A = '238'  #
            self.B = '149'  #
            self.C = '88'  #
        elif self.nominal == 1250:
            self.A = '268'  #
            self.B = '149'  #
            self.C = '118'  #
        elif self.nominal == 1600:
            self.A = '318'  #
            self.B = '149'  #
            self.C = '168'  #
        elif self.nominal == 2000:
            self.A = '358'  #
            self.B = '149'  #
            self.C = '208'  #
        elif self.nominal == 2500:
            self.A = '358'  #
            self.B = '154'  #
            self.C = '208'  #
        self.print_rezult()
        return self.a

    def A000_125_03(self):
        self.oboznachenie = '000 125-03'
        self.naimenovanie = 'Фланец СК'
        if self.nominal == 630:
            self.A = '208'  #
            self.B = '149'  #
            self.C = '48'  #
        elif self.nominal == 800:
            self.A = '223'  #
            self.B = '149'  #
            self.C = '66'  #
        elif self.nominal == 1000:
            self.A = '238'  #
            self.B = '149'  #
            self.C = '88'  #
        elif self.nominal == 1250:
            self.A = '268'  #
            self.B = '149'  #
            self.C = '118'  #
        elif self.nominal == 1600:
            self.A = '318'  #
            self.B = '149'  #
            self.C = '168'  #
        elif self.nominal == 2000:
            self.A = '358'  #
            self.B = '149'  #
            self.C = '208'  #
        elif self.nominal == 2500:
            self.A = '358'  #
            self.B = '154'  #
            self.C = '208'  #
        self.print_rezult()
        return self.a

    def A000_120(self):
        self.L = 624.5
        self.L1 = 625.4
        self.oboznachenie = '000 120'
        self.naimenovanie = 'Шина'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def A000_119(self):
        self.L = 624.5
        self.L1 = 633.1
        self.oboznachenie = '000 119'
        self.naimenovanie = 'Шина'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def A000_128(self):
        self.L = 94

        if self.nominal < 2500:
            self.L1 = 121.1
        else:
            self.L1 = 120.5

        self.oboznachenie = '000 128'
        self.naimenovanie = 'Шина PE ФБ'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def lvn(self):
        self.L = 282

        if self.nominal < 2500:
            self.L1 = 296
        else:
            self.L1 = 306

        self.oboznachenie = 'ЛВ/Н'
        self.naimenovanie = 'Лист верхний/нижний'
        self.A = '-'  #
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def klb(self):

        if self.nominal == 630:
            self.A = '205'  #
        elif self.nominal == 800:
            self.A = '220'  #
        elif self.nominal == 1000:
            self.A = '235'  #
        elif self.nominal == 1250:
            self.A = '265'  #
        elif self.nominal == 1600:
            self.A = '315'  #
        elif self.nominal == 2000:
            self.A = '355'  #
        elif self.nominal == 2500:
            self.A = '355'  #

        self.oboznachenie = 'КЛБ'
        self.naimenovanie = 'Лист боковой'
        self.B = '282'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def lvb(self):

        if self.nominal < 2500:
            self.A = '315'  #
        else:
            self.A = '325'  #

        self.oboznachenie = 'ЛВБ'
        self.naimenovanie = 'Лист верхний/нижний Б'
        self.B = '282'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def lbm(self):
        if self.nominal == 630:
            self.A = '224'  #
        elif self.nominal == 800:
            self.A = '239'  #
        elif self.nominal == 1000:
            self.A = '254'  #
        elif self.nominal == 1250:
            self.A = '284'  #
        elif self.nominal == 1600:
            self.A = '334'  #
        elif self.nominal == 2000:
            self.A = '374'  #
        elif self.nominal == 2500:
            self.A = '374'  #

        self.oboznachenie = 'ЛБМ'
        self.naimenovanie = 'Лист боковой Б'
        self.B = '282'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol2(self):
        self.L = '282'
        self.oboznachenie = 'У2'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol1(self):
        if self.nominal in [2500]:
            self.L = '325'
        else:
            self.L = '315'
        self.oboznachenie = 'У1'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol1_2(self):
        if self.nominal in [2500]:
            self.L = '296'
        else:
            self.L = '306'
        self.oboznachenie = 'У1'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol(self):
        if self.nominal in [630]:
            self.L = '164'
        elif self.nominal in [800]:
            self.L = '179'
        elif self.nominal in [1000]:
            self.L = '194'
        elif self.nominal in [1250]:
            self.L = '224'
        elif self.nominal in [1600]:
            self.L = '274'
        elif self.nominal in [2000]:
            self.L = '314'
        elif self.nominal in [2500]:
            self.L = '314'
        self.oboznachenie = 'У'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol_2(self):
        if self.nominal in [630]:
            self.L = '145'
        elif self.nominal in [800]:
            self.L = '160'
        elif self.nominal in [1000]:
            self.L = '175'
        elif self.nominal in [1250]:
            self.L = '205'
        elif self.nominal in [1600]:
            self.L = '255'
        elif self.nominal in [2000]:
            self.L = '295'
        elif self.nominal in [2500]:
            self.L = '295'
        self.oboznachenie = 'У2'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def ugol2_z(self):
        self.L = '282'
        self.oboznachenie = 'У2-З'
        self.naimenovanie = 'Уголок'
        self.A = '30'
        self.B = '30'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def A000_108(self):
        self.L = '210'
        self.L1 = '224.2'
        self.oboznachenie = '000 108'
        self.naimenovanie = 'Шина компенсации'
        self.A = '-'
        self.B = '-'  #
        self.C = '-'  #
        self.print_rezult()
        return self.a

    def k(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'

        if self.name in ['тв', 'tv']:
            self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_kor) * 2
        elif self.name in ['пф', 'pf']:
            self.L = float(self.os) - float(self.R_kor) - 4
        elif self.name in ['тс', 'tsv']:
            self.L = float(self.os[0]) - float(self.R_kor)
        elif self.name in ['sk']:
            self.L = 428.5
        else:
            self.L = float(self.os) - float(self.R_kor) * 2

        if self.coating == 's':
            self.naimenovanie = 'Крышка крашенная'
            self.oboznachenie = 'К-кр'
            s = ['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90']
        else:
            self.naimenovanie = 'Крышка'
            self.oboznachenie = 'К'
            s = ['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 90']

        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    def k1(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'uv', 'uvf', 'ugf']:
            Alfa = (180 - int(self.C)) / 2
        else:
            Alfa = 45
            self.C = '-'

        self.L = round(float(self.os) - float(self.R_kor) + float(self.H_krishka) / 2 * math.tan(math.radians(Alfa)), 1)
        self.oboznachenie = 'К1'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 +45'], self.L)
        return self.a

    def k1f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - 4
        self.oboznachenie = 'К1'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 +45'], self.L)
        return self.a

    def k2(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'uv', 'uvf', 'ugf']:
            Alfa = (180 - int(self.C)) / 2
        else:
            Alfa = 45
            self.C = '-'

        self.L = round(float(self.os) - float(self.R_kor) + float(self.H_krishka) / 2 * math.tan(math.radians(Alfa)), 1)
        self.oboznachenie = 'К2'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 -45'], self.L)
        return self.a

    def k2f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - 4
        self.oboznachenie = 'К2'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 -45'], self.L)
        return self.a

    def k3(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'ugf']:
            Alfa = int(self.C) / 2
        else:
            Alfa = 45
            self.C = '-'

        if int(self.nominal) >= 1600:
            self.L = float(self.os) - float(self.R_kor) + float(self.H_stenka) / 2 / math.tan(math.radians(Alfa)) + float(self.S_krishka) + 1
        else:
            self.L = float(self.os) - float(self.R_kor) + float(self.H_stenka) / 2 / math.tan(math.radians(Alfa)) + float(self.S_krishka)
        #print(str(self.os) + '-' + str(self.R_kor) + '+' + str(self.H_stenka) + '/2+' + str(self.S_krishka) + '=' + str(self.L))
        self.oboznachenie = 'К3'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 +45s'], self.L)
        return self.a

    # для УВФ и ЗВФ
    def k3f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        #print('угол вертикальный крыка')
        self.L = float(self.os) + float(self.H_stenka) / 2 + float(self.S_krishka) - 4
        #print(str(self.os) + '-' + str(self.R_kor) + '+' + str(self.H_stenka) + '/2+' + str(self.S_krishka) + '=' + str(self.L))
        self.oboznachenie = 'К3'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 +45s'], self.L)
        return self.a

    def k4(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'ugf']:
            Alfa = int(self.C) / 2
        else:
            Alfa = 45
            self.C = '-'

        self.L = round(float(self.os) - float(self.R_kor) - float(self.H_stenka) / 2 / math.tan(math.radians(Alfa)), 1)
        #print(str(float(self.os)) + '-' + str(float(self.R_kor))  + '-' + str(float(self.H_stenka)) + '/' + '2' + '=' + str(self.L))
        self.oboznachenie = 'К4'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 -45s'], self.L)
        return self.a

    # для УВФ и ЗВФ
    def k4f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_stenka) / 2 - 4
        #print(str(float(self.os)) + '-' + str(float(self.R_kor)) + '-' + str(float(self.H_stenka)) + '/' + '2' + '=' + str(self.L))
        self.oboznachenie = 'К4'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 -45s'], self.L)
        return self.a

    # для ТВ двухэтажной
    def k4t(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) - float(self.H_stenka) - 1.5
        # print(str(float(self.os)) + '-' + str(float(self.R_kor))  + '-' + str(float(self.H_stenka)) + '/' + '2' + '=' + str(self.L))
        self.oboznachenie = 'К4'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '90 -45s'], self.L)
        return self.a

    def k5(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka)
        self.oboznachenie = 'К5'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '-45 +45'], self.L)
        return self.a

    def k7(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka)
        self.oboznachenie = 'К7'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '+45 +45'], self.L)
        return self.a

    def k8(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka)
        self.oboznachenie = 'К8'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '-45 -45'], self.L)
        return self.a

    def k9(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.S_krishka)
        self.oboznachenie = 'К9'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '+45s -45s'], self.L)
        return self.a

    def k11(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) + float(self.S_krishka) * 2
        self.oboznachenie = 'К11'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '+45s +45s'], self.L)
        return self.a

    def k12(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka)
        self.oboznachenie = 'К12'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '-45s -45s'], self.L)
        return self.a

    def k13(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 + float(self.H_stenka) / 2 + float(self.S_krishka)
        self.oboznachenie = 'К13'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '+45s +45'], self.L)
        return self.a

    def k14(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 + float(self.H_stenka) / 2 + float(self.S_krishka)
        self.oboznachenie = 'К14'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '+45s -45'], self.L)
        return self.a

    def k15(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - float(self.H_stenka) / 2
        self.oboznachenie = 'К15'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '-45s +45'], self.L)
        return self.a

    def k16(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - float(self.H_stenka) / 2
        self.oboznachenie = 'К16'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка без покрытия 3м.', 'К_нк_3', '-45s -45'], self.L)
        return self.a

    # крышка с отверситем для втычной розетки для типов 1 и 2
    def k18(self):
        if int(self.tip[0]) in [1, 2]:
            self.B = '-'
            self.C = '-'
            self.L = float(self.os) - float(self.R_kor) * 2
            self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка крашенная'
        self.oboznachenie = 'К18'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с отверситем для втычной розетки для типов 3 и 4
    def k18_01(self):
        self.L = float(self.os) - float(self.R_kor) * 2
        self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка крашенная'
        self.oboznachenie = 'К18-01'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с отверситем для втычной розетки для типов 5 и 6
    def k18_02(self):
        self.L = float(self.os) - float(self.R_kor) * 2
        self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка крашенная'
        self.oboznachenie = 'К18-02'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    def k19(self):      # крышка для трансформаторной секции
        #print('self.os', self.os)
        self.L = float(self.os[0]) - float(self.R_kor)
        self.L1 = float(self.os[1]) - float(self.R_kor)
        self.A = float(self.os[2])
        self.B = float(self.os[3])
        self.C = float(self.os[4])
        self.oboznachenie = 'К19'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    def k20(self):      # крышка для отбора мощности с фиксированным выводом
        #print('self.os', self.os)
        self.L = float(self.os[0]) - float(self.R_kor)
        self.L1 = float(self.os[1]) - float(self.R_kor)
        self.A = float(self.os[2])
        self.B = float(self.os[3])
        self.C = float(self.os[4])
        self.oboznachenie = 'К19'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    def _(self):      # крышка для отбора мощности с фиксированным выводом
        #print('self.os', self.os)
        self.L = float(self.os[0]) - float(self.R_kor)
        self.L1 = float(self.os[1]) - float(self.R_kor)
        self.A = float(self.os[2])
        self.B = float(self.os[3])
        self.C = float(self.os[4])
        self.oboznachenie = 'К19'
        self.naimenovanie = 'Крышка'
        self.print_rezult()
        self.profil(['профиль', 'Крышка окрашенная 2.82м.', 'К_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с выступом
    def kv(self):  # N это длина по оси КРЫШКИ
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['тв', 'tv']:
            self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_kor) * 2
        elif self.name in ['пф', 'pf', 'pfk']:
            self.L = float(self.os) - float(self.R_kor) - 4
        elif self.name in ['тс', 'tsv']:
            self.L = float(self.os[0]) - float(self.R_kor)
        else:
            self.L = float(self.os) - float(self.R_kor) * 2
        if self.coating == 's':
            self.naimenovanie = 'Крышка с выступом крашенная'
            self.oboznachenie = 'КВ-кр'
            s = ['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90']
        else:
            self.naimenovanie = 'Крышка с выступом'
            self.oboznachenie = 'КВ'
            s = ['профиль', 'Крышка с выступом 2.82м.', 'КВ_нк_2.82', '90 90']
        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    # для фланца крышка с вычетом плюс 118.5
    def kva(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) - 4
        self.oboznachenie = 'КВ'
        self.naimenovanie = 'Крышка с выступом крашенная'
        self.print_rezult()
        self.profil(['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с выступом с отверстием для втычной розетки для типов 1 и 2
    def kv18(self):
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) * 2
        self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка с выступом крашенная'
        self.oboznachenie = 'КВ18'
        self.print_rezult()
        self.profil(['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с выступом с отверситем для втычной розетки для типов 3 и 4
    def kv18_01(self):
        self.L = float(self.os) - float(self.R_kor) * 2
        self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка с выступом крашенная'
        self.oboznachenie = 'КВ18-01'
        self.print_rezult()
        self.profil(['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с выступом с отверситем для втычной розетки для типов 5 и 6
    def kv18_02(self):
        self.L = float(self.os) - float(self.R_kor) * 2
        self.A = str(float(self.A) - float(self.R_kor))
        self.naimenovanie = 'Крышка с выступом крашенная'
        self.oboznachenie = 'КВ18-02'
        self.print_rezult()
        self.profil(['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90'], self.L)
        return self.a

    # крышка с выступом для отбора мощности с фиксированным выводом
    def kv20(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['тв', 'tv']:
            self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_kor) * 2
        elif self.name in ['пф', 'pf', 'pfk']:
            self.L = float(self.os) - float(self.R_kor) - 4
        elif self.name in ['тс', 'tsv']:
            self.L = float(self.os[0]) - float(self.R_kor)
        else:
            self.L = float(self.os) - float(self.R_kor) * 2
        if self.coating == 's':
            self.naimenovanie = 'Крышка с выступом крашенная'
            self.oboznachenie = 'КВ-кр'
            s = ['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90']
        else:
            self.naimenovanie = 'Крышка с выступом'
            self.oboznachenie = 'КВ'
            s = ['профиль', 'Крышка с выступом 2.82м.', 'КВ_нк_2.82', '90 90']
        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    # крышка с выступом для отбора мощности с фиксированным выводом
    def kv21(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['тв', 'tv']:
            self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_kor) * 2
        elif self.name in ['пф', 'pf', 'pfk']:
            self.L = float(self.os) - float(self.R_kor) - 4
        elif self.name in ['тс', 'tsv']:
            self.L = float(self.os[0]) - float(self.R_kor)
        else:
            self.L = float(self.os) - float(self.R_kor) * 2
        if self.coating == 's':
            self.naimenovanie = 'Крышка с выступом крашенная'
            self.oboznachenie = 'КВ-кр'
            s = ['профиль', 'Крышка с выступом окрашенная 2.82м.', 'КВ_к_2.82', '90 90']
        else:
            self.naimenovanie = 'Крышка с выступом'
            self.oboznachenie = 'КВ'
            s = ['профиль', 'Крышка с выступом 2.82м.', 'КВ_нк_2.82', '90 90']
        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    # стенка
    # стенка крашенная используется для прямых секций
    def c(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['пф', 'pf', 'pfk']:
            self.L = float(self.os) - float(self.R_kor) - 4
        elif self.name in ['п', 'тг', 'ом', 'pt', 'tg', 'pr']:
            self.L = float(self.os) - float(self.R_kor) * 2 - 1
        elif self.name in ['уг', 'угф', 'ug', 'ugf']:
            self.L = float(self.os) - float(self.R_kor) + float(self.H_paketa) / 2
        elif self.name in ['тс', 'tsv']:
            self.L = float(self.os[0]) - float(self.R_kor)
        elif self.name in ['sk']:
            self.L = 428.5
        else:
            self.L = 'неизветсно'
        if self.coating == 's':
            self.oboznachenie = 'С-кр'
            self.naimenovanie = 'Стенка крашенная'
            nominal = self.print_rezult()
            self.profil(['профиль', 'Стенка ' + str(nominal) + ' окрашенный 2.82м.', 'С_' + str(nominal) + '_к_2.82', '90 90'], self.L)
        else:
            self.oboznachenie = 'С'
            self.naimenovanie = 'Стенка'
            nominal = self.print_rezult()
            self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # стенка для С-СД2. то же что и С4 минус 25 мм. ВНУТРЕНЯЯ
    def cA(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) - float(self.H_paketa) / 2 - self.S_stenka
        #print('!!!!!!!!', self.os, self.R_kor, self.H_paketa)
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # стенка для С-СД2. то же что и С4 минус 25 мм. ВНУТРЕНЯЯ ДЛЯ ФЛАНЦЕВ!
    def cAf(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_paketa) / 2 - self.S_stenka - 4
        #print('!!!!!!!!', self.os, self.R_kor, self.H_paketa)
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # стенка для замены С-СД3 для номинала 2000А. то же что и С3 без ширины стенки ВНЕШНЯЯ
    def cB(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) + float(self.H_paketa) / 2
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # стенка для замены С-СД3 для номинала 2000А. то же что и С3 без ширины стенки ВНЕШНЯЯ ДЛЯ ФЛАНЦЕВ!
    def cBf(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_paketa) / 2 - 4
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # стенка для Z горизонтальной для оси Y внешняя
    def cC(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - self.S_stenka
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # для ТВ
    def ct(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_kor) * 2
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    # для ТВ по оси Z
    def ctz(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.nominal in [3200, 4000, 5000]:      # для ТВ по оси Z для двухэтажной секции
            self.L = float(self.os) - float(self.R_kor) - float(self.H_stenka) - 1.5
        else:
            self.L = float(self.os) - float(self.R_kor) - float(self.H_stenka) / 2
        self.oboznachenie = 'С'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 90'], self.L)
        return self.a

    def c1(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'ugf']:
            Alfa = int(self.C) / 2
        else:
            Alfa = 45
            self.C = '-'

        self.L = float(self.os) - float(self.R_kor) + float(self.H_stenka) / 2 / math.tan(math.radians(Alfa))
        self.oboznachenie = 'С1'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45'], self.L)
        return self.a

    # для УВФ и ЗВФ
    def c1f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 - 4
        self.oboznachenie = 'С1'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45'], self.L)
        return self.a

    # Для средней оси "y" комбинированной секции
    def c1a(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['кп', 'kp', 'kpfuv']:
            self.L = float(self.os) + float(self.H_stenka) / 2 + float(self.H_paketa) / 2
        elif self.name in ['кл', 'kl']:
            self.L = float(self.os) + float(self.H_stenka) / 2 - float(self.H_paketa) / 2 - float(self.S_stenka)
        self.oboznachenie = 'С1'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45'], self.L)
        return self.a

    def c2(self):
        self.A = '-'
        self.B = '-'

        if self.name in ['ug', 'ugf']:
            Alfa = int(self.C) / 2
        else:
            Alfa = 45
            self.C = '-'

        self.L = float(self.os) - float(self.R_kor) + float(self.H_stenka) / 2 / math.tan(math.radians(Alfa))
        self.oboznachenie = 'С2'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 -45'], self.L)
        return self.a

    # для УВФ и ЗВФ
    def c2f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 - 4
        self.oboznachenie = 'С2'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 -45'], self.L)
        return self.a

    # Для средней оси "y" комбинированной секции
    def c2a(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['кп', 'kp', 'kpfuv']:
            self.L = float(self.os) + float(self.H_stenka) / 2 - float(self.H_paketa) / 2 - float(self.S_stenka)
        elif self.name in ['кл', 'kl', 'klfuv']:
            self.L = float(self.os) + float(self.H_stenka) / 2 + float(self.H_paketa) / 2
        self.oboznachenie = 'С2'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 -45'], self.L)
        return self.a

    def c3(self):
        self.A = '-'
        self.B = '-'
        Alfa = (180 - int(self.C)) / 2

        if self.seria in ['CR1', 'CR2']:
            self.L = round(float(self.os) - float(self.R_kor) + (float('100') / 2 + float(self.S_stenka)) * math.tan(math.radians(Alfa)), 1)
        else:
            self.L = round(float(self.os) - float(self.R_kor) + (float(self.H_paketa) / 2 + float(self.S_stenka)) * math.tan(math.radians(Alfa)), 1)

        self.oboznachenie = 'С3'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45s'], self.L)
        return self.a

    # Стенка для С-СД4 замена С9
    def c3a(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os)
        self.oboznachenie = 'С3'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45s'], self.L)
        return self.a

    def c4(self):
        self.A = '-'
        self.B = '-'
        Alfa = (180 - int(self.C)) / 2

        if self.seria in ['CR1', 'CR2']:
            self.L = round(float(self.os) - float(self.R_kor) - 100 / 2 * math.tan(math.radians(Alfa)), 1)
        else:
            self.L = round(float(self.os) - float(self.R_kor) - float(self.H_paketa) / 2 * math.tan(math.radians(Alfa)), 1)

        self.oboznachenie = 'С4'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 -45s'], self.L)
        return self.a

    # для Z-горизонтальной с фланцем
    def c3f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_paketa) / 2 + float(self.S_stenka) - 4
        self.oboznachenie = 'С3'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 +45s'], self.L)
        return self.a

    def c4f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_paketa) / 2 - 4
        self.oboznachenie = 'С4'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '90 -45s'], self.L)
        return self.a

    def c5(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka)
        self.oboznachenie = 'С5'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45 +45'], self.L)
        return self.a

    def c7(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka)
        # print(str(self.os) + ' + ' + str(self.H_stenka) + ' = ' + str(self.L))
        self.oboznachenie = 'С7'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' +str(nominal) + '_нк_3', '+45 +45'], self.L)
        return self.a

    def c8(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka)
        self.oboznachenie = 'С8'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45 -45'], self.L)
        return self.a

    def c9(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.S_stenka)
        self.oboznachenie = 'С9'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45s -45s'], self.L)
        return self.a

    def c11(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.S_stenka) * 2 + float(self.H_paketa)
        self.oboznachenie = 'С11'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45s +45s'], self.L)
        return self.a

    def c12(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_paketa)
        self.oboznachenie = 'С12'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '+45s -45s'], self.L)
        return self.a

    def c13(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 + float(self.S_stenka) + float(self.H_paketa) / 2
        self.oboznachenie = 'С13'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '+45s +45'], self.L)
        return self.a

    def c14(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 + float(self.S_stenka) + float(self.H_paketa) / 2
        self.oboznachenie = 'С14'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '+45s -45'], self.L)
        return self.a

    def c15(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 - float(self.H_paketa) / 2
        self.oboznachenie = 'С15'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45s +45'], self.L)
        return self.a

    def c16(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_stenka) / 2 - float(self.H_paketa) / 2
        self.oboznachenie = 'С16'
        self.naimenovanie = 'Стенка'
        nominal = self.print_rezult()
        self.profil(['профиль', 'Стенка ' + str(nominal) + 'без покрытия 3м.', 'С_' + str(nominal) + '_нк_3', '-45s -45'], self.L)
        return self.a

    # крышка средняя
    def kc(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.name in ['тв', 'tv']:
            self.L = float(self.A) + float(self.B) - float(self.R_kor) * 2
        elif self.name in ['пф', 'pf', 'pfk']:
            self.L = float(self.os) - float(self.R_kor) - 4
        else:
            self.L = float(self.os) - float(self.R_kor) * 2
        if self.coating == 's':
            self.oboznachenie = 'КС-кр'
            self.naimenovanie = 'Крышка средняя крашенная'
            s = ['профиль', 'Крышка средняя окрашенная 2.82м.', 'КС_к_2.82', '90 90']
        else:
            self.oboznachenie = 'КС'
            self.naimenovanie = 'Крышка средняя'
            s = ['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 90']
        self.print_rezult()
        self.profil(s, self.L)
        return self.a

    # для угф стенка с вычетом плюс 118.5 - 4
    def kca(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - 4
        self.oboznachenie = 'КС'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 90'], self.L)
        return self.a

    def kc1(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) + float(self.H_krishka) / 2
        self.oboznachenie = 'КС1'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 +45'], self.L)
        return self.a

    # для УГФ
    def kc1f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) / 2 - 4
        self.oboznachenie = 'КС1'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 +45'], self.L)
        return self.a

    def kc2(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        for self.name in ['klfuv']:
            self.L = float(self.os) - 4 - float(self.H_stenka) / 2 + 18.5  # 18.5-потому что по центру
        else:
            self.L = float(self.os) - float(self.R_kor) - float(self.H_stenka) / 2 + 18.5   # 18.5-потому что по центру
        self.oboznachenie = 'КС2'
        #print(str(self.L), '=', str(float(self.os)), '-', str(float(self.R_kor)), '-', str(float(str(self.H_stenka))),
             # '/ 2 + 18.5')
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 +45s'], self.L)
        return self.a

    def kc2a(self):     # для Z-вертикальной по оси Z
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_kor) + float(self.H_stenka) / 2 + 21.5
        #print(str(self.L), '=', str(float(self.os)), '-', str(float(self.R_kor)), '+', str(float(str(self.H_stenka))),
            #  '/ 2 + 21.5')
        self.oboznachenie = 'КС2'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 +45s'], self.L)
        return self.a

    # для УВФ
    def kc2f(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_stenka) / 2 + 18.5 - 4
        self.oboznachenie = 'КС2'
        #print(str(self.L), '=', str(float(self.os)), '-', str(float(self.R_kor)), '-', str(float(str(self.H_stenka))),
              #'/ 2 + 18.5')
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '90 +45s'], self.L)
        return self.a

    def kc3(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) * 2
        self.oboznachenie = 'КС3'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45 -45'], self.L)
        return self.a

    def kc4(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka)
        self.oboznachenie = 'КС4'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45 +45'], self.L)
        return self.a

    def kc5(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + 40
        self.oboznachenie = 'КС5'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45s +45s'], self.L)
        return self.a

    def kc6(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) + float(self.H_krishka) * 2
        self.oboznachenie = 'КС6'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45s +45s'], self.L)
        return self.a

    def kc8(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_stenka) / 2 + 18.5 + float(self.H_krishka) / 2
        self.oboznachenie = 'КС8'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45 +45s'], self.L)
        return self.a

    def kc9(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H_stenka) / 2 + 18.5 + float(self.H_krishka) / 2
        # print(str(self.L), '=', str(float(self.os)), '-', str(float(self.H_stenka)),  '/2 +18.5',  '+', str(float(self.H_krishka)), '/ 2')
        self.oboznachenie = 'КС9'
        self.naimenovanie = 'Крышка средняя'
        self.print_rezult()
        self.profil(['профиль', 'Крышка средняя без покрытия 3м.', 'КС_нк_3', '+45 +45s'], self.L)
        return self.a

    # проставок | для 3-х проводных П и УВ
    def stp09v(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = 23
        self.oboznachenie = 'СТП 09 В'
        self.naimenovanie = 'Зубчатый вывод'
        self.print_rezult()
        self.profil(['профиль', 'Шина 630', 'Ш_630', '90 90'], self.L)
        #print(self.a)
        return self.a

    # проставок | для 3-х проводных П и УВ
    def s(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.seria in ['CR1']:
            if self.name in ['ув', 'uv']:
                if self.os[1] == 'x':
                    self.L = float(self.os[0]) - self.R_sh - self.H / 2
                else:
                    self.L = float(self.os[0]) - self.R_sh + self.H / 2
            elif self.name in ['п', 'pt']:
                self.L = float(self.os) - float(self.R_sh) * 2
        else:
            if str(self.Nprov) in ['4', '3+1']:
                self.L = float(self.os) - float(self.H)
            else:   # 3-х проводной
                if self.name in ['п', 'pt']:
                    self.L = float(self.os) - float(self.R_sh) * 2
                elif self.name in ['пф', 'pf', 'pfk']:
                    self.L = float(self.os) - float(self.R_sh) + self.L1Centre
                elif self.name in ['зв', 'звф', 'zv', 'zvf']:
                    self.L = float(self.os) - float(self.H)
                else:   # УВ
                    self.L = float(self.os) + float(self.H) / 2 - float(self.R_sh)
        self.oboznachenie = 'Ш'
        self.naimenovanie = 'Шина'
        sI = self.print_rezult()
        self.profil(['профиль', 'Шина ' + sI, 'Ш_' + sI, '90 90'], self.L)
        return self.a

    # проставок | для 3-х проводных П и УВ
    def s_01(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.oboznachenie = 'Ш-01'
        self.naimenovanie = 'Шина'
        sI = self.print_rezult()
        self.profil(['профиль', 'Шина ' + sI, 'Ш_' + sI, '90 90'], self.L)
        return self.a

    # для 3-х проводных УВ
    def sa(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.H) / 2 - float(self.R_sh)
        self.oboznachenie = 'Ш'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L)
        return self.a

    # для прямых секций
    def s1(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_b * 2
        self.oboznachenie = 'Ш1'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для отбора мощности
    def s1_01(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        print(self.os)
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_b * 2
        self.oboznachenie = 'Ш1-01'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для ТВ
    def s1t(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_b * 2
        self.oboznachenie = 'Ш1'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для прямых секций
    def s2(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_m * 2
        self.oboznachenie = 'Ш2'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для отбора мощности
    def s2_01(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_m * 2
        self.oboznachenie = 'Ш2-01'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для ТВ
    def s2t(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os[0]) + float(self.os[1]) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_m * 2
        self.oboznachenie = 'Ш2'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для отбора мощности
    def s1om1(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_b * 2
        self.oboznachenie = 'Ш1'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s1om4(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_b * 2
        self.oboznachenie = 'Ш1'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s2om2(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_m
        self.oboznachenie = 'Ш2'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s2om3(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) * 2
        self.L1 = float(self.L) + self.L1_sh_m
        self.oboznachenie = 'Ш2'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для вертикального угла и Z в том числе на 3- х проводной
    def s3(self):  # для углов вертикальных с плюсом
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) + float(self.H) / 2
        # print('s3: ' + str(self.os) + ' - ' + str(self.R_sh) + ' + ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_b
        self.oboznachenie = 'Ш3'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для Z 3- х проводной
    def s_3(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) + float(self.H) / 2
        # print('s3: ' + str(self.os) + ' - ' + str(self.R_sh) + ' + ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L)
        self.oboznachenie = 'Ш'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для ТВ
    def s3t(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.nominal in [3200, 4000, 5000]:
            self.L = float(self.os) - float(self.R_sh) - float(self.H) - 3
        else:
            self.L = float(self.os) - float(self.R_sh) - float(self.H) / 2
        # print('s3: ' + str(self.os) + ' - ' + str(self.R_sh) + ' + ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_b
        self.oboznachenie = 'Ш3'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # та же шина что и Ш3 но для углов вертикальных с минусом
    def s3a(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) - float(self.H) / 2
        # print('s3a: ' + str(self.os) + ' - ' + str(self.R_sh) + ' - ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_b
        self.oboznachenie = 'Ш3'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s4(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) + float(self.H) / 2
        # print('s4: ' + str(self.os) + ' - ' + str(self.R_sh) + ' +  ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_m
        self.oboznachenie = 'Ш4'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # та же шина что и Ш4 но для углов вертикальных с минусом
    def s4a(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = float(self.os) - float(self.R_sh) - float(self.H) / 2
        # print('s4a: ' + str(self.os) + ' - ' + str(self.R_sh) + ' -  ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_m
        self.oboznachenie = 'Ш4'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для ТВ
    def s4t(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.nominal in [3200, 4000, 5000]:
            self.L = float(self.os) - float(self.R_sh) - float(self.H) - 3
        else:
            self.L = float(self.os) - float(self.R_sh) - float(self.H) / 2
        # print('s3: ' + str(self.os) + ' - ' + str(self.R_sh) + ' + ' + str(self.H) + ' / 2 = ' + str(self.L))
        self.L1 = float(self.L) + self.L1_sh_m
        self.oboznachenie = 'Ш4'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для горизонтального угла
    def s5(self):  # шина гнутая внешняя большой гиб

        beta = (180 - int(self.C)) / 2

        if str(self.Nprov) in ['4', '3+1']:
            self.X = float(float(self.os[0]) - float(self.R_sh) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
            self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
        else:       # 3-х проводной
            self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5 * (math.tan(math.radians(beta))))
            self.Y = float(float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5 * (math.tan(math.radians(beta))))

        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш5'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s6(self):  # шина гнутая внешняя малый гиб

        beta = (180 - int(self.C)) / 2

        self.X = float(float(self.os[0]) - float(self.R_sh) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш6'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s7(self):  # шина гнутая внутренняя малый гиб

        beta = (180 - int(self.C)) / 2

        self.X = float(float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш7'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s8(self):  # шина гнутая внутренняя большой гиб (с припуском)

        beta = (180 - int(self.C)) / 2

        if str(self.Nprov) in ['4', '3+1']:
            self.X = float(float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
            self.Y = float(float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
        else:
            self.X = float(float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol) * 2 + int(self.S_sh) / 2) * (math.tan(math.radians(beta))))
            self.Y = float(float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol) * 2 + int(self.S_sh) / 2) * (math.tan(math.radians(beta))))

        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)

        # для 6мм. шины создаем припуск, для 8мм. припуска нет
        if self.S_sh in [6, '6']:
            self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)    # технологический допуск
            self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)    # технологический допуск
        else:
            self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
            self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)

        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш8'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для комбинированных секций

    def s9(self):  # Шина гнутая внешняя крайняя с одним выводом
        self.C = '-'
        if str(self.Nprov) in ['4', '3+1']:
            self.X = float(self.os[0]) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2 - float(self.H) / 2
            self.Y = float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2
        else:   # 3-х проводной
            self.X = float(self.os[0]) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5 - float(self.H) / 2
            self.Y = float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)

        self.oboznachenie = 'Ш9'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s10(self):  # Шина гнутая внешняя средняя  с одним выводом
        self.C = '-'

        self.X = float(float(self.os[0]) + float(self.S_sh_izol) + int(self.S_sh)) - float(self.H) / 2
        self.Y = float(float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш10'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s11(self):  # Шина гнутая внутреняя средняя с одним выводом
        self.C = '-'
        self.X = float(float(self.os[0]) - float(self.S_sh_izol)) - float(self.H) / 2
        self.Y = float(float(self.os[1]) - float(self.R_sh) - float(self.S_sh_izol))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш11'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s12(self):  # Шина гнутая, внутреняя, крайняя, стандартный выыод с одной стороны.
        self.C = '-'
        if str(self.Nprov) in ['4', '3+1']:
            self.X = float(float(self.os[0]) - float(self.S_sh_izol) * 3 - int(self.S_sh)) - float(self.H) / 2
            self.Y = float(float(self.os[1]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        else:
            X = float(float(self.os[0]) - float(self.S_sh_izol) * 2 - int(self.S_sh) / 2) - float(self.H) / 2
            Y = float(float(self.os[1]) - float(self.R_sh) - float(self.S_sh_izol) * 2 - int(self.S_sh) / 2)

        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш12'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для Z-образной

    def s13(self):  # Шина с двойным гибом внешняя крайняя
        self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш13'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s14(self):  # Шина с двойным гибом внешняя средняя
        self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш14'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s15(self):  # Шина с двойным гибом внутреняя средняя
        self.X = float(float(self.os[0]) - float(self.R_sh) - float(self.S_sh_izol))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш15'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s16(self):  # Шина с двойным гибом внутреняя крайняя
        self.X = float(float(self.os[0]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш16'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a


# шины для прямой с фланцем по новому чертежу СТП 01Ф
    def stp01f_01(self):
        razmery = [210, 100]

        self.A = '-'    # не должен быть меньше 100 мм.
        self.B = '-'
        self.C = '-'
        self.L = '-'
        self.L1 = 1
        #print(float(self.os), float(self.R_sh), self.L1Edge, self.L1_sh_b)
        self.oboznachenie = 'Ш17'
        self.naimenovanie = 'Шина (' + str(self.StpEdge) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        print(self.a)

    # для фланцев
    # для номинала от 630 до 2000 включительно
    def s17(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = '-'
        self.L1 = round(float(self.os) - float(self.R_sh) + self.L1Edge + self.L1_sh_b, 1)
        #print(float(self.os), float(self.R_sh), self.L1Edge, self.L1_sh_b)
        self.oboznachenie = 'Ш17'
        self.naimenovanie = 'Шина (' + str(self.StpEdge) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для номинала от 630 до 2000 включительно
    def s18(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = '-'
        self.L1 = round(float(self.os) - float(self.R_sh) + self.L1Centre + self.L1_sh_m, 1)
        #print(float(self.os), float(self.R_sh), self.L1Centre, self.L1_sh_m)
        self.oboznachenie = 'Ш18'
        self.naimenovanie = 'Шина (' + str(self.SptCentre) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для угф
    def s19(self):  # шина гнутая внешняя большой гиб
        self.C = '-'
        self.X = float(float(self.os[0]) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        self.Y = float(float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш19'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s20(self):  # шина гнутая внешняя малый гиб
        self.C = '-'
        self.X = float(float(self.os[0]) + float(self.S_sh_izol) + int(self.S_sh))
        self.Y = float(float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш20'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s21(self):  # шина гнутая внутренняя малый гиб
        self.C = '-'
        self.X = float(float(self.os[0]) - float(self.S_sh_izol))
        self.Y = float(float(self.os[1]) - float(self.R_sh) - float(self.S_sh_izol))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш21'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s22(self):  # шина гнутая внутренняя большой гиб
        self.C = '-'
        self.X = float(float(self.os[0]) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        self.Y = float(float(self.os[1]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш22'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для комбинированных и для CR
    def s23(self):  # шина гнутая внутренняя большой гиб
        beta = (180 - int(self.C)) / 2
        self.X = float(float(self.os[0]) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
        print(self.Y, (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш23'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s24(self):  # шина гнутая внешняя малый гиб
        beta = (180 - int(self.C)) / 2
        self.X = float(float(self.os[0]) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        print(self.Y, (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш24'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s25(self):  # шина гнутая внутренняя малый гиб
        beta = (180 - int(self.C)) / 2
        self.X = float(float(self.os[0]) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
        print(self.Y, float(self.S_sh_izol) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш25'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s26(self):  # шина гнутая внутренняя большой гиб
        beta = (180 - int(self.C)) / 2
        self.X = float(float(self.os[0]) - (float(self.S_sh_izol) * 3 - int(self.S_sh)) * (math.tan(math.radians(beta))))
        self.Y = float(float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
        #print(self.Y, (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.B = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш26'
        self.naimenovanie = 'Шина'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для Z-образной с фланцем

    def s27(self):  # шина гнутая внешняя большой гиб
        self.X = float(float(self.os[0]) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш27'
        self.naimenovanie = 'Шина (' + str(self.StpEdge) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s28(self):  # шина гнутая внешняя малый гиб
        self.X = float(float(self.os[0]) + float(self.S_sh_izol) + int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш28'
        self.naimenovanie = 'Шина (' + str(self.SptCentre) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s29(self):  # шина гнутая внутренняя малый гиб
        self.X = float(float(self.os[0]) - float(self.S_sh_izol))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Centre + 4, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш29'
        self.naimenovanie = 'Шина (' + str(self.SptCentre) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s30(self):  # шина гнутая внутренняя большой гиб
        self.X = float(float(self.os[0]) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1Edge + 4, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш30'
        self.naimenovanie = 'Шина (' + str(self.StpEdge) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для трансформаторной секции
    def s33(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = round(float(self.os) + float(self.S_krishka) + 1.5, 1)
        self.oboznachenie = 'Ш33'
        self.naimenovanie = 'Шина (Ш-ФБ)'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L)
        return self.a

    # для трансформаторной секции
    def s33i(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        self.L = round(float(self.os) + float(self.H) * 2 + float(self.S_krishka) + 7.5, 1)
        self.oboznachenie = 'Ш33'
        self.naimenovanie = 'Шина (Ш-ФБ)'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L)
        return self.a

    # шина с фланцем крайняя с минусом половины ширины шины. (Ш3 с плюсом)
    def s36(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'

        if self.seria in ['CR1']:
            self.L = round(float(self.os) + 210 - self.R_sh, 1)
            self.L1 = round(float(self.os) + self.L1Edge - self.R_sh, 1)
        else:
            if self.name in ['kpfuv', 'klfuv']:
                self.L = round(float(self.os) + float(self.H) / 2 + 210, 1)  # 210 это длина вывода фланца
                self.L1 = round(float(self.os) + float(self.H) / 2 + self.L1Edge, 1)
            else:
                self.L = round(float(self.os) - float(self.H) / 2 + 210, 1)  # 210 это длина вывода фланца
                self.L1 = round(float(self.os) - float(self.H) / 2 + self.L1Edge, 1)
        self.oboznachenie = 'Ш36'
        self.naimenovanie = 'Шина (' + str(self.StpEdge) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # шина с фланцем средняя с минусом половины ширины шины. (Ш4 с плюсом)
    def s37(self):
        self.A = '-'
        self.B = '-'
        self.C = '-'
        if self.seria in ['CR1']:
            self.L = round(float(self.os) + 210 - self.R_sh, 1)
            self.L1 = round(float(self.os) + self.L1Centre - self.R_sh, 1)
        else:
            if self.name in ['kpfuv', 'klfuv']:
                self.L = round(float(self.os) + float(self.H) / 2 + 210, 1)
                self.L1 = round(float(self.os) + float(self.H) / 2 + self.L1Centre, 1)
            else:
                self.L = round(float(self.os) - float(self.H) / 2 + 210, 1)
                self.L1 = round(float(self.os) - float(self.H) / 2 + self.L1Centre, 1)
        self.oboznachenie = 'Ш37'
        self.naimenovanie = 'Шина (' + str(self.SptCentre) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # шина с фланцем средняя с минусом половины ширины шины. (Ш4 с плюсом)
    def s38(self):
        self.C = '-'
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        if self.name in ['ув', 'uv']:
            self.X = float(self.os[0]) - float(self.R_sh) + float(self.S_sh) / 2
            self.Y = float(self.os[1]) - float(self.R_sh) + float(self.S_sh) / 2
        else:   # Для КП КЛ 3-х проводников
            if self.name in ['кп', 'кл']:
                self.X = float(self.os[0]) + int(self.S_sh) / 2 - float(self.H) / 2
                self.Y = float(self.os[1]) - float(self.R_sh) + int(self.S_sh) / 2
            else:    # если это уг
                self.X = float(self.os[0]) - float(self.R_sh) + int(self.S_sh) / 2
                self.Y = float(self.os[1]) - float(self.R_sh) + int(self.S_sh) / 2
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш38'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s41(self):

        beta = (180 - int(self.C)) / 2

        if self.os[2] == 1:
            if str(self.Nprov) in ['4', '3+1']:
                self.X = float(float(self.os[0]) - float(self.R_sh) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
                self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) * 3 + int(self.S_sh) * 2) * (math.tan(math.radians(beta))))
            else:       # 3-х проводной
                self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5 * (math.tan(math.radians(beta))))
                self.Y = float(float(self.os[1]) - float(self.R_sh) + float(self.S_sh_izol) * 2 + int(self.S_sh) * 1.5 * (math.tan(math.radians(beta))))
        elif self.os[2] == 2:
                self.X = float(float(self.os[0]) - float(self.R_sh) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
                self.Y = float(float(self.os[1]) - float(self.R_sh) + (float(self.S_sh_izol) + int(self.S_sh)) * (math.tan(math.radians(beta))))
        elif self.os[2] == 3:
                self.X = float(
                    float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
                self.Y = float(
                    float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol)) * (math.tan(math.radians(beta))))
        elif self.os[2] == 4:
                if str(self.Nprov) in ['4', '3+1']:
                    self.X = float(
                        float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
                    self.Y = float(
                        float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol) * 3 + int(self.S_sh)) * (math.tan(math.radians(beta))))
                else:
                    self.X = float(
                        float(self.os[0]) - float(self.R_sh) - (float(self.S_sh_izol) * 2 + int(self.S_sh) / 2) * (math.tan(math.radians(beta))))
                    self.Y = float(
                        float(self.os[1]) - float(self.R_sh) - (float(self.S_sh_izol) * 2 + int(self.S_sh) / 2) * (math.tan(math.radians(beta))))

        BD = self.razvertka_XY(beta * 2, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2, 1)
        self.B = round(float(self.Y) - BD / 2, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B), 1)
        self.oboznachenie = 'Ш41'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    # для Z-образной для CR1
    def s46_1(self):  # Шина внешняя крайняя
        self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш46'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s46_2(self):  # Шина внешняя средняя
        self.X = float(float(self.os[0]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) - float(self.S_sh_izol))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш46'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s46_3(self):  # Шина внутреняя средняя
        self.X = float(float(self.os[0]) - float(self.R_sh) - float(self.S_sh_izol))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) + int(self.S_sh))
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_m, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_m, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш46'
        self.naimenovanie = 'Шина (' + str(self.stp_L2) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def s46_4(self):  # Шина внутреняя крайняя
        self.X = float(float(self.os[0]) - float(self.R_sh) - float(self.S_sh_izol) * 3 - int(self.S_sh))
        self.Y = float(float(self.os[2]) - float(self.R_sh) + float(self.S_sh_izol) * 3 + int(self.S_sh) * 2)
        BD = self.razvertka_XY(90, self.R, self.Ka, self.S_sh)
        self.A = round(float(self.X) - BD / 2 + self.L1_sh_b, 1)
        self.B = round(float(self.os[1]) + int(self.S_sh) - BD, 1)
        self.C = round(float(self.Y) - BD / 2 + self.L1_sh_b, 1)
        self.L = '-'
        self.L1 = round(float(self.A) + float(self.B) + float(self.C), 1)
        self.oboznachenie = 'Ш46'
        self.naimenovanie = 'Шина (' + str(self.stp_L1) + ')'
        s = self.print_rezult()
        self.profil(['профиль', 'Шина ' + s, 'Ш_' + s, '90 90'], self.L1)
        return self.a

    def print_rezult(self):

        if self.naimenovanie in ['Крышка', 'Сухарь', 'Крышка средняя', 'Уголок_25х25х3', 'Крышка с выступом крашенная',
                                 'Втулка', 'Крышка стыка', 'Демпфер']:
            nominal = '-'
        elif self.nominal > 2500 and self.naimenovanie in ['Стенка', 'Стенка крашенная', 'Изолятор крайний',
                                                           'Изолятор средний', 'Направляющая']:

            if self.material in ['Al']:
                if self.naimenovanie in ['Изолятор крайний', 'Изолятор средний', 'Направляющая'] and self.nominal in [2501]:
                    nominal = 2500
                else:
                    nominalus = {3200: 1600, 2600: 2000, 4000: 2000, 5000: 2000, 6400: 2000, 3201: 2000, 2501: 1250}
                    nominal = nominalus[self.nominal]
            else:
                nominalus = {3200: 1250, 4000: 1600, 5000: 1600, 6400: 1600}
                nominal = nominalus[self.nominal]

            if self.naimenovanie in ['Стенка крашенная']:
                self.oboznachenie = str(self.oboznachenie) + '-01'

        elif re.findall(r'.', self.oboznachenie)[0] in ['Ш'] or self.oboznachenie in ['ТП']:

            if self.material in ['Al']:

                if self.nominal > 2500 and re.findall(r'\w*', self.naimenovanie)[0] in ['Шина']:
                    nominalus = {3200: 1600, 3201: 1600, 2600: 1250, 4000: 2000, 5000: 2500, 6400: 2500, 2501: 1250}
                    nominal = str(nominalus[self.nominal]) + ' (Алюм)'
                else:
                    nominal = str(self.nominal) + ' (Алюм)'

            else:  # self.material in ['Cu']:

                if self.nominal > 2500 and re.findall(r'\w*', self.naimenovanie)[0] in ['Шина', 'Пластина']:
                    nominalus = {3200: 1600, 4000: 2000, 5000: 2500, 6400: 2500}
                    nominal = str(nominalus[self.nominal]) + ' (Медь)'
                else:
                    nominal = str(self.nominal) + ' (Медь)'

        elif self.nominal < 3200 and self.naimenovanie in ['Стенка', 'Стенка крашенная', 'Стенка стыка',
                                                           'Пластина токопроводящая',
                                                           'Изолятор крайний', 'Изолятор средний',
                                                           'Направляющая'] and self.material in ['Cu']:
            nominalus = {400: 630, 630: 630, 800: 630, 1000: 800, 1250: 1000, 1600: 1250, 2000: 1600, 2500: 1600}
            nominal = nominalus[self.nominal]
        else:
            nominal = str(self.nominal)

        self.a = [self.seria, self.ip, self.material, nominal, self.Nprov, self.naimenovanie, self.oboznachenie, self.L,
                  self.L1, self.A, self.B, self.C]

        return nominal

    def razvertka_XY(self, fi, r, k, S):
        # Где s_izol – толщина изоляции, N – номер шины от центра осуи сверху вниз, Y2, X2 – полки, fi – внешний угол,
        # r – внутренний радиус гибки, k – коэффициент положения нейтральной линии (К-фактор), S – толщина металла.
        # OS - это внешняя граница гибки
        OS = 2 * (math.tan(math.radians(fi / 2))) * (int(r) + int(S))
        # BD - это вычет
        BD = OS - float(math.pi) * float(fi) / 180 * (int(r) + float(k) * int(S))
        print('Dano: ', fi, r, k, S, BD)
        return BD

    def profil(self, s, znachenie):
            i = 1

            while i <= int(self.kolN):
                self.spis_kompl['profil'].append([str(s[0]) + ';' + str(s[1]) + ';' + str(s[2]) + ';'
                                                  + str(s[3]) + ';' + str(znachenie) + ';' + str(self.name)])
                i += 1


class writing_to_exl():
    def __init__(self, atrib, etap, array, last_line, ved):
        self.font0 = xlwt.Font()
        self.style0 = xlwt.XFStyle()
        self.font1 = xlwt.Font()
        self.style1 = xlwt.XFStyle()
        self.font2 = xlwt.Font()
        self.style2 = xlwt.XFStyle()
        self.font3 = xlwt.Font()
        self.style3 = xlwt.XFStyle()
        self.oboznach = ["Прямая секция",
                         "Прямая секция с фланцем",
                         "Прямая секция с закрытым фланцем",
                         "Прямая распределительная секция с фикс. Выводом",
                         "Прямая распределительная секция с розеткой",
                         "Угловая горизонтальная секция",
                         "Угловая горизонтальная секция c фланцем",
                         "Угловая вертикальная секция",
                         "Угловая вертикальная секция с фланцем",
                         "Правая комбинированная секция",
                         "Правая комбинированная секция с фланцем уг",
                         "Правая комбинированная секция с фланцем ув",
                         "Левая комбинированная секция",
                         "Левая комбинированная секция с фланцем уг",
                         "Левая комбинированная секция с фланцем ув",
                         "z-образная вертикальная секция с фланцем",
                         "z-образная вертикальная секция",
                         "z-образная горизонтальная с фланцем",
                         "z-образная горизонтальная",
                         "Тройник вертикальный",
                         "Тройник вертикальный с фланцем",
                         "Тройник горизонтальный",
                         "Тройник горизонтальный с флацем",
                         "Секция компенсации",
                         "Секция перевода фаз",
                         "Секция перевода нейтрали",
                         "Блок отбора мощности",
                         "Блок отбора мощности фикированный",
                         "Трансформаторная секция вертикальная",
                         "Трансформаторная секция вертикальная с углом вертикальным",
                         "Трансформаторная секция вертикальная с углом горизонтальным",
                         "Трансформаторная секция вертикальная с тройником",
                         "Трансформаторная секция горизонтальная",
                         "Трансформаторная секция горизонтальная с углом вертикальным",
                         "Трансформаторная секция горизонтальная с углом горизонтальным",
                         "Трансформаторная секция горизонтальная с тройником",
                         "Концевая заглушка",
                         "Стыковочный блок",
                         "Огнепожарная проходка",
                         "Крепежная скоба",
                         "Пружинный подвес",
                         "Жесткий подвес",
                         "Адаптер",
                         "Крышка стыка"]
        self.oboznach_1 = ['Крышка СБ', 'Крышка с выступом СБ', 'Стенка СБ', 'Шина СБ', 'Направляющая', 'Сухарь',
                           'Фланец', 'Шина СБ (Зеркальная)']
        self.wb = openpyxl.Workbook()   # Создаем виртуальную книгу
        self.zakaz = atrib[0]           # номер заказа
        self.name_proizv = atrib[3]     # наименование произ. полщадки
        self.etap = etap                # номер этапа
        self.last_line = last_line      # номер расчет, данные о компьютере.
        self.slovar = array
        self.ved = ved

    def setting_exl(self):
        """Настройки"""
        print('13. ЗАПИСЬ В EXLX')
        self.font0 = xlwt.Font()
        self.font0.name = 'Century Gothic'
        self.font0.colour_index = 0
        self.font0.bold = True
        self.font0.italic = True
        self.font0.underline = True

        self.style0 = xlwt.XFStyle()
        self.style0.font = self.font0

        self.font1 = xlwt.Font()
        self.font1.name = 'Century Gothic'
        self.font1.colour_index = 0

        self.style1 = xlwt.XFStyle()
        self.style1.font = self.font1

        self.font2 = xlwt.Font()
        self.font2.name = 'Century Gothic'
        self.font2.colour_index = 0
        self.font2.bold = True

        self.style2 = xlwt.XFStyle()
        self.style2.font = self.font2

        self.font3 = xlwt.Font()
        self.font3.name = 'Century Gothic'
        self.font3.colour_index = 0
        self.font3.colour_index.bit_length()
        self.font3.bold = True

        self.style3 = xlwt.XFStyle()
        self.style3.font = self.font3


        if self.ved == 'upakovka':
            print('СОЗДАНИЕ КОНТРОЛЬНОЙ ВЕДОМОСТИ')
            spis_dla_vozvrata = self.upakovka()
            #self.OTK()
            self.wb.remove_sheet(self.wb.get_sheet_by_name('Sheet'))
            name_out_file = 'Контрольная ведомость Заказ №' + str(self.zakaz) + '.xlsx'
            print('Сохранение в файл: ', name_out_file)
            self.wb.save(name_out_file)
            return [[1, name_out_file], spis_dla_vozvrata]
        else:
            self.Nach_smen()
            self.txt_tabl()
            #self.komlekt_ie()
            self.wb.remove_sheet(self.wb.get_sheet_by_name('Sheet'))
            name_out_file = 'Заказ №' + str(self.zakaz) + ' Этап №' + str(self.etap) + '.xlsx'
            print('Сохранение в файл: ', name_out_file)
            self.wb.save(name_out_file)
            return [0, name_out_file]

    def kolontitul(self, name_sheet):
        """колонтитулы"""
        # верхний левый колонтитул
        sheet = self.wb[name_sheet]
        if self.ved == 'upakovka':
            sheet.oddHeader.left.text = 'Заказ № ' + str(self.zakaz)
        else:
            sheet.oddHeader.left.text = 'Заказ № ' + str(self.zakaz) + '\nЭтап № ' + str(self.etap)
        sheet.oddHeader.left.size = 12
        sheet.oddHeader.left.font = "Century Gothic"

        # верхний центральный колонтитул
        sheet.oddHeader.center.text = name_sheet
        sheet.oddHeader.center.size = 20
        sheet.oddHeader.center.font = "Century Gothic"

        # верхний правый колонтитул
        now = datetime.datetime.today().strftime("%d %m %Y")

        if self.name_proizv in ['Солярис']:
            sheet.oddHeader.right.text = 'ООО «ПИК «СОЛЯРИС»\n' + str(now)
        else:
            sheet.oddHeader.right.text = 'ООО «Питон Кама»\n' + str(now)

        sheet.oddHeader.right.size = 12
        sheet.oddHeader.right.font = "Century Gothic"

        # нижний правый колонтитул
        now = datetime.datetime.today().strftime("%d %m %Y")
        sheet.oddFooter.right.text = str(self.last_line)
        sheet.oddFooter.right.size = 10
        sheet.oddFooter.right.font = "Century Gothic"

        if name_sheet in ['пила', 'гибка', 'фрезер', 'сверловка', 'напыление', 'сварка', 'зачистка',
                          'шлифовка', 'покраска', 'предсборка', 'сборка']:
            # нижний левый колонтитул
            sheet = self.wb[name_sheet]
            sheet.oddFooter.left.text = 'Время начала:____:____' + '\n' + 'Время завершения:____:____'
            sheet.oddFooter.left.size = 14
            sheet.oddFooter.left.font = "Century Gothic"

            # нижний центральный колонтитул
            sheet.oddFooter.center.text = 'ФИО исполнителя:____________'
            sheet.oddFooter.center.size = 14
            sheet.oddFooter.center.font = "Century Gothic"

    def isFlot(self, value):
        """проверяем является ли значение числом"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def Nach_smen(self):

        """модуль записывает в файл эксель данные для нач. смены и раб. мест."""

        print('создана страница для начальника смены')
        self.wb.create_sheet(title='Маршрутная карта', index=1)  # создаем первый лист
        sheet = self.wb['Маршрутная карта']
        sheet.sheet_properties.pageSetUpPr.fitToPage = True
        sheet.page_setup.fitToHeight = False
        self.kolontitul('Маршрутная карта')
        x = 1
        operation = ['05', '10', '15', '20', '25', '30', '35', '40', '45', '50', '55', '60']
        # записываем первую строку для ведомости нач. смены с раб. местами.
        perv_stroka = ['№', 'Серия', 'ip', 'Материал', 'In', 'Кол. пров.', 'Наименование', 'Обозначение',
                            'Разм.L', 'Разм.L1', 'Разм.A', 'Разм.B', 'Разм.C', 'Кол.',
                            'пила', 'гибка', 'фрезер', 'сверловка', 'напыление', 'сварка',
                            'зачистка', 'шлифовка', 'лаз.резка', 'покраска', 'предсборка', 'сборка_заливка']
        for i in perv_stroka:
            cell = sheet.cell(row=1, column=x)
            cell.font = Font(name='Century Gothic', bold=True, color='000000')
            cell.value = i
            x += 1

        print('созданы страницы для рабочих мест')
        rab_mesto = {'пила': 'O', 'гибка': 'P', 'фрезер': 'Q', 'сверловка': 'R', 'напыление': 'S', 'сварка': 'T',
                     'зачистка': 'U', 'шлифовка': 'V', 'лаз.резка': 'W', 'покраска': 'X', 'предсборка': 'Y',
                     'сборка_заливка': 'Z'}

        # Создаем новые страницы для раб. мест
        for s in rab_mesto:
            nomer_s = perv_stroka.index(s)  # находим порядковый номер для s
            self.wb.create_sheet(title=s, index=nomer_s)  # создаем лист
            sheet2 = self.wb[s]  # создаем новую страницу
            sheet2.sheet_properties.pageSetUpPr.fitToPage = True
            sheet2.page_setup.fitToHeight = False
            self.kolontitul(s)
            x = 1

            # записываем первую строку в новую страницу без рабочих мест
            for i in perv_stroka:

                if x <= 14:
                    cell = sheet2.cell(row=1, column=x)
                    cell.font = Font(name='Century Gothic', bold=True, color='000000')
                    cell.value = str(i)
                    x += 1
                else:
                    continue

        # начинаем заполнять ячейки для рабочих мест в ведомости начальников смен
        y = 2

        for i in self.slovar:
            x = 2

            # для обозначения секций жирным шрифтом с подчеркиванием для сборок
            if self.slovar[i]['Наименование'] in self.oboznach:
                self.slovar[i]['Обозначение'] = str(self.slovar[i]['Обозначение'])
                st = Font(name='Century Gothic', bold=True, color='000000')
            # для обозначения жирным шрифтом для обозначения подсборок
            elif self.slovar[i]['Наименование'] in self.oboznach_1:
                st = Font(name='Century Gothic', bold=True, italic=True, color='000000')
            # для обозначения деталей простым шрифтом
            else:
                st = Font(name='Century Gothic')

            # записываем номер строки в ведомость нач. смены.
            cell = sheet.cell(row=y, column=1)
            cell.font = st
            cell.value = i

            # начинаем вычислять какая строчка нам нужна для формулы значения
            nS_schet = 1                                        # номер счетчика

            for cell in self.wb['Маршрутная карта']['A']:     # перебираем столбец А в списке нач смен
                #print(cell.value)
                #print('i', i)
                if cell.value == i:                             # ищем нужную сточку
                    znchStr = nS_schet                          # присваиваем значение нужной строчки переменной
                nS_schet += 1

            for j in self.slovar[i]:
                if j in ['номер элемента', 'тип', 'стандарт', 'категория']:
                    continue    # пропускаем ненужные колонки
                cell = sheet.cell(row=y, column=x)
                cell.font = st

                if self.slovar[i][j] == '0' and j in rab_mesto:
                    cell.value = 'Х'
                elif self.slovar[i][j] in operation and j in rab_mesto:     # проверяем, есть ли номер операции в списке
                    cell.value = ''
                    stroka = [i, self.slovar[i]['Серия'], self.slovar[i]['ip'], self.slovar[i]['Материал'],
                              self.slovar[i]['In'], self.slovar[i]['Кол. пров.'],
                              self.slovar[i]['Наименование'],
                              self.slovar[i]['Обозначение'], self.slovar[i]['Разм.L'], self.slovar[i]['Разм.L1'],
                              self.slovar[i]['Разм.A'], self.slovar[i]['Разм.B'], self.slovar[i]['Разм.C'],
                              '''='Маршрутная карта'!N''' + str(znchStr) + '''-'Маршрутная карта'!'''
                              + rab_mesto[j] + str(znchStr)]

                    xxx = 1
                    yyy = self.wb[j].max_row + 1

                    for s in stroka:
                        cell2 = self.wb[j].cell(row=yyy, column=xxx)
                        cell2.font = Font(name='Century Gothic')
                        cell2.value = str(s)
                        xxx += 1
                else:
                    cell.value = self.slovar[i][j]
                x += 1
            y = y + 1

    def upakovka(self):
        print('УПАКОВКА ОТК')
        spis_dla_vozvrata = []
        name_sheet = 'Контрольная ведомость'
        self.wb.create_sheet(title=name_sheet, index=18)  # создаем первый лист
        w_rab_mesto = self.wb[name_sheet]  # создаем новую страницу
        w_rab_mesto.sheet_properties.pageSetUpPr.fitToPage = True
        w_rab_mesto.page_setup.fitToHeight = False
        self.kolontitul(name_sheet)

        # ves B
        vesEAl = {630: 7.6, 800: 8.8, 1000: 10.8, 1250: 13.2, 1600: 17.1, 2000: 20.3, 2500: 24.5, 3200: 32, 4000: 38.3,
                5000: 46.6, 6400: 71}
        vesECu = {800: 15.9, 1000: 17.8, 1250: 24.8, 1600: 31.8, 2000: 43.9, 2500: 57.1, 3200: 63.1, 4000: 87.2}
        vesStikAl = {630: 2, 800: 2.2, 1000: 2.6, 1250: 3.1, 1600: 4.4, 2000: 5.1, 2500: 5.17, 3200: 8.35}
        vesStikCu = {1000: 3.61, 1600: 5.53, 2500: 9.34, 3200: 9.36, 4000: 14.69}

        # записываем первую строку
        x = 1
        for i in ['№ п/п', 'Артикул', 'Серийный номер', 'Наименование', 'Размер, мм', 'Номер элемента',
                  'Собрал', 'Упаковал', 'Отметка ОТК', 'Место', 'Масса, кг.', 'Примечание']:
            cell = w_rab_mesto.cell(row=1, column=x)
            cell.font = Font(name='Century Gothic', bold=True, color='000000')
            cell.value = i
            x += 1

        y = 2   # счетчик строк
        x1 = 1  # номер строки
        serNom = 1

        for i in self.slovar:
            spis_dla_vozvrata_2 = []
            d = re.findall(r'\d+', self.slovar[i]['Размер, мм'])

            if self.slovar[i]['Обозначение'] in ['УВ', 'УГ', 'УВФ', 'УГФ', 'uv', 'ug', 'uvf', 'ugf']:
                dlina = int(d[0]) + int(d[1])
            elif self.slovar[i]['Обозначение'] in ['ЗВ', 'ЗГ', 'КП', 'КЛ', 'ЗВФ', 'ЗГФ', 'ТВ', 'ТГ',
                                                   'zb', 'zg', 'kp', 'kl', 'zvf', 'zgf', 'tv', 'tg']:
                dlina = int(d[0]) + int(d[1]) + int(d[2])
            elif self.slovar[i]['Обозначение'] in ['П', 'ПФ', 'ОМ', 'ОМФ', 'ТС', 'pt', 'pf', 'pr', 'prf', 'ts']:
                dlina = int(d[0])
            else:
                dlina = 0

            # Вес шинопровода
            sss = ['УВ', 'УГ', 'УВФ', 'УГФ', 'ЗВ', 'ЗГ', 'КП', 'КЛ', 'ЗВФ', 'ЗГФ', 'ТВ', 'ТГ', 'П', 'ПФ',
                   'ОМ', 'ОМФ', 'ТС', 'uv', 'ug', 'uvf', 'ugf', 'zv', 'zg', 'kp', 'kl', 'zvf', 'zgf', 'tv', 'tg',
                   'pt', 'pf', 'pr', 'prf']
            if self.slovar[i]['Серия'] == 'B' and self.slovar[i]['Обозначение'] in sss:

                if self.slovar[i]['Мат. Пров.'] == 'Al' and int(self.slovar[i]['Ном. ток, А']) in vesEAl:
                    ves = round(dlina * vesEAl[int(self.slovar[i]['Ном. ток, А'])] / 1000, 2)
                elif self.slovar[i]['Мат. Пров.'] == 'Cu' and int(self.slovar[i]['Ном. ток, А']) in vesECu:
                    ves = round(dlina * vesECu[int(self.slovar[i]['Ном. ток, А'])] / 1000, 2)
                else:
                    ves = '-'

            # Вес стыков
            elif self.slovar[i]['Серия'] == 'B' and self.slovar[i]['Обозначение'] in ['СБ', 'sb']:
                if self.slovar[i]['Мат. Пров.'] == 'Al' and int(self.slovar[i]['Ном. ток, А']) in vesStikAl:
                    ves = round(vesStikAl[int(self.slovar[i]['Ном. ток, А'])], 2)
                elif self.slovar[i]['Мат. Пров.'] == 'Cu' and int(self.slovar[i]['Ном. ток, А']) in vesStikCu:
                    ves = round(vesStikCu[int(self.slovar[i]['Ном. ток, А'])], 2)
                else:
                    ves = '-'
            else:
                ves = '-'

            #   1 stolbec № п/п
            cell = w_rab_mesto.cell(row=y, column=1)
            cell.font = Font(name='Century Gothic')
            cell.value = x1

            # 2 столбец Артикул
            cell = w_rab_mesto.cell(row=y, column=2)
            cell.font = Font(name='Century Gothic')
            value = str(self.slovar[i]['Серия']) + '-' + str(self.slovar[i]['IP']) + '-' + str(
                self.slovar[i]['Мат. Пров.']) + '-' + str(self.slovar[i]['Кол. Пров.']) + '-' + str(
                self.slovar[i]['Ном. ток, А']) + '-' + str(self.slovar[i]['Обозначение'] + str(self.slovar[i]['Тип']))
            cell.value = value
            spis_dla_vozvrata_2.append(value)      # для возвращяемого списка

            #   3 stolbec Серийный номер
            print('ssss', self.slovar[i]['Наименование'])
            if self.slovar[i]['Наименование'] in ['Крепежная скоба']:
            # if self.slovar[i]['Наименование'] in ['Крепежная скоба', 'Крышка стыка', 'Пружинный подвес',
            #                                       'Концевая заглушка']:
                value = ''
            else:
                value = str(re.findall(r'\d+', str(self.zakaz).lower())[0]) \
                        + '-' + str(re.findall(r'\d+', str(self.slovar[i]['Этап']).lower())[0]) \
                        + '-' + str("%03d" % serNom)
            cell = w_rab_mesto.cell(row=y, column=3)
            cell.font = Font(name='Century Gothic')
            cell.value = value
            serNom += 1
            spis_dla_vozvrata_2.append(value)      # для возвращаемого списка

            # 4 столбец Наименование
            cell = w_rab_mesto.cell(row=y, column=4)
            cell.font = Font(name='Century Gothic')
            cell.value = self.slovar[i]['Наименование']
            spis_dla_vozvrata_2.append(self.slovar[i]['Наименование'])      # для возвращяемого списка

            # 5 столбец Размер
            cell = w_rab_mesto.cell(row=y, column=5)
            cell.font = Font(name='Century Gothic')
            cell.value = self.slovar[i]['Размер, мм']
            spis_dla_vozvrata_2.append(self.slovar[i]['Размер, мм'])      # для возвращяемого списка

            # 6 столбец номер элемента
            cell = w_rab_mesto.cell(row=y, column=6)
            cell.font = Font(name='Century Gothic')
            cell.value = self.slovar[i]['Номер элемента']
            spis_dla_vozvrata_2.append(self.slovar[i]['Номер элемента'])      # для возвращяемого списка

            # 11 столбец масса
            cell = w_rab_mesto.cell(row=y, column=11)
            cell.font = Font(name='Century Gothic')

            if self.slovar[i]['Наименование'] in ['Крепежная скоба', 'Крышка стыка', 'Пружинный подвес']:
                print(self.slovar[i])
                cell.value = str(self.slovar[i]['Кол, шт']) + ' шт.'
                spis_dla_vozvrata_2.append(str(self.slovar[i]['Кол, шт']) + ' шт.')      # для возвращяемого списка
            else:
                cell.value = ves
                spis_dla_vozvrata_2.append(ves)      # для возвращяемого списка

            # 12 столбец примечание
            cell = w_rab_mesto.cell(row=y, column=12)
            cell.font = Font(name='Century Gothic')

            if self.slovar[i]['Обозначение'] in ['kz', 'op', 'ks', 'pp', 'gp', 'ad', 'ksb']:
                cell.value = str(self.slovar[i]['Примечание']) + str(self.slovar[i]['Кол, шт']) + ' шт.'
            else:
                cell.value = self.slovar[i]['Примечание']

            x1 += 1
            y += 1
            spis_dla_vozvrata.append(spis_dla_vozvrata_2)  # для возвращяемого списка

        return spis_dla_vozvrata

    def komlekt_ie(self):
        """записываем материалы"""
        print('Комплектующие')
        self.wb.create_sheet(title='Комплектующие', index=14)  # создаем первый лист
        sheet = self.wb['Комплектующие']
        self.kolontitul('Комплектующие')
        sorting('txt', 'комплектующие.txt', 'комплектующие ИТОГ.txt', 4, False, ';').addition()

        tr = open('комплектующие ИТОГ.txt', 'r')  # отркываем и читаем файл
        line = (tr.readline().rstrip())  # начинаем читать построчно
        y = 1

        while line:
            q = re.findall(r'[^;]+', line)  # создаем список из строки
            x = 1

            for i in q:
                st = Font(name='Century Gothic', color='000000')
                cell = sheet.cell(row=y, column=x)
                cell.font = st
                cell.value = i
                x = x + 1
            y = y + 1
            line = tr.readline()  # присваем значению line следующую строку

    def txt_tabl(self):
        """Выводим на печать таблицу и записываем ее в текстовый файл"""
        print('СОХРАНЕНИЕ ТАБЛИЦЫ')
        #tab_spis_det = open('Таблица заказ № ' + str(self.zakaz) + 'Этап № ' + str(self.etap) + '.txt', 'w')
        s = self.slovar

        for i in s:
            a =[]
            a.append(i)
            for j in self.slovar[i]:
                a.append(self.slovar[i][j])
            tab_q = '{0:<5}{1:<5}{2:<5}{3:<5}{4:<15}{5:<5}{6:<35}{7:<15}{8:<15}' \
                '{9:<15}{10:<10}{11:<10}{12:<10}{13:<10}{14:<10}{15:<10}'.format(a[0], a[1], a[2], a[3], a[4], a[5],
                                                                                a[6], a[7], a[8], a[9], a[10], a[11],
                                                                                a[12], a[13], a[14], a[15])
            print(tab_q)
            #tab_spis_det.write(str(tab_q) + '\n')
        #tab_spis_det.close()


class calc():
    def __init__(self, input_data, Proizv):
        print(input_data)
        self.a = {'Серия': input_data[0],
                  'ip': input_data[1],
                  'Материал': input_data[2],
                  'Кол. пров.': int(input_data[3]),
                  'In': input_data[4],
                  'Наименование': input_data[5],
                  'Обозначение': str(input_data[6]).lower(),
                  'тип': input_data[7],
                  'размер': input_data[8],
                  'Производство': str(Proizv),
                  'количество': int(input_data[9]),
                  'стандарт': 'стандарт'}

    def isFloat(self, value):
        """Проверяем, является ли значение числом"""
        try:
            float(value)
            return True
        except ValueError:
            return False

    def calc_nom(self):        # размер фланца

        if self.a['Серия'] in ['Е3', 'B']:
            self.a['толщина стенки'] = 20
            self.a['толщина изоляции'] = 0.5
            self.a['ширина крышки'] = 115
            self.a['толщина крышки'] = 29.5
            self.a['толщина крышки средней'] = 40
            self.a['расстояние от оси до шины'] = 18.5
            self.a['расстояние от оси до корпуса'] = 116
        elif self.a['Серия'] in ['CR1', 'CR', 'CRM']:
            self.a['толщина стенки'] = 25
            self.a['ширина крышки'] = 125
            self.a['толщина крышки'] = 33
            self.a['толщина крышки средней'] = 40
            self.a['расстояние от оси до шины'] = 17.5
            self.a['расстояние от оси до корпуса'] = 127.5
        elif self.a['Серия'] in ['CR2']:    # CR1 в корпусе
            self.a['толщина стенки'] = 25
            self.a['ширина крышки'] = 125
            self.a['толщина крышки'] = 33
            self.a['толщина крышки средней'] = 40
            self.a['расстояние от оси до шины'] = 17.5
            self.a['расстояние от оси до корпуса'] = 127.5


        spisok_oboznachenii = {"pt": "Прямая секция",
                               "pf": "Прямая секция с фланцем",
                               "pfk": "Прямая секция с закрытым фланцем",
                               "prf": "Прямая распределительная секция с фикс. Выводом",
                               "pr": "Прямая распределительная секция с розеткой",
                               "ug": "Угловая горизонтальная секция",
                               "ugf": "Угловая горизонтальная секция c фланцем",
                               "uv": "Угловая вертикальная секция",
                               "uvf": "Угловая вертикальная секция с фланцем",
                               "kp": "Правая комбинированная секция",
                               "kpfug": "Правая комбинированная секция с фланцем уг",
                               "kpfuv": "Правая комбинированная секция с фланцем ув",
                               "kl": "Левая комбинированная секция",
                               "klfug": "Левая комбинированная секция с фланцем уг",
                               "klfuv": "Левая комбинированная секция с фланцем ув",
                               "zvf": "z-образная вертикальная секция с фланцем",
                               "zv": "z-образная вертикальная секция",
                               "zgf": "z-образная горизонтальная с фланцем",
                               "zg": "z-образная горизонтальная",
                               "tv": "Тройник вертикальный",
                               "tvf": "Тройник вертикальный с фланцем",
                               "tg": "Тройник горизонтальный",
                               "tgf": "Тройник горизонтальный с флацем",
                               "sk": "Секция компенсации",
                               "spf": "Секция перевода фаз",
                               "pn": "Секция перевода нейтрали",
                               "om": "Блок отбора мощности",
                               "omf": "Блок отбора мощности фикированный",
                               "tsv": "Трансформаторная секция вертикальная",
                               "tsvuv": "Трансформаторная секция вертикальная с углом вертикальным",
                               "tsvug": "Трансформаторная секция вертикальная с углом горизонтальным",
                               "tsvt": "Трансформаторная секция вертикальная с тройником",
                               "tsg": "Трансформаторная секция горизонтальная",
                               "tsguv": "Трансформаторная секция горизонтальная с углом вертикальным",
                               "tsgug": "Трансформаторная секция горизонтальная с углом горизонтальным",
                               "tsgt": "Трансформаторная секция горизонтальная с тройником",
                               "kz": "Концевая заглушка",
                               "sb": "Стыковочный блок",
                               "op": "Огнепожарная проходка",
                               "ks": "Крепежная скоба",
                               "pp": "Пружинный подвес",
                               "gp": "Жесткий подвес",
                               "ad": "Адаптер",
                               "ksb": "Крышка стыка",
                               "sux": "Сухарь",
                               "n": "Направляющая",
                               "fl": "Фланец",
                               "ops": "Опалубка для стыка",
                               "п": "Прямая секция",
                               "пф": "Прямая секция с фланцем",
                               "пфк": "Прямая секция с закрытым фланцем",
                               "омф": "Прямая распределительная секция с фикс. Выводом",
                               "ом": "Прямая распределительная секция с розеткой",
                               "уг": "Угловая горизонтальная секция",
                               "угф": "Угловая горизонтальная секция c фланцем",
                               "ув": "Угловая вертикальная секция",
                               "увф": "Угловая вертикальная секция с фланцем",
                               "кп": "Правая комбинированная секция",
                               "кпфуг": "Правая комбинированная секция с фланцем уг",
                               "кпфув": "Правая комбинированная секция с фланцем ув",
                               "кл": "Левая комбинированная секция",
                               "клфуг": "Левая комбинированная секция с фланцем уг",
                               "клфув": "Левая комбинированная секция с фланцем ув",
                               "звф": "z-образная вертикальная секция с фланцем",
                               "зв": "z-образная вертикальная секция",
                               "згф": "z-образная горизонтальная с фланцем",
                               "зг": "z-образная горизонтальная",
                               "тв": "Тройник вертикальный",
                               "твф": "Тройник вертикальный с фланцем",
                               "тг": "Тройник горизонтальный",
                               "тгф": "Тройник горизонтальный с флацем",
                               "ск": "Секция компенсации",
                               "спф": "Секция перевода фаз",
                               "спн": "Секция перевода нейтрали",
                               "бом": "Блок отбора мощности",
                               "бомф": "Блок отбора мощности фикированный",
                               "тсв": "Трансформаторная секция вертикальная",
                               "тсвув": "Трансформаторная секция вертикальная с углом вертикальным",
                               "тсвуг": "Трансформаторная секция вертикальная с углом горизонтальным",
                               "тсвт": "Трансформаторная секция вертикальная с тройником",
                               "тсг": "Трансформаторная секция горизонтальная",
                               "тсгув": "Трансформаторная секция горизонтальная с углом вертикальным",
                               "тсгуг": "Трансформаторная секция горизонтальная с углом горизонтальным",
                               "тсгт": "Трансформаторная секция горизонтальная с тройником",
                               "кз": "Концевая заглушка",
                               "сб": "Стыковочный блок",
                               "оп": "Огнепожарная проходка",
                               "пп": "Пружинный подвес",
                               "жпп": "Жесткий подвес",
                               "ад": "Адаптер",
                               "кс": "Крепежная скоба",
                               "ксб": "Крышка стыка"
                               }

        if self.isFloat(self.a['In']):
            self.a['In'] = int(self.a['In'])
        else:
            self.a['In'] = 0

        if self.a['тип'] == 'None':
            self.a['тип'] = ''

        if self.a['размер'] == 'None':
            self.a['размер'] = ''


        if self.a['Обозначение'] in spisok_oboznachenii:
            print(self.a['Обозначение'])

            if self.a['Наименование'] == spisok_oboznachenii[self.a['Обозначение']]:

                if self.a['Наименование'] in ["Крышка стыка", "Крепежная скоба"]:
                    self.a['In'] = 630

                print('все верно!')

            else:
                print('ошибка в Наименовании. Исправили на ', spisok_oboznachenii[self.a['Обозначение']])
                self.a['Наименование'] = spisok_oboznachenii[self.a['Обозначение']]

        else:
            print('ошибка в обозначении')
            self.a['стандарт'] = 'нестандарт'

        if self.a['Материал'] in ['а', 'А', 'a', 'A', 'Al', 'AL']:
            self.a['Материал'] = 'Al'
            self.a['K'] = 0.4
            #self.a['R'] = 10

            if self.a['Серия'] in ['Е3', 'B']:
                rS = {250: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      400: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      630: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      800: {'ширина шины': 55, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1000: {'ширина шины': 80, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1250: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1600: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2000: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2500: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 1,
                             'межфазное расстояние фланца': 130, 'количество втулок': 2},
                      2501: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      3200: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      4000: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      5000: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      6400: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 3,
                             'межфазное расстояние фланца': 130, 'количество втулок': 6}}

            elif self.a['Серия'] in ['CR1', 'CR', 'CRM', 'CR2']:
                rS = {250: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      400: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      630: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      800: {'ширина шины': 55, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1000: {'ширина шины': 80, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1250: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1600: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      1601: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2000: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2500: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 1,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      3200: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      4000: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      5000: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      6400: {'ширина шины': 200, 'толщина шины': 8, 'количество этажей': 3,
                             'межфазное расстояние фланца': 130, 'количество втулок': 6}}

                if self.a['In'] in [5000, 6400]:
                    self.a['толщина изоляции'] = 11.5 / 2
                else:
                    self.a['толщина изоляции'] = 9.5 / 2

        elif self.a['Материал'] in ['м', 'М', 'm', 'M', 'Cu', 'CU']:
            self.a['Материал'] = 'Cu'
            self.a['K'] = 0.34
            #self.a['R'] = 7

            if self.a['Серия'] in ['Е3', 'B']:
                rS = {630: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      800: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1000: {'ширина шины': 55, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1250: {'ширина шины': 80, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1600: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      2000: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2500: {'ширина шины': 160, 'толщина шины': 8, 'количество этажей': 1,
                             'межфазное расстояние фланца': 130, 'количество втулок': 2},
                      2502: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 130, 'количество втулок': 2},
                      2501: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      3200: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      4000: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      5000: {'ширина шины': 160, 'толщина шины': 8, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      5002: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      6400: {'ширина шины': 160, 'толщина шины': 8, 'количество этажей': 3,
                             'межфазное расстояние фланца': 130, 'количество втулок': 6},
                      6402: {'ширина шины': 200, 'толщина шины': 6, 'количество этажей': 3,
                             'межфазное расстояние фланца': 130, 'количество втулок': 6}}

            if self.a['Серия'] in ['CR1', 'CR', 'CRM', 'CR2']:
                rS = {250: {'ширина шины': 30, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      400: {'ширина шины': 30, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      630: {'ширина шины': 30, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      800: {'ширина шины': 40, 'толщина шины': 6, 'количество этажей': 1,
                            'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1000: {'ширина шины': 55, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1250: {'ширина шины': 80, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 1},
                      1600: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2000: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 1,
                             'межфазное расстояние фланца': 100, 'количество втулок': 2},
                      2500: {'ширина шины': 80, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      3200: {'ширина шины': 110, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      4000: {'ширина шины': 160, 'толщина шины': 6, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      5000: {'ширина шины': 160, 'толщина шины': 8, 'количество этажей': 2,
                             'межфазное расстояние фланца': 130, 'количество втулок': 4},
                      6400: {'ширина шины': 160, 'толщина шины': 8, 'количество этажей': 3,
                             'межфазное расстояние фланца': 130, 'количество втулок': 6}}

                if self.a['In'] in [5000, 6400]:
                    self.a['толщина изоляции'] = 11.5 / 2
                else:
                    self.a['толщина изоляции'] = 9.5 / 2

        else:
            print('Неверно указан Материал ', self.a['Материал'])
            self.a['стандарт'] = 'нестандарт'

        print(self.a['In'])
        if int(self.a['In']) not in rS:
            print("Не указан номинальный ток")
            self.a['стандарт'] = 'нестандарт'
            s = rS[630]
        else:
            s = rS[int(self.a['In'])]

        for i in s:
            self.a[i] = s[i]

        # Нормализация материала
        material = str(self.a.get('Материал', '')).lower()
        material_key = None
        if material in {'al', 'ал', 'AL', 'Al'}:
            material_key = 'al'
        elif material in {'cu', 'ме', 'м', 'CU', 'Cu'}:
            material_key = 'cu'

        if not material_key:
            self.a['стандарт'] = 'нестандарт'
            return

        # Алюминий 6мм
        if material_key == 'al' and self.a['толщина шины'] == 6: self.a['R'] = 14
        # Алюминий 8мм
        elif material_key == 'al' and self.a['толщина шины'] == 8: self.a['R'] = 15
        # Медь 6мм
        elif material_key == 'cu' and self.a['толщина шины'] == 6: self.a['R'] = 11
        # Медь 8мм
        elif material_key == 'cu' and self.a['толщина шины'] == 8: self.a['R'] = 12
        else:
            print(self.a['Производство'], self.a['Материал'], self.a['толщина шины'])

        self.a['ширина стенки'] = int(self.a['ширина шины']) + 2

        # размер между этажами
        if self.a['количество этажей'] == 2:
            self.a['разница между этажами'] = self.a['ширина шины'] / 2 + 3
        elif self.a['количество этажей'] == 3:
            self.a['разница между этажами'] = self.a['ширина шины'] + 6
        else:
            self.a['разница между этажами'] = 0


        # перечисляем стп для разных выводов
        if self.a['Обозначение'] in ['pf', 'pfk', 'ugf', 'uvf', 'zgf', 'zvf', 'kpuvf', 'kpugf', 'kluvf', 'klugf'] \
                and len(re.split(r'[*+-]', self.a['размер'])) > 1:

            if self.a['Обозначение'] in ['pf', 'pfk']:
                razmer = str(re.split(r'[*+-]', self.a['размер'])[1])
            elif self.a['Обозначение'] in ['ugf', 'uvf']:
                razmer = str(re.split(r'[*+-]', self.a['размер'])[2])
            else:
                razmer = str(re.split(r'[*+-]', self.a['размер'])[3])

            if razmer == '130':
                print("Нестандартная секция!\nМеняем межфазное расстояние на 130 мм.")
                self.a['межфазное расстояние фланца'] = '130'
            elif razmer == '100':
                print("Нестандартная секция!\nМеняем межфазное расстояние на 100 мм.")
                self.a['межфазное расстояние фланца'] = '100'
        else:
            self.a['фланец край'] = 0
            self.a['фланец центр'] = 0
            self.a['СТП край'] = ''
            self.a['СТП центр'] = ''

        # 3 проводника
        if str(self.a['Кол. пров.']) in ['3']:
            self.a['количество токопроводящих пластин'] = 6
            self.a['количество демпферов'] = 3
            self.a['количество средних изоляторов'] = 2
            self.a['длина вывода фланца'] = 210

            # 130 mm bus-6 mm    3200/4000А
            if str(self.a['межфазное расстояние фланца']) == '130' and self.a['толщина шины'] == 6:
                self.a['СТП край'] = 'СТП 035'                          # край
                self.a['СТП центр'] = ' '                               # центр (прямая)
                self.a['фланец край'] = 328.2                           # край
                self.a['фланец центр'] = self.a['длина вывода фланца']  # центр (прямая)
            # 100 mm bus-8 mm 2500/5000/6400A
            elif str(self.a['межфазное расстояние фланца']) == '100' and self.a['толщина шины'] == 8:
                self.a['СТП край'] = 'СТП 037'                          # край
                self.a['СТП центр'] = '???'                             # центр (прямая)
                self.a['фланец край'] = 269.6                           # край
                self.a['фланец центр'] = self.a['длина вывода фланца']  # центр (прямая)
            else:
                self.a['СТП край'] = '???'                              # край 100 mm bus-6 mm
                self.a['СТП центр'] = ' '                               # центр (прямая)
                self.a['фланец край'] = 289                             # край
                self.a['фланец центр'] = self.a['длина вывода фланца']  # центр (прямая)

            # bus-8 mm СТП 036
            if self.a['толщина шины'] == 8:
                self.a['большой гиб'] = 1.9                             # большой гиб
                self.a['малый гиб'] = 0                                 # малый гиб (прямая)
                self.a['СТП край вывод'] = 'СТП 036'
                self.a['СТП центр вывод'] = ''
                self.a['толщина пакета'] = 30
            # bus-6 mm СТП 034
            else:
                self.a['большой гиб'] = 1.1                             # большой гиб
                self.a['малый гиб'] = 0.5                                 # малый гиб (прямая)
                self.a['СТП край вывод'] = 'СТП 034'
                self.a['СТП центр вывод'] = ''
                self.a['толщина пакета'] = 22

        if str(self.a.get('Кол. пров.', '')) == '4':
            # Общие параметры для 4 проводников
            self.a.update({
                'количество токопроводящих пластин': 8,
                'количество демпферов': 4,
                'количество средних изоляторов': 3,
                'длина вывода фланца': 210,
            })


            # Проверка межфазного расстояния
            try:
                phase_dist = int(self.a['межфазное расстояние фланца'])
            except (ValueError, TypeError):
                self.a['стандарт'] = 'нестандарт'
                return

            if phase_dist not in (100, 130):
                self.a['стандарт'] = 'нестандарт'
                return

            # Проверка толщины шины
            thickness = self.a.get('толщина шины')
            if thickness not in (6, 8):
                self.a['стандарт'] = 'нестандарт'
                return

            # Конфигурации фланцев
            CONFIG = {
                    'al': {
                        130: {
                            6: (241.4, 379.8, 'СТП 066 Ф-01', 'СТП 066 Ф-02'),
                            8: (240.2, 376.0, 'СТП 066 Ф-05', 'СТП 066 Ф-06')
                        },
                        100: {
                            6: (232.8, 334.8, 'СТП 066 Ф-03', 'СТП 066 Ф-04'),
                            8: (231.6, 329.8, 'СТП 066 Ф-07', 'СТП 066 Ф-08')
                        }
                    },
                    'cu': {
                        130: {
                            6: (240.6, 378.5, 'СТП 066 Ф-11', 'СТП 066 Ф-12'),
                            8: (239, 373, 'СТП 066 Ф-15', 'СТП 066 Ф-16')
                        },
                        100: {
                            6: (231.9, 333.5, 'СТП 066 Ф-13', 'СТП 066 Ф-14'),
                            8: (230.4, 328, 'СТП 066 Ф-17', 'СТП 066 Ф-18')
                        }
                    }
                }


            # Поиск значений в конфиге
            flange_values = CONFIG.get(material_key, {}).get(phase_dist, {}).get(thickness)
            if flange_values:
                self.a['фланец центр'], self.a['фланец край'], self.a['СТП центр'], self.a['СТП край'] = flange_values
            else:
                self.a['стандарт'] = 'нестандарт'


            # bus-8 mm. Стандартный вывод шинопровода.
            if self.a['толщина шины'] == 8:
                self.a['большой гиб'] = 3.7  # большой гиб
                self.a['малый гиб'] = 0.4  # малый гиб (прямая)
                self.a['СТП край вывод'] = 'СТП 014'
                self.a['СТП центр вывод'] = 'СТП 015'
                self.a['толщина пакета'] = 38
            # bus-6 mm
            else:
                self.a['большой гиб'] = 2.5  # большой гиб
                self.a['малый гиб'] = 0.2  # малый гиб (прямая)
                self.a['СТП край вывод'] = 'СТП 05'
                self.a['СТП центр вывод'] = 'СТП 06'
                self.a['толщина пакета'] = 30

            if self.a['Серия'] in ['CR1', 'CR', 'CRM', 'CR2']:
                self.a['большой гиб'] = 0  # большой гиб
                self.a['малый гиб'] = 0  # малый гиб
        else:
            print('ошибка в количестве проводников')
            self.a['стандарт'] = 'нестандарт'

        return self.a


class to_pdf_reportlab:
    def __init__(self, s, nZak):
        self.register_fonts()
        self.pdf_files = self.obedin(s, nZak)

    def register_fonts(self):
        def register_font(font_name, font_file):
            font_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), 'fonts'))
            font_path = os.path.join(font_dir, font_file)
            if not os.path.exists(font_path):
                raise FileNotFoundError(f"Font file not found: {font_path}")
            pdfmetrics.registerFont(TTFont(font_name, font_path))

        register_font('GOTHIC', 'GOST.TTF')
        register_font('GOTHIC2', 'GOST type A Italic.ttf')
        register_font('GOTHIC3', 'GOST type A Bold.ttf')

    def obedin(self, s, nZak):
        name = "Наклейки Заказ №" + str(nZak) + ".pdf"
        name2 = 'Наклейки для стыков Заказ №' + str(nZak) + '.pdf'
        spis = []

        for i in s:
            spis.append(self.simple_table(i))

        merger = PdfMerger()
        merger2 = PdfMerger()

        for pdf in spis:
            if re.split(r'[-]', pdf)[0] in ['0']:
                merger.append(pdf)
            else:
                merger2.append(pdf)

        merger.write(name)
        merger2.write(name2)
        merger.close()
        merger2.close()

        for i in spis:
            os.remove(i)

        return [[2, name], [2, name2]]

    def simple_table(self, spis):
        def s_plus(s):
            s1 = []
            s2 = []
            while s:
                s1.append(s[0])
                s.pop(0)
                if len(s1) == 20:
                    s2.append(''.join(s1))
                    s1 = []
                    if len(s) <= 20:
                        s2.append(''.join(s))
            return s2

        if spis[2] in ['Стыковочный блок', 'стыковочный блок', 'Стыковочный моноблок']:
            name = '1-' + str(spis[1]) + '.pdf'
            c = canvas.Canvas(name, pagesize=(30, 20))
            c.setFont('GOTHIC3', 6)
            c.drawString(1.5, 7.5, spis[1])
        else:
            name = '0-' + str(spis[1]) + '.pdf'
            c = canvas.Canvas(name, pagesize=(100, 50))
            c.setLineWidth(.3)
            c.setFont('GOTHIC', 8)
            c.drawString(8, 36.5, spis[1])
            c.setFont('GOTHIC3', 4)
            c.drawString(7, 29, spis[0])
            c.drawString(10, 20, "Наименование")
            c.drawString(45, 20, 'Размер, мм.')
            c.drawString(75, 20, 'Масса, кг.')

            c.setFont('GOTHIC2', 4)
            s = list(spis[2])
            n = 12

            if len(s) > 20:
                ss = s_plus(s)
                for i in ss:
                    c.drawString(6, n, i)
                    n -= 3
            else:
                c.drawString(7, 12, spis[2])

            c.drawString(45, 12, spis[3])
            c.drawString(80, 12, str(spis[5]))
            c.setFont('GOTHIC3', 14)
            c.drawString(50, 28, spis[4])

            c.line(5, 45, 5, 5)
            c.line(5, 45, 95, 45)
            c.line(5, 5, 95, 5)
            c.line(95, 45, 95, 5)

            c.line(45, 45, 45, 25)
            c.line(5, 35, 45, 35)
            c.line(5, 25, 95, 25)

            c.line(40, 25, 40, 5)
            c.line(70, 25, 70, 5)
            c.line(5, 18, 95, 18)

        c.save()
        return name


class sorting():
    def __init__(self, tip, IN_name_file, OUT_name_file, N_stolb, zagolvok, razdelitel):
        '''     если мы хотим на выходе получить список а не записывать все в файл, то вместо имени выходного файла в\
            значение "OUT_name_file" нужно поставть "False".
                если мы хотим на входе загрузить список, а не читать из файла, то вместо имени входного файла в
            значение "IN_name_file" нужно поставить "False", а значение "tip" ставим "0"    '''

        self.tip = tip      # xl или txt или False если это просто список
        self.IN_name_file = IN_name_file
        self.OUT_name_file = OUT_name_file
        self.N_stolb = N_stolb  # столбец по которому идет сравнение
        self.zagolvok = zagolvok
        self.razdelitel = razdelitel
        self.q = []
        self.w = []

    def addition(self):
        """модуль сложения всех повторяющихся строк"""
        print('СЛОЖЕНИЕ ПОВТОРОВ')

        arrayApp = []
        array2 = []

        if self.tip == 'xl':  # если мы читаем из экселя
            wb = openpyxl.load_workbook(self.IN_name_file, data_only=True)
            sheet = wb.get_sheet_by_name('Спецификация')

            for row in sheet.rows:
                sel = []

                for cell in row:
                    sel.append(str(cell.value))

                arrayApp.append(sel)

            #print(arrayApp)

            if self.zagolvok == True:   # спрашиваем про заголовок
                del arrayApp[0]    # удаляем первую строку
            else:
                print('без заголовка')

            # удаляем ненужные слобцы
            for i in arrayApp:
                i[13] = int(i[13])
                del i[12]
                del i[0]

        elif self.tip == 'txt':     # если мы хотим прочитать файл в список и отсортировать его

            with open(self.IN_name_file) as file:
                array = [row.strip() for row in file]   # переписываем все строки в список ['первая строка', 'вторая строка...

                if self.zagolvok == True:
                    del array[0]    # удаляем первую строку
                else:
                    print('без заголовка')

            for i in array:

                if self.razdelitel == ';':
                    j = re.findall(r'[^;]+', i)
                elif self.razdelitel == ' ':
                    j = re.findall(r'[^\s]+', i)
                else:
                    j = re.findall(r'[^;\s]+', i)
                arrayApp.append(j)

            #print('Начальный список', arrayApp)

        else:       # если мы сразу запустили список а не читаем из файла
            arrayApp = self.IN_name_file

            if self.zagolvok == True:   # спрашиваем про заголовок
                del arrayApp[0]    # удаляем первую строку
            else:
                print('без заголовка')

        kol_str = len(arrayApp)    # записываем клличесвто элементов в списке

        for j in arrayApp:
            self.q = copy.copy(j)
            #print('список который сравниваем', self.q)
            qN = self.q[int(self.N_stolb) - 1]  # присваиваем значение количества строки которую нужно сравнить
            del self.q[int(self.N_stolb) - 1]   # удаляем значение количества строки которую нужно сравнить
            #print('Теперь у нас есть список', self.q)
            y = arrayApp.index(j) + 1  # нам нужна следующая строка
            sov = False                 # это счетчик совпадений

            # начинаем проверять на совпадение
            while y <= kol_str-1:   # начинаем сравнивать со следующей строкой
                i = 0
                self.w = copy.copy(arrayApp[y])     # строка с которой сравниваем это следующая строка
                #print('список с которым сравниваем', self.w)
                wN = self.w[int(self.N_stolb) - 1]  # присваиваем значение количества строки с которой нужно сравнить
                del self.w[int(self.N_stolb) - 1]   # удаляем значение количества строки с которой нужно сравнить
                #print('Теперь у нас есть список', self.w)

                if self.q == self.w:
                    i += 1
                    #print(qN)
                    qN = str(int(wN) + int(qN))  # складываем количество
                    #print('Складываем количество +' + wN + ' Итог=' + qN)
                    sov = True  # сообщаем что были совпадения
                    del arrayApp[y]
                    kol_str = len(arrayApp)
                else:
                    #print('элемент не похож')
                    y = y + 1

            # проверяем есть ли совпадения
            if sov == False:
                array2.append(j)
            else:
                self.q.insert(int(self.N_stolb)-1, qN)
                array2.append(self.q)

        if self.OUT_name_file == False:
            #print('Отсортированный список:', array2)
            return array2
        else:   # записываем результат в файл
            f = open(self.OUT_name_file, 'w')

            for i in array2:
                in_dat2 = (';'.join(i))
                f.write(in_dat2 + '\n')

            f.close()


class line_raskroi():

    def techno(array):
        '''модуль для создания маршрутной карты'''
        print('СОЗДАНИЕ МАРШРУТНОЙ КАРТЫ')
        print(array)
        spis = {'000 170': ["15", "30", "35"],
                '000 774-01': ["15", "60"],
                '000 774-02': ["15", "60"],
                'kl': ["30", "50", "55", "60"],
                'klfuv': ["50", "55", "60"],
                'kp': ["30", "50", "55", "60"],
                'kpfuv': ["50", "55", "60"],
                'ksm': ["55", "60"],
                'kcb': ["55", "60"],
                'ksb': ["55", "60"],
                'kz': ["30", "35", "40", "50", "55"],
                'om': ["55", "60"],
                'omf': ["55", "60"],
                'pf': ["55", "60"],
                'pfk': ["55", "60"],
                'pr': ["30", "50", "55", "60"],
                'pr1': ["30", "50", "55", "60"],
                'pr2': ["30", "50", "55", "60"],
                'pr3': ["30", "50", "55", "60"],
                'pr4': ["30", "50", "55", "60"],
                'pr5': ["30", "50", "55", "60"],
                'pr6': ["30", "50", "55", "60"],
                'pt': ["50", "60"],
                'sb': ["55", "60"],
                'sk': ["55", "60"],
                'Ск-Тр': ["35", "45", "55"],
                '000 125': ["55", "60"],
                '000 125-01': ["55", "60"],
                '000 125-02': ["55", "60"],
                '000 125-03': ["55", "60"],
                '000 777': ["55", "60"],
                '000 776': ["55", "60"],
                'ts': ["30", "50", "55", "60"],
                'ts1.1': ["30", "50", "55", "60"],
                'ts1.2': ["30", "50", "55", "60"],
                'ts1.3': ["30", "50", "55", "60"],
                'ts1.4': ["30", "50", "55", "60"],
                'ts2.1': ["30", "50", "55", "60"],
                'ts2.2': ["30", "50", "55", "60"],
                'ts2.3': ["30", "50", "55", "60"],
                'ts2.4': ["30", "50", "55", "60"],
                'ts3.1': ["30", "50", "55", "60"],
                'ts3.2': ["30", "50", "55", "60"],
                'ts3.3': ["30", "50", "55", "60"],
                'ts3.4': ["30", "50", "55", "60"],
                'ts4.1': ["30", "50", "55", "60"],
                'ts4.2': ["30", "50", "55", "60"],
                'ts4.3': ["30", "50", "55", "60"],
                'ts4.4': ["30", "50", "55", "60"],
                'ts5.1': ["30", "50", "55", "60"],
                'ts5.2': ["30", "50", "55", "60"],
                'ts5.3': ["30", "50", "55", "60"],
                'ts5.4': ["30", "50", "55", "60"],
                'ts6.1': ["30", "50", "55", "60"],
                'ts6.2': ["30", "50", "55", "60"],
                'ts6.3': ["30", "50", "55", "60"],
                'ts6.4': ["30", "50", "55", "60"],
                'ts7.1': ["30", "50", "55", "60"],
                'ts7.2': ["30", "50", "55", "60"],
                'ts7.3': ["30", "50", "55", "60"],
                'ts7.4': ["30", "50", "55", "60"],
                'ts8.1': ["30", "50", "55", "60"],
                'ts8.2': ["30", "50", "55", "60"],
                'ts8.3': ["30", "50", "55", "60"],
                'ts8.4': ["30", "50", "55", "60"],
                'tv': ["30", "50", "55", "60"],
                'ug': ["30", "50", "55", "60"],
                'ugf': ["30", "40", "50", "55", "60"],
                'uv': ["30", "50", "55", "60"],
                'uvf': ["30", "50", "55", "60"],
                'zg': ["30", "50", "55", "60"],
                'zgf': ["30", "50", "55", "60"],
                'zv': ["30", "50", "55", "60"],
                'zvf': ["30", "50", "55", "60"],
                'В': ["05", "15", "20"],
                'Д': ["55"],
                'ЗВ': ["30", "50", "55", "60"],
                'ЗВФ': ["30", "50", "55", "60"],
                'ЗГ': ["30", "50", "55", "60"],
                'ЗГФ': ["30", "50", "55", "60"],
                'З-ТС': ["15", "40", "50", "55"],
                'ИК': ["50", "55"],
                'ИС': ["50", "55"],
                'К': ["05", "15", "35", "55"],
                'К1': ["05", "15", "30"],
                'К11': ["05", "15", "30"],
                'К12': ["05", "15", "30"],
                'К13': ["05", "15", "30"],
                'К14': ["05", "15", "30"],
                'К15': ["05", "15", "30"],
                'К16': ["05", "15", "30"],
                'К18': ["05", "15", "30", "35", "55"],
                'К18-01': ["05", "15", "30", "35"],
                'К18-02': ["05", "15", "30", "35"],
                'К19': ["05", "15"],
                'К2': ["05", "15", "30"],
                'К20': ["05", "15"],
                'К21': ["05", "15"],
                'К3': ["05", "15", "30"],
                'К4': ["05", "15", "30"],
                'К5': ["05", "15", "30"],
                'К7': ["05", "15", "30"],
                'К8': ["05", "15", "30"],
                'К9': ["05", "15", "30"],
                'КВ': ["05", "15", "30", "40", "50", "55"],
                'КВ18': ["05", "15", "30", "35", "55"],
                'КВ18-01': ["05", "15", "30", "35", "55"],
                'КВ18-02': ["05", "15", "30", "35", "55"],
                'КВ20': ["05", "15"],
                'КВ21': ["05", "15"],
                'КВ-кр': ["05", "15", "55"],
                'КЗ': ["30", "35", "40", "50", "55"],
                'К-кр': ["05", "15", "55"],
                'КЛ': ["30", "50", "55", "60"],
                'КП': ["30", "50", "55", "60"],
                'КС': ["05", "15", "30"],
                'КС1': ["05", "15", "30"],
                'КС2': ["05", "15", "30"],
                'КС3': ["05", "15", "30"],
                'КС4': ["05", "15", "30"],
                'КС5': ["05", "15", "30"],
                'КС6': ["05", "15", "30"],
                'КС8': ["05", "15", "30"],
                'КС9': ["05", "15", "30"],
                'КСБ': ["55"],
                'К-СД1': ["30", "35", "40", "50", "55"],
                'К-СД10': ["30", "35", "40", "50", "55"],
                'К-СД11': ["30", "35", "40", "50", "55"],
                'КС-СД11': ["30", "35", "40", "50", "55"],
                'К-СД12': ["30", "35", "40", "50", "55"],
                'К-СД13': ["30", "35", "40", "50", "55"],
                'К-СД13ф': ["30", "35", "40", "50", "55"],
                'К-СД14': ["30", "35", "40", "50", "55"],
                'К-СД15': ["30", "35", "40", "50", "55"],
                'К-СД16': ["30", "35", "40", "50", "55"],
                'К-СД1-З': ["30", "35", "40", "50", "55"],
                'К-СД1-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'К-СД2': ["30", "35", "40", "50", "55"],
                'К-СД2ф': ["30", "35", "40", "50", "55"],
                'К-СД3': ["30", "35", "40", "50", "55"],
                'К-СД3ф': ["30", "35", "40", "50", "55"],
                'К-СД4': ["30", "35", "40", "50", "55"],
                'К-СД4Ф': ["30", "35", "40", "50", "55"],
                'К-СД5': ["30", "35", "40", "50", "55"],
                'К-СД5Ф': ["30", "35", "40", "50", "55"],
                'К-СД6': ["30", "35", "40", "50", "55"],
                'К-СД6-З': ["30", "35", "40", "50", "55"],
                'К-СД6-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'К-СД7': ["30", "35", "40", "50", "55"],
                'К-СД8': ["30", "35", "40", "50", "55"],
                'К-СД9': ["30", "35", "40", "50", "55"],
                'КС-кр': ["05", "15", "40", "55"],
                'ЛБ': ["15", "30"],
                'ЛВ': ["15", "30"],
                'ЛТ': ["15", "30"],
                'МЦ': ["15"],
                'Н': ["05", "15", "35"],
                'ОМ': ["55", "60"],
                'ОМ1.1': ["30", "50", "55", "60"],
                'ОМ1.2': ["30", "50", "55", "60"],
                'ОМ1.3': ["30", "50", "55", "60"],
                'ОМ1.4': ["30", "50", "55", "60"],
                'ОМ1.5': ["30", "50", "55", "60"],
                'ОМ1.6': ["30", "50", "55", "60"],
                'ОМ2.1': ["30", "50", "55", "60"],
                'ОМ2.2': ["30", "50", "55", "60"],
                'ОМ2.3': ["30", "50", "55", "60"],
                'ОМ2.4': ["30", "50", "55", "60"],
                'ОМ2.5': ["30", "50", "55", "60"],
                'ОМ2.6': ["30", "50", "55", "60"],
                'ОМФ': ["55", "60"],
                'П': ["50", "60"],
                'ПФ': ["55", "60"],
                'ПФК': ["55", "60"],
                'С': ["05", "35", "55"],
                'С-01': ["05", "15", "30"],
                'С1': ["05", "30"],
                'С1-01': ["05", "15", "30"],
                'С11': ["05", "30"],
                'С11-01': ["05", "15", "30"],
                'С12': ["05", "30"],
                'С12-01': ["05", "15", "30"],
                'С13': ["05", "30"],
                'С13-01': ["05", "15", "30"],
                'С14': ["05", "30"],
                'С14-01': ["05", "15", "30"],
                'С15': ["05", "30"],
                'С15-01': ["05", "15", "30"],
                'С16': ["05", "30"],
                'С16-01': ["05", "15", "30"],
                'С2': ["05", "30"],
                'С2-01': ["05", "15", "30"],
                'С3': ["05", "30"],
                'С3-01': ["05", "15", "30"],
                'С4': ["05", "30"],
                'С4-01': ["05", "15", "30"],
                'С5': ["05", "30"],
                'С5-01': ["05", "15", "30"],
                'С7': ["05", "30"],
                'С7-01': ["05", "15", "30"],
                'С8': ["05", "30"],
                'С8-01': ["05", "15", "30"],
                'С9': ["05", "30"],
                'С9-01': ["05", "15", "30"],
                'СБ': ["55", "60"],
                'Ск': ["05", "40", "50", "55"],
                'Ск-01': ["05", "15", "40", "50", "55"],
                'С-кр': ["05", "55"],
                'С-кр-01': ["05", "15", "55"],
                'СС': ["05", "15", "35"],
                'ЛВ/Н': ["45", "40", "50"],
                'КЛБ': ["45", "40", "50"],
                'ЛВБ': ["45", "40", "50"],
                'ЛБМ': ["45", "40", "50"],
                'km': ["45", "30", "35", "55"],
                'kb': ["45", "30", "35", "55"],
                '000 124': ["45", "30", "35", "55"],
                'С-СД1': ["30", "35", "40", "50", "55"],
                'С-СД10': ["30", "35", "40", "50", "55"],
                'С-СД11': ["30", "35", "40", "50", "55"],
                'С-СД12': ["30", "35", "40", "50", "55"],
                'С-СД13': ["30", "35", "40", "50", "55"],
                'С-СД14': ["30", "35", "40", "50", "55"],
                'С-СД15': ["30", "35", "40", "50", "55"],
                'С-СД16': ["30", "35", "40", "50", "55"],
                'С-СД2': ["30", "35", "40", "50", "55"],
                'С-СД3': ["30", "35", "40", "50", "55"],
                'С-СД3-3ф': ["30", "35", "40", "50", "55"],
                'С-СД3-З': ["30", "35", "40", "50", "55"],
                'С-СД3-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'С-СД3ф': ["30", "35", "40", "50", "55"],
                'С-СД4': ["30", "35", "40", "50", "55"],
                'С-СД4-З': ["30", "35", "40", "50", "55"],
                'С-СД4-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'С-СД4-ЗФ': ["30", "35", "40", "50", "55"],
                'С-СД4Ф': ["30", "35", "40", "50", "55"],
                'С-СД5': ["30", "35", "40", "50", "55"],
                'С-СД6': ["30", "35", "40", "50", "55"],
                'С-СД7': ["30", "35", "40", "50", "55"],
                'С-СД8': ["30", "35", "40", "50", "55"],
                'С-СД9': ["30", "35", "40", "50", "55"],
                'СТП 026 В': ["05", "25", "30"],
                'СТП 09 В': ["05", "25", "30"],
                'СУ': ["05", "15", "20"],
                'ТВ': ["30", "50", "55", "60"],
                'ТП': ["05", "10", "25", "35", "55"],
                'ТС': ["30", "50", "55", "60"],
                'ТС1.1': ["30", "50", "55", "60"],
                'ТС1.2': ["30", "50", "55", "60"],
                'ТС1.3': ["30", "50", "55", "60"],
                'ТС1.4': ["30", "50", "55", "60"],
                'ТС2.1': ["30", "50", "55", "60"],
                'ТС2.2': ["30", "50", "55", "60"],
                'ТС2.3': ["30", "50", "55", "60"],
                'ТС2.4': ["30", "50", "55", "60"],
                'ТС3.1': ["30", "50", "55", "60"],
                'ТС3.2': ["30", "50", "55", "60"],
                'ТС3.3': ["30", "50", "55", "60"],
                'ТС3.4': ["30", "50", "55", "60"],
                'ТС4.1': ["30", "50", "55", "60"],
                'ТС4.2': ["30", "50", "55", "60"],
                'ТС4.3': ["30", "50", "55", "60"],
                'ТС4.4': ["30", "50", "55", "60"],
                'ТС5.1': ["30", "50", "55", "60"],
                'ТС5.2': ["30", "50", "55", "60"],
                'ТС5.3': ["30", "50", "55", "60"],
                'ТС5.4': ["30", "50", "55", "60"],
                'ТС6.1': ["30", "50", "55", "60"],
                'ТС6.2': ["30", "50", "55", "60"],
                'ТС6.3': ["30", "50", "55", "60"],
                'ТС6.4': ["30", "50", "55", "60"],
                'ТС7.1': ["30", "50", "55", "60"],
                'ТС7.2': ["30", "50", "55", "60"],
                'ТС7.3': ["30", "50", "55", "60"],
                'ТС7.4': ["30", "50", "55", "60"],
                'ТС8.1': ["30", "50", "55", "60"],
                'ТС8.2': ["30", "50", "55", "60"],
                'ТС8.3': ["30", "50", "55", "60"],
                'ТС8.4': ["30", "50", "55", "60"],
                'ТЦ': ["15"],
                'У': ["05", "30"],
                'У2': ["05", "30"],
                'У1': ["05", "30"],
                'У2-З': ["05", "30"],
                'УВ': ["30", "50", "55", "60"],
                'УВФ': ["30", "50", "55", "60"],
                'УГ': ["30", "50", "55", "60"],
                'УГФ': ["30", "50", "55", "60"],
                '000 120': ["05", "10", "25", "40", "50", "55"],
                '000 119': ["05", "10", "25", "40", "50", "55"],
                '000 128': ["05", "10", "15", "25"],
                '000 108': ["45"],
                'Ш': ["05", "25", "30"],
                'Ш-01': ["05", "25", "40", "50", "55"],
                'Ш1': ["05", "10", "25", "40", "50", "55"],
                'Ш10': ["05", "10", "25", "30"],
                'Ш1-01': ["05", "10", "25", "30"],
                'Ш11': ["05", "10", "25", "30"],
                'Ш12': ["05", "10", "25", "30"],
                'Ш13': ["05", "10", "25", "40", "50", "55"],
                'Ш14': ["05", "10", "25", "40", "50", "55"],
                'Ш15': ["05", "10", "25", "40", "50", "55"],
                'Ш16': ["05", "10", "25", "40", "50", "55"],
                'Ш17': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш18': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш19': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш2': ["05", "10", "25", "40", "50", "55"],
                'Ш20': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш2-01': ["05", "10", "25", "30"],
                'Ш21': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш22': ["05", "10", "15", "25", "40", "50", "55"],
                'Ш23': ["05", "10", "25", "40", "50", "55"],
                'Ш24': ["05", "10", "25", "40", "50", "55"],
                'Ш25': ["05", "10", "25", "40", "50", "55"],
                'Ш26': ["05", "10", "25", "40", "50", "55"],
                'Ш27': ["05", "10", "25", "40", "50", "55"],
                'Ш28': ["05", "10", "25", "40", "50", "55"],
                'Ш29': ["05", "10", "25", "40", "50", "55"],
                'Ш3': ["05", "10", "25", "30"],
                'Ш30': ["05", "10", "25", "40", "50", "55"],
                'Ш33': ["05", "15", "25", "30"],
                'Ш36': ["05", "10", "15", "25", "30", "40", "50", "55"],
                'Ш37': ["05", "10", "15", "25", "30", "40", "50", "55"],
                'Ш38': ["05", "10", "25", "40", "50", "55"],
                'Ш46': ["05", "10", "25", "40", "50", "55"],
                'Ш4': ["05", "10", "25", "30"],
                'Ш41': ["10", "40", "50", "55"],
                'Ш5': ["05", "10", "25", "40", "50", "55"],
                'Ш6': ["05", "10", "25", "40", "50", "55"],
                'Ш7': ["05", "10", "25", "40", "50", "55"],
                'Ш8': ["05", "10", "25", "40", "50", "55"],
                'Ш9': ["05", "10", "25", "30"],
                'k_pe': ["30", "35", "40", "50", "55"],
                'Ш-СД1': ["30", "35", "40", "50", "55"],
                'Ш-СД1-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД10': ["30", "35", "40", "50", "55"],
                'Ш-СД11': ["30", "35", "40", "50", "55"],
                'Ш-СД12': ["30", "35", "40", "50", "55"],
                'Ш-СД13': ["30", "35", "40", "50", "55"],
                'Ш-СД14': ["30", "35", "40", "50", "55"],
                'Ш-СД15': ["30", "35", "40", "50", "55"],
                'Ш-СД15-З': ["30", "35", "40", "50", "55"],
                'Ш-СД15-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД16': ["30", "35", "40", "50", "55"],
                'Ш-СД16-З': ["30", "35", "40", "50", "55"],
                'Ш-СД16-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД17': ["30", "35", "40", "50", "55"],
                'Ш-СД17-З': ["30", "35", "40", "50", "55"],
                'Ш-СД17-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД18': ["30", "35", "40", "50", "55"],
                'Ш-СД18-З': ["30", "35", "40", "50", "55"],
                'Ш-СД18-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД19': ["30", "35", "40", "50", "55"],
                'Ш-СД19-З': ["30", "35", "40", "50", "55"],
                'Ш-СД19-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД1-З': ["30", "35", "40", "50", "55"],
                'Ш-СД2': ["30", "35", "40", "50", "55"],
                'Ш-СД2-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД20': ["30", "35", "40", "50", "55"],
                'Ш-СД20-З': ["30", "35", "40", "50", "55"],
                'Ш-СД20-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД21': ["30", "35", "40", "50", "55"],
                'Ш-СД21-З': ["30", "35", "40", "50", "55"],
                'Ш-СД21-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД22': ["30", "35", "40", "50", "55"],
                'Ш-СД22-З': ["30", "35", "40", "50", "55"],
                'Ш-СД22-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД25': ["30", "35", "40", "50", "55"],
                'Ш-СД26': ["30", "35", "40", "50", "55"],
                'Ш-СД27': ["30", "35", "40", "50", "55"],
                'Ш-СД28': ["30", "35", "40", "50", "55"],
                'Ш-СД29': ["30", "35", "40", "50", "55"],
                'Ш-СД2-З': ["30", "35", "40", "50", "55"],
                'Ш-СД3': ["30", "35", "40", "50", "55"],
                'Ш-СД3-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД30': ["30", "35", "40", "50", "55"],
                'Ш-СД31': ["30", "35", "40", "50", "55"],
                'Ш-СД32': ["30", "35", "40", "50", "55"],
                'Ш-СД33': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД33-01': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД33-02': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД33-03': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД33-04': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД33-05': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34-01': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34-02': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34-03': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34-04': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД34-05': ["10", "30", "35", "40", "50", "55"],
                'Ш-СД35': ["30", "35", "40", "50", "55"],
                'Ш-СД35-З': ["30", "35", "40", "50", "55"],
                'Ш-СД35-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД36': ["30", "35", "40", "50", "55"],
                'Ш-СД36-З': ["30", "35", "40", "50", "55"],
                'Ш-СД36-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД37': ["30", "35", "40", "50", "55"],
                'Ш-СД38': ["30", "35", "40", "50", "55"],
                'Ш-СД39': ["30", "35", "40", "50", "55"],
                'Ш-СД3-З': ["30", "35", "40", "50", "55"],
                'Ш-СД4': ["30", "35", "40", "50", "55"],
                'Ш-СД4-З (Зеркальная)': ["30", "35", "40", "50", "55"],
                'Ш-СД40': ["30", "35", "40", "50", "55"],
                'Ш-СД41': ["30", "35", "40", "50", "55"],
                'Ш-СД42': ["30", "35", "40", "50", "55"],
                'Ш-СД4-З': ["30", "35", "40", "50", "55"],
                'Ш-СД7': ["30", "35", "40", "50", "55"],
                'Ш-СД8': ["30", "35", "40", "50", "55"],
                'Ш-СД9': ["30", "35", "40", "50", "55"]
                }
        spisok_nazvanii = {'пила': '05', 'гибка': '10', 'фрезер': '15', 'сверловка': '20', 'напыление': '25',
                           'сварка': '30',
                           'зачистка': '35', 'шлифовка': '40', 'лаз.резка': '45', 'покраска': '50', 'предсборка': '55',
                           'сборка_заливка': '60'}

        for i in array:  # берем строку
            oper = spis[array[i]['Обозначение']]  # список с операциями [1, 0, 0...]

            for j in spisok_nazvanii:

                if spisok_nazvanii[j] in oper:
                    array[i][j] = spisok_nazvanii[j]
                else:
                    array[i][j] = '0'

        return array

    def material(name_file):
        spis = ['Токопроводящая пластина', 'Стенка стыка', 'Сухарь', 'Направляющая', 'Крышка', 'Крышка с выступом',
                'Уголок_25х25х3', 'Стенка', 'Крышка средняя', 'Шина']
        f = open('techno.txt', 'w')
        with open(name_file) as file:
            array = [row.strip() for row in
                     file]  # переписываем все строки в список ['первая строка', 'вторая строка', ...]
            array2 = []
            # print(array)
            kol_str = len(array)  # записываем клличесвто элементов в списке, оно же
            # print('всего строк ', kol_str)
        n_poz = 0
        for x in array:
            q = re.findall(r'[^;\s]+', x)  # список строки КОТОРУЮ НУЖНО СРАВНИТЬ
            # print('количество элементов в списке атрибутов строки ', len(q))
            w9 = q[-1]

            # начинаем проверять на совпадение
            # print('\nстрока которую сравниваем ', x)
            y = array.index(x) + 1  # нам нужна следующая строка
            sov = 0  # это счетчик совпадений
            while y <= kol_str - 1:  # начинаем сравнивать со следующей строкой
                line = array[y]  # строка с которой сравниваем это следующая строка
                w = re.findall(r'[^;\s]+', line)  # список строки С КОТОРОЙ СРАВНИВАЕМ
                if q[1] == w[1] and q[2] in spis and q[2] == w[2]:  # если значения строк совпадают, то
                    w9 = str(int(w9) + int(w[9]))  # складываем количество
                    sov = sov + 1  # сообщаем что были совпадения
                    # print('совпадение в', y, 'строке +', str(w[9]))
                    # print('строка которую удаляем', array[y])
                    del array[y]
                    kol_str = len(array)
                    # print('итого строк осталось: ', kol_str)
                    # print(y)
                    # print(line)
                else:
                    # print('нет совпадений в ', y, ' строке')
                    y = y + 1

            # проверяем есть ли совпадения
            if sov == 0:
                array2.append(x)
            else:
                in_spis = [q[0], q[1], q[2], w9]
                in_dat2 = (' '.join(in_spis))
                # print('Записываем в список ', in_dat2)
                array2.append(in_dat2)

        # записываем результат в файл
        # print(array2)
        for i in array2:
            # print(i)
            f = open('techno.txt', 'a')
            f.write(i + '\n')
            f.close()

    class komlektuyushie:
        '''модуль для создания ведомости комплектующих'''

        def __init__(self, data, length_OS, spis_kompl):
            self.data = data
            self.length_OS = length_OS
            self.spis_kompl = spis_kompl

        def print_data(self, data):

            for i in data:
                self.spis_kompl['st_izd'].append(
                    [str(i[0]) + ';' + str(i[1]) + ';' + str(i[2]) + ';' + str(i[3] * self.kol)])

        def standart_izdel(self):
            kol_bolt_M6x30 = {'630': 10, '800': 10, '1000': 10, '1250': 10, '1600': 10, '2000': 10, '2500': 12,
                              '2600': 14,
                              '3200': 14, '3201': 14, '4000': 14, '5000': 14, '6400': 14}

            if self.data['Обозначение'] in ['пф', 'угф', 'увф', 'звф', 'згф', 'тс', 'pf', 'pfk', 'ugf', 'uvf', 'zvf',
                                            'zgf']:
                self.kol = 1
                spis_st_izd = ['стандартный вывод', 'заклепка', 'флнцевый вывод']
                self.length_OS = self.length_OS - self.data['расстояние от оси до корпуса']
            elif self.data['Обозначение'] in ['п', 'уг', 'ув', 'зв', 'зг', 'кп', 'кл', 'ом', 'омф', 'pr', 'ug', 'uv',
                                              'zv',
                                              'zg', 'kp', 'kl', 'pr', 'prf']:
                self.kol = 2
                spis_st_izd = ['стандартный вывод', 'заклепка']
                self.length_OS = self.length_OS - self.data['расстояние от оси до корпуса'] * 2
            elif self.data['Обозначение'] in ['тв', 'тг', 'tv', 'tg']:
                self.kol = 3
                spis_st_izd = ['стандартный вывод', 'заклепка']
                self.length_OS = self.length_OS - self.data['расстояние от оси до корпуса'] * 3
            else:
                return False

            if self.length_OS <= 1000:
                kol_zakl = int(self.length_OS / 100) * 4
            elif self.length_OS > 1000 and self.length_OS < 1500:
                kol_zakl = int(self.length_OS / 150) * 4
            else:
                kol_zakl = int(self.length_OS / 200) * 4

            for i in spis_st_izd:
                if i == 'стандартный вывод':
                    s = [['стд. изд', 'Винт самонарезной М6х12 DIN7500C полуцилиндр гол. оцинк. TORX',
                          'Пи-Ст-В.сам.пцг.torx.М6х12', 12 * self.kol],
                         ['стд. изд', 'Винт самонарезной М6х12 DIN7500М потай гол. оцинк. TORX',
                          'Пи-Ст-В.сам.пг.torx.М6х12', 4 * self.kol]]
                elif i == 'флнцевый вывод':
                    s = [['стд. изд', 'Винт самонарезной М6х12 DIN7500C полуцилиндр гол. оцинк. TORX',
                          'Пи-Ст-В.сам.пцг.torx.М6х12', 8 * self.kol],
                         ['стд. изд', 'Винт самонарезной М6х12 DIN7500М потай гол. оцинк. TORX',
                          'Пи-Ст-В.сам.пг.torx.М6х12', 4 * self.kol],  # крепление фланца к шкафу и РЕ
                         ['стд. изд', 'Болт шестигранный М8х30 8.8 DIN933', 'Пи-Ст-Б.шг.М8х30',
                          kol_bolt_M6x30[str(self.data['In'])] * self.kol],  # крепление шин ушами
                         ['стд. изд', 'Болт шестигранный М8х65 8.8 DIN 933', 'Пи-Ст-Б.шг.М8х65', 2 * self.kol]]
                elif i == 'заклепка':
                    s = [['стд. изд', 'Заклепка вытяжная AFT 4,8х12 мм Алюм/Сталь станд.бортик (0,5/5,0zac) ZAC',
                          'Пи-Ст-Зк.выт.4.8х12', kol_zakl]]
                else:
                    s = [['', '', '', 0]]
                self.print_data(s)

    def linear_cutting(IN_name_file, OUT_name_file):
        '''Очередная сортировка хз зачем она нужна'''
        print('ЛИНЕЙНЫЙ РАСКРОЙ')
        open(OUT_name_file, 'w').close()
        with open(IN_name_file) as file:
            array = [row.strip() for row in
                     file]  # переписываем все строки в список ['первая строка', 'вторая строка', ...]
            array2 = []
            kol_str = len(array)  # записываем клличесвто элементов в списке, оно же
        for x in array:
            q = re.findall(r'[^;]+', x)  # список строки КОТОРУЮ НУЖНО СРАВНИТЬ
            # print('список который сравниваем', q)
            qN = q[-1]  # присваиваем значение количества строки которую нужно сравнить
            del q[-1]  # удаляем значение количества строки которую нужно сравнить
            # начинаем проверять на совпадение
            y = array.index(x) + 1  # нам нужна следующая строка
            sov = 0  # это счетчик совпадений
            while y <= kol_str - 1:  # начинаем сравнивать со следующей строкой
                i = 0
                s = True
                line = array[y]  # строка с которой сравниваем это следующая строка
                w = re.findall(r'[^;]+', line)  # список строки С КОТОРОЙ СРАВНИВАЕМ
                # print('список с которым сравниваем', w)
                wN = w[-1]
                del w[-1]
                if q == w:
                    print(q[i], w[i])
                    i += 1
                    s = True
                else:
                    s = False
                    # print('элемент не похож')
                if s == True:
                    qN = str(float(wN) + float(qN))  # складываем количество
                    sov = sov + 1  # сообщаем что были совпадения
                    del array[y]
                    kol_str = len(array)
                else:
                    y = y + 1
            # проверяем есть ли совпадения
            if sov == 0:
                array2.append(x)
            else:
                in_spis = q
                in_spis.append(qN)
                in_dat2 = (';'.join(in_spis))
                array2.append(in_dat2)

        # записываем результат в файл
        for i in array2:
            f = open(OUT_name_file, 'a')
            f.write(i + '\n')
            f.close()


class InOut:
    """модуль в котором мы обрабатывам входной файл из экселя для выдачи обработанных списков для начальников смен
    и для создания контрольной ведомости"""

    def __init__(self, fname, fdat):
        self.fname = fname  # имя файла который нужно открыть
        self.fdat = fdat    # форма которую нужно выдать, для контрольной ведомости 'k', для нач.смен 'n'


    def zapusk(self):

        if self.fdat == 'n':
            print('Ведомость нач. смен')
            return self.slog_povt(self.sklad_del(self.spisok_etapov(self.addition())))
        elif self.fdat == 'k':
            print('Контрольная ведомость')
            return self.slovar_raskritii(self.addition())
        elif self.fdat == 'o':
            print('Отметка нестандарта')
            return self.sortNest()
        else:
            return 'ошибка'

    def addition(self):
        """модуль создания из файла эксель раскрытого списка"""
        print('ЭКСЕЛЬ РАСКРЫТЫЙ СПИСКОК')

        array = []
        wb = openpyxl.load_workbook(self.fname, data_only=True)
        sheet = wb.get_sheet_by_name('Спецификация')
        rows = sheet.max_row
        cols = sheet.max_column

        for i in range(1, rows + 1):
            sel = []

            for j in range(1, cols + 1):
                if j <= 14:
                    cell = sheet.cell(row=i, column=j)
                    sel.append(str(cell.value))
                else:
                    continue

            array.append(sel)
        print(array)

        return array

    def spisok_etapov(self, spis):
        """модуль создания из списка словарь этапов"""
        print('СЛОВАРЬ ЭТАПОВ')
        array = []

        # перебираем строк и создаем полный список
        s = 0
        del spis[0]  # удаляем первую строку

        for i in spis:
            if i[0] in ('Итог', 'Итог:', 'Итого', 'Итого:', 'итог', 'итог:', 'итого', 'итого:', 'None'):
                print('удаляем строчку ', spis.index(i))
                del spis[spis.index(i)]
                continue
            else:
                print(i)
                kol_povt = int(i[11])
                i.pop(11)

            while kol_povt >= 1:
                array.append(i)
                kol_povt = kol_povt - 1

        # меняем формат значения этапа на цифренное
        for s in array:
            if s[12] in ('None', '', ' '):
                s[12] = 1
            else:
                s[12] = int(s[12])
        print(array)
        # создаем словарь этапов из полного списка
        array = sorted(array, key=lambda ji: ji[12])  # сортируем итоговый список по номеру этапа
        s = int(array[0][12])  # номер этапа
        di = {s: [array[0]]}  # создаем словарь с этапами
        del array[0]  # удаляем первую строчку, которую добавили в словарь

        for i in array:

            if int(i[12]) == s:
                di[s].append(i)
            else:
                s += 1
                di[s] = [i]

        return di

    def sklad_del(self, di):
        """модуль убирает все строчки связаннные со складом"""
        print('УДАЛЯЕМ СКЛАД')

        for i in di:
            s = []

            for j in di[i]:

                if j[11] != 'склад':
                    s.append(j)

            di[i] = s


        return di

    def slog_povt(self, di):
        """модуль складывает все повторяющиеся элементы списка"""
        print('СКЛАДЫВАЕМ ПОВТОРЫ')

        def del_n(di):
            # убираем ненужные атрибуты
            n = 0
            while len(di) > n:
                dj = copy.copy(di[n])
                del dj[0]
                s = 1

                while s <= 3:
                    del dj[9]
                    s += 1

                dj.append(1)
                di[n] = dj
                n += 1

            return di

        for i in di:
            di[i] = del_n(di[i])
            # начинаем сравнивать
            kol_str = len(di[i])  # записываем клличесвто элементов в списке
            array = []

            if kol_str == 1:
                print('no sum')
                continue
            else:
                for j in di[i]:
                    q = copy.copy(j)
                    #print('список который сравниваем', q)
                    qN = q[-1]  # присваиваем значение количества строки которую нужно сравнить
                    del q[-1]   # удаляем значение количества строки которую нужно сравнить
                    #print('Теперь у нас есть список', q)
                    y = di[i].index(j) + 1  # нам нужна следующая строка

                    # начинаем проверять на совпадение
                    while y <= kol_str-1:   # начинаем сравнивать со следующей строкой
                        ij = 0
                        w = copy.copy(di[i][y])     # строка с которой сравниваем это следующая строка
                        #print('список с которым сравниваем', w)
                        wN = w[-1]  # присваиваем значение количества строки с которой нужно сравнить
                        del w[-1]   # удаляем значение количества строки с которой нужно сравнить
                        #print('Теперь у нас есть список', w)

                        if q == w:
                            ij += 1
                            #print(qN)
                            qN = int(wN) + int(qN)  # складываем количество
                            #print('Складываем количество +', wN, ' Итог=', qN)
                            del di[i][y]
                            kol_str = len(di[i])
                        else:
                            #print('элемент не похож')
                            y = y + 1

                    q.insert(9, qN)
                    array.append(q)
                    #print(array)

                di[i].clear()
                di[i] = array
        return di

#
    def slovar_raskritii(self, array):
        """модуль для создания словаря из раскрытого списка"""
        print('РАСКРЫТЫЙ СЛОВАРЬ')

        def si(spis):
            # перебираем строк и создаем полный список
            array = []
            s = 0

            for i in spis:

                if s == 0:
                    i.pop(11)
                    s += 1
                    kol_povt = 1
                elif i[7] in ['kz', 'op', 'ks', 'pp', 'gp', 'ad', 'ksb']:
                    i.append(i[11])
                    i.pop(11)
                    s += 1
                    kol_povt = 1
                elif i[0] in ('Итог', 'Итог:', 'Итого', 'Итого:', 'итог', 'итог:', 'итого', 'итого:', 'None'):
                    print('удаляем сточку ',  spis.index(i))
                    del spis[spis.index(i)]
                    continue
                else:
                    print(i)
                    kol_povt = int(i[11])
                    i.pop(11)

                while kol_povt >= 1:
                    array.append(i)
                    kol_povt = kol_povt - 1
            return array

        n = 0
        s = {}
        array = si(array)

        for i in array:

            if i[12] in ('None', '', ' ', None):
                i[12] = 1
            if n == 0:
                n += 1
                continue
            else:
                nn = 0
                s[n] = {}

                if i[7] in ['kz', 'op', 'ks', 'pp', 'gp', 'ad', 'ksb']:
                    s[n]['Кол, шт'] = i[13]
                    del i[13]

                for j in i:

                    if j == 'None':
                        j = ''
                    s[n][array[0][nn]] = j
                    nn += 1

            n += 1

        return s

    def sortNest (self):
        """модуль для отметки нестандарта в контрольной ведомости"""
        print('СОРТРОВКА НЕСТАНДАРТА')
        s1 = self.fname[0]
        s2 = self.fname[1]
        print('s1', s1)
        print('s2', s2)

        for i in s1:
            f = [s1[i]['Серия'], s1[i]['ip'], s1[i]['Материал'], s1[i]['Кол. пров.'], s1[i]['In'],
                 s1[i]['Наименование'], s1[i]['Обозначение'], s1[i]['тип'], s1[i]['размер']]

            for i2 in s2:

                if s2[i2]['Ном. ток, А'] in ['', '-', '0', 0, ' ']:
                    s2[i2]['Ном. ток, А'] = 0
                print(s2[i2]['Этап'])
                if s2[i2]['Этап'] in ['None', '', ' ']:
                    s2[i2]['Этап'] = 1

                f2 = [s2[i2]['Серия'], s2[i2]['IP'], s2[i2]['Мат. Пров.'], s2[i2]['Кол. Пров.'],
                      s2[i2]['Ном. ток, А'], s2[i2]['Наименование'], s2[i2]['Обозначение'],
                      s2[i2]['Тип'], s2[i2]['Размер, мм']]

                if f == f2:
                    s2[i2]['Примечание'] = 'СИ'
                    s2[i2]['количество'] = s1[i]['количество']

        return s2


if __name__ == '__main__':  # Если мы запускаем файл напрямую, а не импортируем
    s = rashet('88 Сбербанк', 'D:/PycharmProjects/materials/пример.xlsx', 'Kama')
    #s = rashet(195, '/home/eva/PycharmProjects/materials/пример.xlsx', 'Solaris')
    #s = rashet(157, 'D:/PycharmProjects/materials/Технопарк доп заказ.xlsx')

    s.zapusk()