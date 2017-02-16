#!/usr/bin/env python
#coding:utf-8
from __future__ import unicode_literals
from __future__ import division

"""
Minimal Example
===============
Generating a square wordcloud from the US constitution using default arguments.
"""

import os
import sys
from os import path
from glob import glob
from time import time

import chardet
import re
import codecs   #codecs提供的open方法来指定打开的文件的语言编码，它会在读取的时候自动转换为内部unicode
import jieba    #分词包
import numpy as np   #numpy计算包
import pandas as pd   #数据分析包
import matplotlib.pyplot as plt

from wordcloud import WordCloud

SCRIPTNAME = ''
try:
  SCRIPTNAME = __file__
except:
  SCRIPTNAME = sys.executable

#if hasattr(sys, 'frozen'):
#  print(sys.executable)
#  print(os.path.dirname(sys.executable))
#  print(os.path.realpath(sys.executable))
#else:
#  print(sys.argv[0])

if sys.platform == 'win32':
  enc = 'mbcs'
else:
  enc = 'utf8'

CWD = os.path.abspath(os.path.dirname(SCRIPTNAME))
#print(CWD)
USERDICTS = path.join(CWD, "userdicts.txt")
STOPWORDS = path.join(CWD, "stopwords.txt")
FONTPATH = path.join(CWD, "NotoSansCJKsc-DemiLight.otf")
#print(os.path.isfile(FONTPATH))

def filter_tags(htmlstr):
    re_cdata   = re.compile(r'//<!\[CDATA\[[^>]*//\]\]>',re.I)
    re_script  = re.compile(r'<\s*script[^>]*>[^<]*<\s*/\s*script\s*>',re.I)
    re_style   = re.compile(r'<\s*style[^>]*>[^<]*<\s*/\s*style\s*>',re.I)
    re_br      = re.compile(r'<br\s*?/?>')
    re_h       = re.compile(r'</?\w+[^>]*>')
    re_comment = re.compile(r'<!--[^>]*-->')

    s = re_cdata.sub('',htmlstr)
    s = re_script.sub('',s)
    s = re_style.sub('',s)
    s = re_br.sub('\n',s)
    s = re_h.sub('',s)
    s = re_comment.sub('',s)

    s = replaceCharEntity(s)
    return s

def replaceCharEntity(htmlstr):
    CHAR_ENTITIES={'nbsp':' ','160':' ',
                'lt':'<','60':'<',
                'gt':'>','62':'>',
                'amp':'&','38':'&',
                'quot':'"','34':'"',}

    for k in CHAR_ENTITIES:
      htmlstr = htmlstr.replace(k, CHAR_ENTITIES[k])
    return(htmlstr)

def TextFilter(text, keepNum=False):
  idx = text.find('[Events]')
  if idx >= 0:
    content = text[idx:]
  else:
    content = text

  content = filter_tags(content)

  content = re.sub(r'\\N', '', content)
  content = re.sub(r'\{\\kf.*?\}', '', content)
  content = re.sub(r'\\f.*?%', '', content).replace('.', '')
  content = re.sub(r'\\(3*)c&H.*?&', '', content).replace('.', '')

  if not keepNum:
    content = re.sub(r'\d+', '', content).replace('.', '')

  return(content)

def LoadTexts(textfiles):
  text = []
  for f in textfiles:
    text.append(LoadText(f))
  return(', '.join(text))

def LoadText(textfile):
  if not os.path.isfile(textfile): return('')

  # Read the whole text.
  text = codecs.open(textfile, 'r').read()

  ftype = chardet.detect(text)
  #print(ftype)
  if ftype and ('encoding' in ftype):
    if (ftype['confidence'] < 0.8) or (not ftype['encoding']):
      ftype['encoding'] = 'utf-8'
  #text = text.decode(ftype['encoding'])

  text = codecs.open(textfile, 'r', encoding=ftype['encoding'], errors='ignore').read()
  #print(text[3:])
  return(TextFilter(text))

def CutText(text):
  if os.path.isfile(USERDICTS):
    print('Loading userdicts for cutting...')
    jieba.load_userdict(USERDICTS)

  #
  segment = []
  segs = jieba.cut(text) #切词，“么么哒”才能出现

  for seg in segs:
    if len(seg) > 1 and seg != '\r\n':
      segment.append(seg)

  #
  words_df = pd.DataFrame({'segment':segment})
  words_df.head()
  if os.path.isfile(STOPWORDS):
    stopwords = pd.read_csv(path.join(CWD, "stopwords.txt"),index_col=False,quoting=3,sep="\t",names=['stopword'],encoding="utf8")
    words_df = words_df[~words_df.segment.isin(stopwords.stopword)]

  words_stat = words_df.groupby(by=['segment'])['segment'].agg({'count':np.size})
  words_stat = words_stat.reset_index().sort_values(by='count', ascending=False)
  #print(words_stat)
  return(words_stat)

def CalcCloud(words, num=1000, width=1024, height=1024, bgcolor=None, mask=None):
  # Generate a word cloud image
  #wordcloud = WordCloud(font_path="NotoSansCJKsc-DemiLight.otf", max_font_size=40, background_color="black")
  wordcloud = WordCloud(font_path=FONTPATH,
                        width=width, height=height,
                        #max_font_size=40,
                        #min_font_size=4,
                        mode='RGBA',
                        background_color=bgcolor)
  wordcloud = wordcloud.fit_words(words.head(num).itertuples(index=False))
  return(wordcloud)

def DrawCloud(wordcloud, useMat=True, saveto=None):
  # Display the generated image:
  # the matplotlib way:
  if useMat:
    fig = plt.figure()
    plt.imshow(wordcloud)
    plt.axis("off")
    #
    if saveto:
      fig.savefig(saveto)
    else:
      plt.show()
  # The pil way (if you don't have matplotlib)
  else:
    image = wordcloud.to_image()
    if saveto:
      image.save(saveto)
    else:
      image.show()

def ShowImage(image):
  return

if __name__ == '__main__':
  num = 150
  if len(sys.argv) <= 1:
    print(u'usage: %s <input textfile> [output imagefile]' % os.path.basename(SCRIPTNAME) )
    exit()
  #f = path.join(CWD, sys.argv[1])
  f = sys.argv[1]
  if os.path.isfile(f):
    flist = [f]
  else:
    flist = glob(sys.argv[1])

  if len(flist)<=0:
    print(u'Text fils(s) can not loaded. File(s) name error or not exists.')
    exit()

  st = time()
  print(u'-'*72)
  print(u'Loading text file(s)......')
  text = LoadTexts(flist)
  print(u'Loading Timing = %.4fs' % (time() - st))
  st = time()
  print(u'-'*72)
  print(u'Cutting text contents......')
  words = CutText(text)
  print(u'-'*72)
  print(words[:num])
  print(u'Cutting Timing = %.4fs' % (time() - st))
  st = time()
  print(u'-'*72)
  print(u'Calcing word cloud layout......')
  cloud = CalcCloud(words, num)
#  print(cloud)
  print(u'Calcing Timing = %.4fs' % (time() - st))
  st = time()
  print(u'-'*72)
  if len(sys.argv) > 2:
    print(u'Saving word cloud to image......')
    saveto = sys.argv[2]
  else:
    print(u'Drawing word cloud to image......')
    saveto = None
  DrawCloud(cloud, False, saveto)
  print(u'Drawing Timing = %.4fs' % (time() - st))
  print(u'-'*72)
  print(u'Finished.')
