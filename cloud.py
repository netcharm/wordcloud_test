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
import getopt

from glob import glob
from time import time

import chardet
import re
import codecs         #codecs提供的open方法来指定打开的文件的语言编码，它会在读取的时候自动转换为内部unicode
import jieba          #分词包
import numpy as np    #numpy计算包
import pandas as pd   #数据分析包
import matplotlib.pyplot as plt
from PIL import Image

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
FONTPATH  = path.join(CWD, "NotoSansCJKsc-DemiLight.otf")
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
  CHAR_ENTITIES = {
    '&nbsp':' ','&160':' ',
    '&lt':'<','&60':'<',
    '&gt':'>','&62':'>',
    '&amp':'&','&38':'&',
    '&quot':'"','&34':'"',
  }

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

  print(u'> Loading %s' % os.path.basename(textfile.decode(enc)))
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

def CutText(text, userdict=None, stopword=None):
  if userdict and os.path.isfile(userdict):
    print('Loading userdicts for cutting...')
    jieba.load_userdict(userdict)
    print(u'-'*72)
  elif os.path.isfile(USERDICTS):
    print('Loading userdicts for cutting...')
    jieba.load_userdict(USERDICTS)
    print(u'-'*72)

  print('> Cutting contents...')
  segment = []
  segs = jieba.cut(text) #切词，“么么哒”才能出现

  for seg in segs:
    if len(seg) > 1 and seg != '\r\n':
      segment.append(seg)

  #
  words_df = pd.DataFrame({'segment':segment})
  words_df.head()
  if stopword and os.path.isfile(stopword):
    stopwords = pd.read_csv(stopword, index_col=False, quoting=3, sep="\t", names=['stopword'], encoding="utf8")
    words_df = words_df[~words_df.segment.isin(stopwords.stopword)]
  elif os.path.isfile(STOPWORDS):
    stopwords = pd.read_csv(path.join(CWD, "stopwords.txt"), index_col=False, quoting=3, sep="\t", names=['stopword'], encoding="utf8")
    words_df = words_df[~words_df.segment.isin(stopwords.stopword)]

  words_stat = words_df.groupby(by=['segment'])['segment'].agg({'count':np.size})
  words_stat = words_stat.reset_index().sort_values(by='count', ascending=False)
  #print(words_stat)
  return(words_stat)

def CalcCloud(words, num=1000, width=1024, height=1024, bgcolor=None, mask=None):
  _mask = None
  if mask:
    _mask = np.array(Image.open(path.join(mask)))
  # Generate a word cloud image
  #wordcloud = WordCloud(font_path="NotoSansCJKsc-DemiLight.otf", max_font_size=40, background_color="black")
  wordcloud = WordCloud(font_path=FONTPATH,
                        width=width, height=height,
                        #max_font_size=40,
                        #min_font_size=4,
                        mode='RGBA',
                        background_color=bgcolor,
                        mask=_mask
                        )
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
      #plt.show()
      pass
    return(plt)
  # The pil way (if you don't have matplotlib)
  else:
    image = wordcloud.to_image()
    if saveto:
      image.save(saveto)
    else:
      #image.show()
      pass
    return(image)

def ShowImage(image):
  return

def Usage():
  print(u'usage: %s [options] <[-i] input textfile>' % os.path.basename(SCRIPTNAME) )
  print(u'  options:' )
  print(u'    -w 400, --width=400' )
  print(u'    -h 400, --height=200' )
  print(u'    -b none, --bgcolor=none' )
  print(u'    -m none, --mask=none' )
  print(u'    -n 150, --number=150' )
  print(u'    -u none, --userdict=none' )
  print(u'    -s none, --stopword=none' )
  print(u'    -i, --input=<text file>' )
  print(u'    -o, --output=[output image file]' )
  return

def ParseArgs(argv):
  opt_s = 'w:h:b:m:i:o:n:u:s:'
  opt_l = ['width=', 'height=', 'bgcolor=', 'mask=', 'input', 'output', 'number', 'userdict', 'stopword']
  try:
    if isinstance(argv, str) or isinstance(argv, unicode) :
      args = argv.split()
    elif isinstance(argv, list):
      args = argv[1:]
    opts, args = getopt.getopt(args, opt_s, opt_l)
    #print(opts)
    #print(args)
  except getopt.GetoptError as err:
    # print help information and exit:
    print str(err)  # will print something like "option -a not recognized"
    Usage()
    sys.exit(2)

  options = dict()
  options['number'] = 150
  options['width'] = 512
  options['height'] = 512
  options['bgcolor'] = None
  options['mask'] = None
  options['userdict'] = None
  options['stopword'] = None
  options['input'] = []
  options['output'] = None

  for o, v in opts:
    if o.lower() in ['-w', '--width']:
      options['width'] = int(v)
    elif o.lower() in ['-h', '--height']:
      options['height'] = int(v)
    elif o.lower() in ['-b', '--bgcolor']:
      options['bgcolor'] = v
    elif o.lower() in ['-m', '--mask']:
      options['mask'] = v
    elif o.lower() in ['-i', '--input']:
      if os.path.isfile(v):
        options['input'].append(v)
      else:
        options['input'] = glob(v)
    elif o.lower() in ['-o', '--output']:
      options['output'] = v
    elif o.lower() in ['-n', '--number']:
      options['number'] = v
    elif o.lower() in ['-u', '--userdict']:
      options['userdict'] = v
    elif o.lower() in ['-s', '--stopword']:
      options['stopword'] = v

  if len(options['input']) <= 0 and len(args)>0:
    if os.path.isfile(args[0]):
      options['input'].append(args[0])
    else:
      options['input'] = glob(args[0])
  elif len(options['input']) <= 0:
    Usage()
    sys.exit(2)

  return(options)


if __name__ == '__main__':
  if len(sys.argv) <= 1:
    Usage()
    sys.exit()

  options = ParseArgs(sys.argv)

  st = time()
  print(u'-'*72)
  print(u'Loading text file(s)......')
  text = LoadTexts(options['input'])
  print(u'Loading Timing = %.4fs' % (time() - st))

  st = time()
  print(u'-'*72)
  print(u'Loading Jieba to cutting text contents......')
  words = CutText(text, userdict=options['userdict'], stopword=options['stopword'])
  print(words[:options['number']])
  print(u'Cutting Timing = %.4fs' % (time() - st))

  st = time()
  print(u'-'*72)
  print(u'Calcing word cloud layout......')
  cloud = CalcCloud( words,
    options['number'],
    width=options['width'],
    height=options['height'],
    mask=options['mask'],
    bgcolor=options['bgcolor']
  )
  #print(cloud)
  print(u'Calcing Timing = %.4fs' % (time() - st))

  st = time()
  print(u'-'*72)
  if options['output']:
    print(u'Saving word cloud to image......')
  else:
    print(u'Drawing word cloud to image......')
  img = DrawCloud(cloud, False, options['output'])
  print(u'Drawing Timing = %.4fs' % (time() - st))
  img.show()
  print(u'-'*72)
  print(u'Finished.')
