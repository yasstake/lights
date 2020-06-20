OUTDIR=./OUTDIR
INDIR=./lightsdata/


all: $(OUTDIR)
	python -m loader.ocr $(INDIR) $(OUTDIR)

$(OUTDIR):
	mkdir $(OUTDIR)

clean:
	rm -rf $(OUTDIR)
