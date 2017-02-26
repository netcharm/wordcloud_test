#!/usr/bin/env python
#coding:utf-8
#from __future__ import unicode_literals
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

import numpy as np    #numpy计算包
import pandas as pd   #数据分析包
import matplotlib.pyplot as plt
from PIL import Image

import jieba          #中文分词包
import MeCab          #日文分词包
#######################################################
#set MECAB_PATH=C:\Program Files\MeCab\bin\libmecab.dll
#set MECAB_CHARSET=utf8 or shift-jis
#######################################################
#os.environ['MECAB_PATH']='C:/Program Files/MeCab/bin/libmecab.dll'
os.environ['MECAB_PATH']='D:\\App\\Booklib\\MeCab\\bin\\libmecab.dll'
os.environ['MECAB_CHARSET']='utf-16'

from wordcloud import WordCloud

__version__ = '1.0.0.0'

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

reflag = re.I|re.U|re.M

def filter_tags(htmlstr):
  idx = htmlstr.find('<body>')
  if idx >= 0:
    s = htmlstr[idx:]
  else:
    s = htmlstr

  re_cdata   = re.compile(r'//<!\[CDATA\[[^>]*//\]\]>', reflag)
  re_script  = re.compile(r'<\s*script[^>]*>[^<]*<\s*/\s*script\s*>', reflag)
  re_style   = re.compile(r'<\s*style[^>]*>[^<]*<\s*/\s*style\s*>', reflag)
  re_br      = re.compile(r'<br\s*?/?>', reflag)
  re_h       = re.compile(r'</?\w+[^>]*>', reflag)
  re_comment = re.compile(r'<!--[^>]*-->', reflag)
  re_head    = re.compile(r'(<html.*?>)|(<\?xml.*?\?>)|(<!DOCTYPE.*?>)|(<head>.*?</head>)|(<title.*?/title>)|(<meta.*?/meta>)', flag)

  s = re_cdata.sub('',s)
  s = re_script.sub('',s)
  s = re_style.sub('',s)
  s = re_br.sub('\n',s)
  s = re_h.sub('',s)
  s = re_comment.sub('',s)
  s = re_head.sub('',s)

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

def filter_lrc(content):
  pat_lyric = ur'(\[id:.*?\])|(\[al:.*?\])|(\[ar:.*?\])|(\[ti:.*?\])|(\[by:.*?\])|(\[la:.*?\])|(\[offset:.*?\])|(\[\d+:\d+(\.\d+){0,1}\])'
  return(re.sub(pat_lyric, '', content, flags=reflag))

def filter_ass(content):
  idx = content.find('[Events]')
  if idx >= 0:
    content = content[idx+8:]

  content = content.strip()
  pat_ass_head = ur'(^\[Script Info\](([(\r)|(\n)|(\r\n)].*?)*?)^\[Events\][(\r)|(\n)|(\r\n)].*?Text)'
  pat_ass_diag = ur'(^Format:.*?Text)|(^Dialogue:.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,.*?,)|(\\N)|(\{\\kf.*?\})|(\{\\f.*?\})|(\\f.*?%)|(\{\\(3){0,1}c&H.*?&\})|(\\(3){0,1}c&H.*?&)|(\{\\a\d+\})|(\{\\.*?\})'
  # cost too times for multi-line re
  #content = re.sub(pat_ass_head, ' ', content, flags=reflag)
  content = re.sub(pat_ass_diag, ' ', content, flags=reflag)
  return(content)

def TextFilter(text, doc='txt', keepNum=False):
  content = text
  if doc.lower() in ['html', 'htm', 'xml', 'xhtml']:
    content = filter_tags(content)
  elif doc.lower() in ['lrc', 'lyric']:
    content = filter_lrc(content)
  elif doc.lower() in ['ass', 'ssa']:
    content = filter_ass(content)
  #print(content)

  pat_misc = ur'(&#\d+;)|([\u0001-\u001F,\u0021-\u0040,\u005B-\u0060,\u007B-\u00FF,\u2000-\u206F,\u2190-\u2426,\u3000-\u303F,\u31C0-\u31E3,\uFE10-\uFE4F])|([\.|·|　|…])'
  content = re.sub(pat_misc, ' ', content, flags=reflag)
  #print(content)

  if not keepNum:
    content = re.sub(r'\d+', '', content, flags=reflag).replace('.', ' ')

  return(content)

def LoadTexts(textfiles):
  text = []
  for f in textfiles:
    text.append(LoadText(f))
  return(', '.join(text))

def LoadText(textfile):
  if not os.path.isfile(textfile): return('')

  print(u'> %s' % os.path.basename(textfile.decode(enc)))
  # Read the whole text.
  text = codecs.open(textfile, 'r').read()

  ftype = chardet.detect(text)
  #print(ftype)
  if ftype and ('encoding' in ftype):
    if (ftype['confidence'] < 0.8) or (not ftype['encoding']):
      ftype['encoding'] = 'utf-8'

  text = codecs.open(textfile, 'r', encoding=ftype['encoding'], errors='replace').read()
  try:
    doc = os.path.splitext(textfile)[1][1:]
  except:
    doc = 'txt'
  return(TextFilter(text, doc=doc))

def CutCN(text, userdict=None, stopword=None):
  if userdict and os.path.isfile(userdict):
    print('> Loading userdicts for Jieba cutting...')
    jieba.load_userdict(userdict)
    print(u'-'*72)
  elif os.path.isfile(USERDICTS):
    print('> Loading userdicts for Jieba cutting...')
    jieba.load_userdict(USERDICTS)
    print(u'-'*72)

  print('> Making contents segments...')
  segs = jieba.cut(text) #切词，“么么哒”才能出现

  return(segs)

def CutJP(text, userdict=None, stopword=None):
  # params: -Oyomi, -Osimple, -Ochasen (only for ipadic), or null string
  m = MeCab.Tagger("")
  d = m.dictionary_info()
  print('> Loading MeCab dict %s @ %s' % (d.filename.encode(enc), d.charset))
  ts = m.parseToNode(text.encode('utf8'))
  print('> Making contents segments...')
  segs = []
  while ts:
    #print ts.surface, "\t", ts.feature
    #print(len(segs), ts.surface)
    try:
      #if ts.surface=='\r' or ts.surface=='': pass
      segs.append(unicode(ts.surface))
    except:
      pass
    ts = ts.next

  return(segs)

def CutText(text, userdict=None, stopword=None, lang='cn'):
  segment = []
  if lang.lower()=='jp':
    try:
      segs = CutJP(text, userdict=userdict, stopword=stopword)
    except:
      segs = CutCN(text, userdict=userdict, stopword=stopword)
  else:
    segs = CutCN(text, userdict=userdict, stopword=stopword)

  for seg in segs:
    if len(seg) > 1 and seg != '\r\n':
      segment.append(seg)

  #
  words_df = pd.DataFrame({'segment':segment})
  words_df.head()
  if stopword and os.path.isfile(stopword):
    stopwords = pd.read_csv(stopword, index_col=False, quoting=3, sep="\t", names=['stopword'], encoding="utf8")
  elif os.path.isfile(STOPWORDS):
    stopwords = pd.read_csv(path.join(CWD, "stopwords.txt"), index_col=False, quoting=3, sep="\t", names=['stopword'], encoding="utf8")

  stopwords_c = pd.DataFrame({'stopword':stopwords.stopword.str.capitalize()})
  stopwords_u = pd.DataFrame({'stopword':stopwords.stopword.str.upper()})
  stopwords_l = pd.DataFrame({'stopword':stopwords.stopword.str.lower()})

  words_df = words_df[~words_df.segment.isin(stopwords.stopword)]
  words_df = words_df[~words_df.segment.isin(stopwords_c.stopword)]
  words_df = words_df[~words_df.segment.isin(stopwords_u.stopword)]
  words_df = words_df[~words_df.segment.isin(stopwords_l.stopword)]

  words_stat = words_df.groupby(by=['segment'])['segment'].agg({'count':np.size})
  words_stat = words_stat.reset_index().sort_values(by='count', ascending=False)
  #print(words_stat)
  return(words_stat)

def CalcCloud(words, font=FONTPATH, num=1000, width=1024, height=1024, bgcolor=None, mask=None):
  _mask = None
  if mask:
    _mask = np.array(Image.open(path.join(mask)))
  # Generate a word cloud image
  #wordcloud = WordCloud(font_path="NotoSansCJKsc-DemiLight.otf", max_font_size=40, background_color="black")
  if os.path.isfile(font):
    dst_font = font
  else:
    dst_font = FONTPATH
  wordcloud = WordCloud(font_path=dst_font,
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
    fig.canvas.set_window_title('Words Cloud')
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
  print(u'    -?, --help')
  print(u'      display usage help' )
  print(u'    -f fontpath, --font=fontpath')
  print(u'      custom font name with full path & ext' )
  print(u'    -p, --plot')
  print(u'      using matplotlib display cloud image' )
  print(u'    -w 400, --width=512')
  print(u'      cloud image\' width' )
  print(u'    -h 400, --height=512')
  print(u'      cloud image\' height' )
  print(u'    -b none, --bgcolor=black')
  print(u'      cloud image\'s background color' )
  print(u'    -m none, --mask=none')
  print(u'      cloud image\'s outline mask image' )
  print(u'    -n 150, --number=150')
  print(u'      max words displayed in cloud ' )
  print(u'    -u none, --userdict=none')
  print(u'      user dictionary for text cutting' )
  print(u'    -s none, --stopword=none')
  print(u'      stopwords list for text cutting' )
  print(u'    -i, --input=<text file>')
  print(u'      input text file(s), single file or wildcard like *.txt, *.html' )
  print(u'    -o, --output=[output image file]')
  print(u'      if set this option, cloud image will save to file, and will not displayed' )
  return

def ParseArgs(argv):
  opt_s = 'w:h:b:m:i:o:n:u:s:l:f:p?'
  opt_l = ['width=', 'height=', 'bgcolor=', 'mask=', 'input=', 'output=', 'number=', 'userdict=', 'stopword=', 'lang=', 'font=', 'plot', 'help']
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
  options['font'] = FONTPATH
  options['number'] = 150
  options['width'] = 512
  options['height'] = 512
  options['bgcolor'] = 'black'
  options['mask'] = None
  options['userdict'] = None
  options['stopword'] = None
  options['input'] = []
  options['output'] = None
  options['lang'] = 'cn'
  options['plot'] = False

  for o, v in opts:
    if o.lower() in ['-?', '--help']:
      Usage()
      sys.exit(2)
    elif o.lower() in ['-w', '--width']:
      options['width'] = int(v)
    elif o.lower() in ['-h', '--height']:
      options['height'] = int(v)
    elif o.lower() in ['-b', '--bgcolor']:
      if v.lower() == 'none':
        options['bgcolor'] = None
      else:
        options['bgcolor'] = v
    elif o.lower() in ['-m', '--mask']:
      options['mask'] = v
    elif o.lower() in ['-i', '--input']:
      if os.path.isfile(v):
        options['input'].append(v)
      else:
        options['input'].extend(glob(v))
    elif o.lower() in ['-o', '--output']:
      options['output'] = v
    elif o.lower() in ['-n', '--number']:
      options['number'] = v
    elif o.lower() in ['-u', '--userdict']:
      options['userdict'] = v
    elif o.lower() in ['-s', '--stopword']:
      options['stopword'] = v
    elif o.lower() in ['-l', '--lang']:
      options['lang'] = v
    elif o.lower() in ['-f', '--font']:
      options['font'] = v
    elif o.lower() in ['-p', '--plot']:
      options['plot'] = True

  if len(args) > 0:
    for arg in args:
      if os.path.isfile(arg):
        options['input'].append(arg)
      else:
        options['input'].extend(glob(arg))
  elif len(options['input']) <= 0:
    Usage()
    sys.exit(2)

  #print(options)
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
  print(u'Cutting text contents......')
  words = CutText(text, userdict=options['userdict'], stopword=options['stopword'], lang=options['lang'])
  print(words[:options['number']])
  print(u'Cutting Timing = %.4fs' % (time() - st))

  st = time()
  print(u'-'*72)
  print(u'Calcing word cloud layout......')
  cloud = CalcCloud( words,
    font=options['font'],
    num=options['number'],
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
  img = DrawCloud(cloud, options['plot'], options['output'])
  print(u'Drawing Timing = %.4fs' % (time() - st))
  img.show()
  print(u'-'*72)
  print(u'Finished.')
