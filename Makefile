

OUTDIR=./OUTDIR
INDIR=./lights_data

.include depend

#.PHONY dep clean all

out.png:


$(OUTDIR):
	mkdir $(OUTDIR)

clean:
	rm -rf $(OUTDIR)
