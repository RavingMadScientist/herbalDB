import subprocess


#note, we will need to use a temp directory so that we can get rid of all
#the latex metadata after the deed is done
def compileTex(texFile):
    subprocess.call(["pdflatex" , texFile])