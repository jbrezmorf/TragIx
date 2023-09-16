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
	csplain zpevnik.tex

zpevnik.tex : zpevnik.head.tex zpevnik.tail.tex 
	cat zpevnik.head.tex >zpevnik.tex
	ls *.sng|sort|grep -v "test.sng"|sed 's/\(.*\)/\\inputsong{\1}/' >>zpevnik.tex
	cat zpevnik.tail.tex >>zpevnik.tex
