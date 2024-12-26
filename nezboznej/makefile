#  makefile predpoklada instalovany tex s formatem csplain
#  v kodovani iso-8859-2
TAIL_SOURCE=zpevnik-utf8.tail.tex
HEAD_SOURCE=zpevnik-utf8.head.tex
MAIN_SOURCE=zpevnik-utf8.src

.PHONY : all
all : zpev-duplex.pdf
front : zpev-front.pdf
back : zpev-back.pdf


.PHONY : clean
clean:
	rm -f zpev-duplex.pdf zpevnik.*

# zpev-front.pdf : zpev-front.ps
# 	ps2pdf -sPAPERSIZE=a4 zpev-front.ps zpev-front.pdf
# zpev-back.pdf : zpev-back.ps
# 	  ps2pdf -sPAPERSIZE=a4 zpev-back.ps zpev-back.pdf
# zpev-duplex.pdf : zpev-duplex.ps
# 	ps2pdf -sPAPERSIZE=a4 zpev-duplex.ps zpev-duplex.pdf
# 
# zpev-duplex.ps : zpevnik.ps
# 	pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm),1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-duplex.ps
# zpev-back.ps : zpevnik.ps
# 	pstops -pa4 '2:1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-back.ps
# zpev-front.ps : zpevnik.ps
# 	pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm)' zpevnik.ps zpev-front.ps

# zpev-back.pdf : zpevnik.pdf
# 	pdftk zpevnik.pdf cat 1-endS output zpev-back.pdf

#zpev-back.pdf : zpevnik.pdf
#	pdftk zpevnik.pdf cat even output zpev-back-even.pdf
#	pdftk zpev-back-even.pdf cat end-1 output zpev-back.pdf
#	rm zpev-back-even.pdf
	
# zpev-front.pdf : zpevnik.pdf
# 	pdftk zpevnik.pdf cat end-1 output zpev-front.pdf

#zpev-front.pdf : zpevnik.pdf
#	pdftk zpevnik.pdf cat odd output zpev-front-odd.pdf
#	pdftk zpev-front-odd.pdf cat end-1 output zpev-front.pdf
#	rm zpev-front-odd.pdf
	
# zpev-duplex.pdf : zpevnik.pdf
# 	pdftk zpevnik.pdf cat 1-endS output zpev-duplex.pdf
	
# zpev-duplex.pdf : zpevnik.pdf
# 	pdftk zpevnik.pdf shuffle odd even output zpev-duplex.pdf

zpev-duplex.pdf : zpevnik.pdf
	 pdftops zpevnik.pdf zpevnik.ps
	 #pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm),1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-duplex.ps
	 pstops -pa4 '2:-1L(21cm,0cm)+0L(21cm,14.85cm),1L(21cm,0cm)+-0L(21cm,14.85cm)' zpevnik.ps zpev-duplex.ps
	 ps2pdf zpev-duplex.ps zpevnik-duplex.pdf
	 #pdfjam zpevnik.pdf --nup 2x1 --landscape --paper a4paper --outfile zpev-duplex.pdf

# zpevnik.ps : zpevnik.dvi
# 	dvips -o zpevnik.ps zpevnik.dvi

zpevnik.pdf : zpevnik.tex lyric.tex
	echo "Build"
	luatex -fmt pdfcsplain zpevnik.tex

.PHONY : zpevnik.tex
zpevnik.tex : $(HEAD_SOURCE) $(TAIL_SOURCE) $(MAIN_SOURCE)
	#make convert
	cp $(MAIN_SOURCE) _$(MAIN_SOURCE)
	make separate
	cat $(HEAD_SOURCE) >zpevnik.tex
	ls songs/*.sng|sed 's/\(.*\)/\\inputsong{\1}/' >>zpevnik.tex
	cat $(TAIL_SOURCE) >>zpevnik.tex

convert:
	enc=`head -n 1 $(MAIN_SOURCE)|grep "^encoding:"|sed 's/encoding://'|\
	sed 's/ //g'`;\
	enc=$${enc:-utf8};\
	./cstocs $$enc utf8 zpevnik.src >_zpevnik.src.utf8

.PHONY : separate
separate:
	rm -r -f songs; mkdir songs
	python3 sepsongs.py _$(MAIN_SOURCE)

# Target to sort songs in 'songs' dir and form new main source file.
# TODO: call separate
sort:
	for f in songs/*.sng;\
	do head -n 1 $$f|sed 's/N: *//'|sed "s|$$|:$$f|";done|sort|\
	sed 's/.*://'>sorted.list
	rm -f _zpevnik.sort; 
	head -n 1 $(MAIN_SOURCE)|grep "^encoding:">_zpevnik.sort;
	for f in `cat sorted.list`;\
	do echo "==================">>zpevnik.sort;cat $$f >>_zpevnik.sort;\
	done
	mv -f $(MAIN_SOURCE) $(MAIN_SOURCE).backup
	mv _zpevnik.sort $(MAIN_SOURCE)
	


