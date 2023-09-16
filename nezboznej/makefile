#  makefile predpoklada instalovany tex s formatem csplain
#  v kodovani iso-8859-2


all : zpev-duplex.pdf
front : zpev-front.pdf
back : zpev-back.pdf

zpev-front.pdf : zpev-front.ps
	ps2pdf -sPAPERSIZE=a4 zpev-front.ps zpev-front.pdf
zpev-back.pdf : zpev-back.ps
	  ps2pdf -sPAPERSIZE=a4 zpev-back.ps zpev-back.pdf
zpev-duplex.pdf : zpev-duplex.ps
	ps2pdf -sPAPERSIZE=a4 zpev-duplex.ps zpev-duplex.pdf

zpev-duplex.ps : zpevnik.ps
	pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm),1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-duplex.ps
zpev-back.ps : zpevnik.ps
	pstops -pa4 '2:1L(29.7cm,0cm)+-0L(29.7cm,14.85cm)' zpevnik.ps zpev-back.ps
zpev-front.ps : zpevnik.ps
	pstops -pa4 '2:-1L(29.7cm,0cm)+0L(29.7cm,14.85cm)' zpevnik.ps zpev-front.ps

zpevnik.ps : zpevnik.dvi
	dvips -o zpevnik.ps zpevnik.dvi

zpevnik.dvi : zpevnik.tex lyric.tex
	tex -fmt csplain zpevnik.tex

zpevnik.tex : zpevnik.head.tex zpevnik.tail.tex zpevnik.src
	make convert
	make separate
	cat zpevnik.head.tex >zpevnik.tex
	ls songs/*.sng|sed 's/\(.*\)/\\inputsong{\1}/' >>zpevnik.tex
	cat zpevnik.tail.tex >>zpevnik.tex

convert:
	enc=`head -n 1 zpevnik.src|grep "^encoding:"|sed 's/encoding://'|\
	sed 's/ //g'`;\
	enc=$${enc:-utf8};\
	./cstocs $$enc il2 zpevnik.src >zpevnik.src.il2

separate:
	rm -r -f songs; mkdir songs
	./sepsongs zpevnik.src.il2 # perl script 

sort:
	for f in songs/*.sng;\
	do head -n 1 $$f|sed 's/N: *//'|sed "s|$$|:$$f|";done|sort|\
	sed 's/.*://'>sorted.list
	rm -f zpevnik.sort; 
	head -n 1 zpevnik.src|grep "^encoding:">zpevnik.sort;
	for f in `cat sorted.list`;\
	do echo "==================">>zpevnik.sort;cat $$f >>zpevnik.sort;\
	done
	mv -f zpevnik.src zpevnik.backup
	mv zpevnik.sort zpevnik.src
	


