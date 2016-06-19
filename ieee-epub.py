#!/usr/bin/env python
import os, sys, re, shutil, uuid, subprocess, codecs
from bs4 import BeautifulSoup

def purge(text):
	return re.sub(' +', ' ', text.replace('\n', ''))

if len(sys.argv) < 3:
	exit("./ieee-epub INPUT OUTPUT")

try:
	os.mkdir('META-INF')
	os.mkdir('OEBPS')
except:
	print("Folders META-INF and OEBPS exists, please run in clean directory. ")
	exit("If you want to run anyway, delete these directories. ")
	
filesdir = sys.argv[1].split('.')[0]+'_files'

soup = BeautifulSoup(open(sys.argv[1], 'r').read(), 'html.parser')
try:
	title = purge(soup.select_one('div.content > div.text > h1').text)
except:
	title = purge(soup.select_one('div#article-page-hdr > h1').text)

abstract = purge(soup.select_one('div.content > div.text > p').text)

authors = []
for a in soup.select('div#authors > div.content > div.author > div.copy > h3'):
	authors.append(a.text)

with open('META-INF/container.xml', 'w') as cf:
	cf.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
	cf.write('<container version="1.0" xmlns="urn:oasis:names:tc:opendocument:xmlns:container">\n')
	cf.write('<rootfiles>\n')
	cf.write('<rootfile full-path="OEBPS/content.opf" media-type="application/oebps-package+xml"/>\n')
	cf.write('</rootfiles>\n')
	cf.write('</container>\n')

print "Converting:", title
txt = '<?xml version="1.0" encoding="UTF-8" standalone="no" ?>'
txt += '<html><head><title>%s</title><link href="%s/styles.css" type="text/css" rel="stylesheet"></link></head>' % (title, filesdir)
txt += '<body><div><h1>%s</h1></div>' % (title)
txt += '<p>By: %s</p>' % (', '.join(authors))
txt += '<h2>Abstract</h2><p>%s</p><hr />' % (abstract)

for sec in soup.select('div#article > div[id]'):
	head = sec.select_one('div.header > h2').text
	txt += "<h2>%s</h2>" % head
	for p in sec.findChildren():
		if p.name == "p" and not p.has_attr('class'):
			[s.extract() for s in p.select('span.tex')]
			[s.extract() for s in p.select('span.link')]
			for form in p.select('span.formula'):
				form.name = "div"
				form['style'] = "margin:16px auto;"
		elif p.name == "h3":
			pass
		elif p.name == "h4":
			pass
		elif p.name == "h5":
			pass
		elif p.name == "div" and p.has_attr('id') and p['id'].startswith('fig'):
			[s.extract() for s in p.select('div.zoom')]
			[s.extract() for s in p.select('p.links')]
		else:
			continue
		txt += unicode(p)

txt += '</body></html>'
with codecs.open('OEBPS/content.xhtml', 'w', encoding='utf-8') as wf:
	wf.write(txt)

with open('OEBPS/content.opf', 'w') as of:
	of.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
	of.write('<package xmlns="http://www.idpf.org/2007/opf" unique-identifier="BookID" version="2.0" >')
	of.write('<metadata xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:opf="http://www.idpf.org/2007/opf">')
	of.write('<dc:title>%s</dc:title>' % title)
	for a in authors:
		of.write('<dc:creator>%s</dc:creator>' % a)
	of.write('<dc:language>en-US</dc:language>')
	of.write('<dc:rights>Copyright IEEE</dc:rights>')
	of.write('<dc:publisher>IEEE</dc:publisher>')
	of.write('<dc:identifier id="BookID" opf:scheme="UUID">%s</dc:identifier>' % uuid.uuid4())
	of.write('</metadata>')
	of.write('<manifest>')
	of.write('<item id="content" href="content.xhtml" media-type="application/xhtml+xml" />')
	of.write('<item id="styles.css" href="%s/styles.css" media-type="text/css" />' % filesdir)
	for f in os.listdir(filesdir):
		if f.endswith('.png'):
			of.write('<item id="%s" href="%s/%s" media-type="image/png" />' % (f, filesdir, f))
		elif f.endswith('.gif'):
			of.write('<item id="%s" href="%s/%s" media-type="image/gif" />' % (f, filesdir, f))
	of.write('</manifest>')
	of.write('<spine toc="ncx">')
	of.write('<itemref idref="content" />')
	of.write('</spine>')
	of.write('</package>')

try:
	shutil.copytree(filesdir, "OEBPS/%s" % filesdir)
except:
	pass
try:
	os.remove(sys.argv[2])
except:
	pass
subprocess.check_output(["zip", sys.argv[2], "META-INF", "OEBPS", "-r"])
shutil.rmtree("META-INF")
shutil.rmtree("OEBPS")
