# Python WordCloud package example

## Requirements

1. python 2.7.x
1. wordcloud
1. Pillow
1. numpy
1. pandas
1. matplotlib
1. jieba
1. mecab python binding

## Usage

```
  print(u'usage: %s [options] <[-i] input textfile>' % os.path.basename(SCRIPTNAME) )
  print(u'  options:' )
  print(u'    -?, --help')
  print(u'      display usage help' )
  print(u'    -f fontpath, --font=fontpath')
  print(u'      custom font name with full path & ext' )
  print(u'    -p, --plot')
  print(u'      using matplotlib display cloud image' )
  print(u'    -l cn, --lang=cn|jp')
  print(u'      select text language will cutting, only support cn/jp' )
  print(u'    -w 400, --width=512')
  print(u'      cloud image\' width' )
  print(u'    -h 400, --height=512')
  print(u'      cloud image\' height' )
  print(u'    -b none, --bgcolor=black')
  print(u'      cloud image\'s background color' )
  print(u'    -m none, --mask=none')
  print(u'      cloud image\'s outline mask image' )
  print(u'    -c true, --recolor=true|false|gray')
  print(u'      recolor the output cloud with mask image color' )
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
```

## ToDo

using PyQT4 for GUI


