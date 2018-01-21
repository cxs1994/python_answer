# -*- coding: utf-8 -*-

# @Author  : Allen_Liang
# @Time    : 2018/1/14 15:38

from aip import AipOcr  
import requests
import json
import time
from PIL import Image
from PIL import ImageChops
import os
import matplotlib.pyplot as plt
import webbrowser
import urllib.parse
#命令行颜色包
from colorama import init,Fore
import random
#from pymongo import MongoClient
import sys

from common.config import Config

init()

# 百度OCR_api定义常量
# 输入你的API信息  
APP_ID = ''
API_KEY = ''
SECRET_KEY = ''
aipOcr = AipOcr(APP_ID, API_KEY, SECRET_KEY)  

# 定义参数变量  
options = {  
  'detect_direction': 'true',  
  'language_type': 'CHN_ENG',  
}  



class Answer:
    # 用adb从截图pull到计算机上
    def pull_screenshot(self):
        os.system('adb shell screencap -p /sdcard/screenshot.png')
        os.system('adb pull /sdcard/screenshot.png .')

    # 头脑王者图片切割
    def image_cut_tounao(self):
        # 全图
        img = Image.open("./screenshot.png")
        img.save('screenshot/' + self.now_time + '.png')
        # 问题区域
        question = img.crop((38, 386, 688, 580))
        question.save('question/' + self.now_time + '.png')
        # 选项区域
        choices = img.crop((38, 640, 688, 1126))
        choices.save('choices/' + self.now_time + '.png')

    # 读取问题图片
    def get_file_content(self, q_filePath):
        with open(q_filePath, 'rb') as fp:
            return fp.read()

    # OCR识别问题文字
    def question_words(self, q_filePath, options):
        # 调用通用文字识别接口
        result = aipOcr.basicGeneral(self.get_file_content(q_filePath), options)
        q_Result_s = ''
        words_list = []
        for word_s in result['words_result']:
            words_list.append(word_s['words'])
        q_Result_s = q_Result_s.join(words_list)
        return q_Result_s

    # 读取选项图片
    def get_file_content(self, c_filePath):
        with open(c_filePath, 'rb') as fp:
            return fp.read()

    # OCR识别问题文字
    def choices_words(self, c_filePath, options):
        # 调用通用文字识别接口
        result = aipOcr.basicGeneral(self.get_file_content(c_filePath), options)
        words_list = []
        for word_s in result['words_result']:
            words_list.append(word_s['words'])
        return words_list

    # 执行查文件
    def file_base(self, question, choices):
        f = open("questions.data", encoding='utf8')
        file_content = f.read()
        f.close()
        f = file_content.find(question)
        my_choices = ''
        if f != -1:
            my_choices_text = file_content[f:f + len(question) + 50]
            a = my_choices_text.find('{"a":"')
            if a != -1:
                b = my_choices_text.find('","ts":', a, a + 50)
                if b != -1:
                    my_choices = my_choices_text[a + 6:b]

        print('我的file题库查询结果: ', Fore.RED + my_choices + Fore.RESET)
        if my_choices:
            for i in range(len(choices)):
                if (choices[i] == my_choices):
                    self.oncheck(i)
            return True
        return False
        # 模糊查询关闭
        b = file_content.find(question.encode('utf8')[9:24].decode('utf8'))
        while b != -1:
            my_choices = file_content[b - 10:b + 20]
            print('我的file题库查询结果: ' + my_choices)
            return True
        for i in range(len(choices)):
            d = file_content.find(choices[i])
            while d != -1:
                my_choices = file_content[d - 20:d + 20]
                print('我的file题库查询结果: ' + my_choices)
                return True
        print('我的file题库无结果')
        return False

    # 网页分析统计
    def count_base(self, question, choices):
        req = requests.get(url='http://www.baidu.com/s', params={'wd': question})
        content = req.text
        counts = []
        dic = {}
        # print('———————————————————————————')
        if '不是' in question or '不能' in question or '不属于' in question or '不可以' in question or '不包括' in question:
            for i in range(len(choices)):
                counts.append(content.count(choices[i]))
                dic[choices[i]] = counts[i]
                print(choices[i] + " : " + str(counts[i]))
            if dic:
                if dic[max(dic, key=dic.get)] != dic[min(dic, key=dic.get)]:
                    print('请注意此题为否定题，建议选择：', Fore.RED + min(dic, key=dic.get) + Fore.RESET)
                    for i in range(len(choices)):
                        if (choices[i] == min(dic, key=dic.get)):
                            self.oncheck(i)
                    self.save_file(question, min(dic, key=dic.get))

        else:
            for i in range(len(choices)):
                counts.append(content.count(choices[i]))
                dic[choices[i]] = counts[i]
                print(choices[i] + " : " + str(counts[i]))
            if dic:
                if dic[max(dic, key=dic.get)] != 0:
                    print('请注意此题为肯定题，建议选择：', Fore.RED + max(dic, key=dic.get) + Fore.RESET)
                    for i in range(len(choices)):
                        if (choices[i] == max(dic, key=dic.get)):
                            self.oncheck(i)
                    self.save_file(question, max(dic, key=dic.get))

    # 问答写入文件
    def save_file(self, question, my_choices):
        f = open('questions.data', 'a', encoding='utf8')
        f.write('\n')
        f.write(question + '{"a":"' + my_choices + '","ts":' + self.now_time + '}')
        f.close()

    # 查询结果与选项进行比对，计算相似度，返回最相似值
    def check(self, my_choices, choices):
        max_ratio = 0  # 初始匹配度
        max_choices = ''  # 初始匹配值
        for i in range(len(choices)):
            num = len(choices[i] and my_choices)
            choices_len = len(choices[i])
            if (num == 0):  # 不匹配
                continue
            if (num == choices_len):  # 完全匹配时，返回完全匹配值
                return choices[i]
            if (choices_len / num > max_ratio):  # 非完全匹配时，返回最匹配值
                max_ratio = choices_len / num
                max_choices = choices[i]
            return max_choices

    # 点击
    def oncheck(self, i):
        print(i)
        # 点击选项配置
        config = Config
        config_options = config.get_config(config, 'options')
        press_time = int(random.uniform(200, 1000))
        xx = config_options[i]['x1']
        yy = config_options[i]['y1']
        x = int(random.uniform(xx - 50, xx + 50))
        y = int(random.uniform(yy - 10, yy + 10))  # 随机防 ban
        cmd = 'adb shell input swipe {x1} {y1} {x2} {y2} {duration}'.format(
            x1=x,
            y1=y,
            x2=x,
            y2=y,
            duration=press_time
        )
        print(cmd)
        os.system(cmd)

    # 验证是否有问题图片
    def compare_images(self):
        img = Image.open('choices/' + self.now_time + '.png')
        config = Config
        check_config = config.get_config(config, 'check')
        # check_img = img.crop((50, 0, 150, 600))
        check_img = img.crop((check_config['x1'], check_config['y1'], check_config['x2'], check_config['y2']))
        check_img.save('check_choices.png')
        check_choices = Image.open('check_choices.png')
        check = Image.open('check.png')
        diff = ImageChops.difference(check_choices, check)
        if diff.getbbox() is None:
            # 图片间没有任何不同则是问答图
            return True
        else:
            img.save('error/' + self.now_time + '.png')
            return False

    # 根据选择游戏执行
    def game_fun(self):
        while True:

            # 当前截屏时间
            self.now_time = time.strftime("%Y%m%d%H%M%S")

            # start = time.time()

            # 利用adb获取并pull到电脑
            self.pull_screenshot()
            # 图片切割
            self.image_cut_tounao()

            is_option_img = self.compare_images()
            if not is_option_img:
                print('+++++++++++++++++++++截图非题目选项+++++++++++++++++++++')
                continue

            q_filePath = "question/" + self.now_time + ".png"
            c_filePath = "choices/" + self.now_time + ".png"
            question = self.question_words(q_filePath,options)
            choices = self.choices_words(c_filePath,options)

            # 测试数据
            # question = '下列哪部作品不属于杜甫的「三别」？'
            # choices = ['无家别','新婚别','垂死别','生死别']
            # question = '第一届现代奥运会在哪个国家举行？'
            # choices = ['美国', '德国', '巴西', '希腊']
            #question = '中国古代女子体态以胖为美的是哪个朝代？'
            #choices = ['清朝','唐朝','宋朝','明朝']

            print('问题: ' + question)

            # 先查询本地资源文件
            file_res = self.file_base(question, choices)
            if (file_res):
                continue

            # 再查询本地数据库
            # mongo_res = mongo_base(question, choices)
            # if (mongo_res):
            # continue

            # 最后查不到就百度
            self.count_base(question, choices)

            # end = time.time()
            # print('+++++++++++++++++++++'+'程序用时：' + str(end - start) + '秒'+'+++++++++++++++++++++')

if __name__ == '__main__':
    init()

    answer = Answer()
    answer.game_fun()
    sys.exit()
    # 连接mongodb
    #conn = MongoClient('127.0.0.1', 27017)
    #db = conn.question
    #my_question = db.questionlist
    go = input('输入回车继续运行,输入 n 回车结束运行: ')
    if go == 'n':
        sys.exit()
    #这里原来是有多个选择的，不过我只玩头脑王者（image_cut_tounao）
    game_fun(image_cut_tounao)
