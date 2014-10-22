from urllib import urlopen 
import re
from HTMLParser import HTMLParser
from time import sleep
import codecs
class bookgrabber:
  folder=''
  pagenumbers=list()		#Liste fuer die Seitenzahlen (falls leerseiten existieren)
  urllist=list()		#Liste fuer die verschiedenen Seiten URLs
  content=list()		#Liste mit den extrahierten Buchseiten
  blocknumbers=list()			#Anzahl der gefundenen Bloecke mit Text; zum Pruefen von nicht erkannten Bloecken
  def __init__(self,folder,startpage,number=1):
    self.folder=folder
    self.urllist.append(folder+startpage)
    self.pagenumbers.append(number)
    self.content=list()
    self.metacontent=list()
  def urlcontent(self, url):	#gibt den Quelltext einer URL zurueck
    usock = urlopen(url)
    data = usock.read()
    usock.close()
    return data
  def extract_page(self):
    parser=HTMLParser()
    text=self.urlcontent(self.urllist[-1])
    blockcount=0
    blockcontent=list()
    for block in re.findall('(?s)<tr>(.*?)</tr>',text):
      blockcount+=1
      columncontent=list()
      for column in re.findall('<td(.*?)>(.*?)</td>',block):
	columndict=dict()
	columndict['text']=column[1]
	if columndict['text']=='&nbsp;': columndict['text']=''
	columndict['text']=parser.unescape(columndict['text'])
	keywords=re.findall('[ ](.*?)=',column[0])
	for keyword in keywords:
	  keyval=re.search(keyword+'="(.*?)"',column[0])
	  if keyval: columndict[keyword]=keyval.group(1)
	columncontent.append(columndict)
      blockcontent.append(columncontent)
    self.metacontent.append(blockcontent)
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    pagetext=list(block[2]['text'] for block in blockcontent)		#extrahiert den Text aus der mittleren Spalte heraus (pagetext=Liste aus Zeilentexten)  
    while pagetext[-1]=='':						#remove empty lines at page end
      pagetext=pagetext[:-1]
      #print "empty last field "+self.urllist[-1]   			#empty last fields do occur as I tested!!
    menulinks=re.findall('href="(.*?)"',pagetext[-1])			#use last nonempty line to extract the links in the menu
    pagenames=re.findall('>Seite (.*?)<',pagetext[-1])			#collect pagenumbers of the links
    pagetext=pagetext[3:-1]						#now remove last line and also the first 3 #reedit: why the first 3 lines dear past me?! Well we don't use it anyway right?
    self.content.append(pagetext)					#now pagetext will not be pagetext any further and can be added to content #reedit: wtf past me what do you mean?!
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    #   Finden der naechsten Seite aus den Zeilentexten
    #----------------------------------------------------------------------------------------------------------------------------------------------------------
    if len(menulinks)==0:						#no menu should not happen
      print "no menu"
      for line in pagetext:
	print line
      return False
    elif len(menulinks)<3:						#can happen for first or last page
      if len(self.urllist)==1:						#for first page do this
	nextpage=menulinks[0]
	nextname=pagenames[0]
      else:								#for last page there is no next page, so we are done
	print "Can't find next page after %s" % (self.urllist[-1])
	print "Suppose it is the last page"
	print "Collected total of %d pages" % (len(self.urllist))
	return False
    else:								#otherwise we have a 3 entry menu where the next page is the middle link
      if menulinks[1]=='020.html':		#debug
        return False
      else:					#debug
        nextpage=menulinks[1]			#shift 1 left after debug
        nextname=pagenames[1]			#also shift 1 left 
    nexturl=self.folder+nextpage
    self.urllist.append(nexturl)
    self.pagenumbers.append(int(nextname))
    return True								#Having reached this point means there is a next page
  def extract(self):
    EOB=False
    while not EOB:
      EOB = not self.extract_page()
      if not EOB:
	print "now searching:"+self.urllist[-1]
      else:
	print 'finished'
    sleep(0.0)
    print self.pagenumbers
  def postprocessor(self):
    for page in self.metacontent:
      for line in page:
	for column in line:
	  column['text']=re.sub('(<i>)(.*?)(</i>)','\\\\textit{\\2}',column['text'])
	  column['text']=re.sub('(<h5>)(.*?)(</h5>)','\\\\subsection{\\2}',column['text'])
	  column['text']=re.sub('[#]','',column['text'])
	  if column['text'].find('<i>'):
	    column
	  column['text']
	pass
    self.content=list(list(line[2]['text'] for line in page[3:-1]) for page in self.metacontent)
  def write_book(self,filename):
    fl = codecs.open(filename, "w", "utf-8")
    vorlage = codecs.open('kant_vorlage.tex')
    for line in vorlage:
      fl.write(line)		#no newline because it is already in the string
    for i in range(len(self.metacontent)):
      fl.write(self.tex_page(buch1.metacontent[i]))
      fl.write('\\newpage\n')   ##reedit: TODO i will need extra blank lines if page numbers are jumping
    fl.write('\\end{document}')
    #self.postprocessor()
    #for page in self.content:
    #  for line in page:
#	tmp=''
#	if len(line.rstrip())!=0 and re.match('\w|[ ]|[,]|[.]|[:]',line.rstrip()[-1]):
#	  tmp='\\linebreak'
#	  if len(line)<60:
#	    tmp='\\\\'
#	fl.write(line+tmp+'\n')
#     fl.write('\\newpage\n')
#    fl.write('\\end{document}')
  def tex_page(self,page):
    offset=2;	#die ersten 3 Zellen sind nicht seitentext
    i=1;
    text=''
    while i+offset<len(page):
      #print i
      linetext=''
      thisline=page[i+offset]
      if i>0:
	prevline=page[i+offset-1]
      else:
	prevline=None
      if i<len(page)-offset-1:
	nextline=page[i+offset+1]
      else:
	nextline=None
      body=get_body(thisline)
      margin=get_margin(thisline)
      #print body
      
      
      if is_section(thisline):									#handling of section headings
	if (not is_section(prevline)) and is_section(nextline):					#first line
	  body=re.sub('(<h2>)(.*?)(</h2>)','\section{\\2\\\\\\\\',body)	
	if is_section(prevline) and is_section(nextline):					#middle line
	  body=re.sub('(<h2>)(.*?)(</h2>)','\\2\\\\\\\\',body)
	if is_section(prevline) and (not is_section(nextline)):					#last line
	  body=re.sub('(<h2>)(.*?)(</h2>)','\\2}',body)
	if (not is_section(prevline)) and (not is_section(nextline)):				#only line
	  body=re.sub('(<h2>)(.*?)(</h2>)','\section{\\2}',body)
	  
      if is_subsection(thisline):									#handling of section headings
	if (not is_subsection(prevline)) and is_subsection(nextline):					#first line
	  body=re.sub('(<h5>)(.*?)(</h5>)','\subsection{\\2',body)	
	if is_subsection(prevline) and is_subsection(nextline):					#middle line
	  body=re.sub('(<h5>)(.*?)(</h5>)','\\2\\\\\\\\',body)
	if is_subsection(prevline) and (not is_subsection(nextline)):					#last line
	  body=re.sub('(<h5>)(.*?)(</h5>)','\\2}',body)
	if (not is_subsection(prevline)) and (not is_subsection(nextline)):				#only line
	  body=re.sub('(<h5>)(.*?)(</h5>)','\subsection{\\2}',body)
      if is_empty(thisline) and is_empty(prevline):
	lineend=''
      else:
	lineend='\n'
      if is_quote(thisline):
	body=re.sub('(<i>)(.*?)(</i>)','\\\\textit{\\2}',body)
      linetext+=body
      if is_passage(thisline):									# you are in a paragraph
	if is_passage(nextline):								# next line is a text line of the same paragraph
	  if len(body)>60:									# line is long enough for blocksatz
	    linetext+='\\linebreak'
	  else:											#not long enough for blocksatz
	    linetext+='\\\\'
	else:											#at the end of a paragraph
	  if is_empty(nextline):								#here next line should be whitespace
	    #linetext+='\\\\'
	    linetext+=''
      else:
	linetext+=''
      text=text+linetext+lineend
      i+=1
    return text
  
  
  pass
def is_passage(line):
  if (not is_section(line)) and (not is_subsection(line)) and (not is_empty(line)):
    return True
  else:
    return False
def is_section(line):
    body=get_body(line)
    if re.search('(<h2>)',body):
      return True
    else:
      return False
def is_subsection(line):
  body=get_body(line)
  if re.search('(<h5>)',body):
    return True
  else:
    return False
def is_quote(line):
  body=get_body(line)
  if re.search('(<i>)',body):
    return True
  else:
    return False
def is_empty(line):
  if get_body(line)=='':
    return True
  else:
    return False
def is_regular(line):
  for column in line:
    if 'width' in column and column['width']=='60%':
      return True 
  return False
def get_body(line):						#gets the body from line (body of the td tag with width="60%"
  if is_regular(line):
    for column in line:
      if 'width' in column and column['width']=='60%':
	return column['text']
  else:
    #print 'irregular line!!!'
    return ''
def get_margin(line):
    for column in line:
      if 'width' in column and column['width']=='16%':
	return column['text']
    return None
    
def showtags(buch):
  taglist=list()
  for page in buch.content:
    for line in page:
      tags= re.findall('<(.*?)>',line)
      if len(tags)!=0:
	taglist.extend(tags)
  for element in set(taglist):
    print element

#if __name__=='__main__' :
buch1=bookgrabber('http://www.korpora.org/kant/aa01/','001.html')
buch1.extract()
showtags(buch1)
buch1.write_book('book1.tex')
buch1.tex_page(buch1.metacontent[0])
for i in range(len(buch1.metacontent)):
  print buch1.tex_page(buch1.metacontent[i]),
  print '\\newpage'




    

