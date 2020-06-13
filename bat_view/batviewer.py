# -*- coding: utf-8 -*-
"""
Created on Sat Jun 13 11:51:05 2020
Simple viewer for Batdetect data.
@author: David
"""
import os,struct
import wave, numpy,io,csv
import matplotlib.pyplot as plt
import scipy.signal as sig, numpy as np
import tkinter as tk
import tkinter.filedialog as tkfd
from PIL import Image, ImageTk

class SpecViewer (tk.Frame):
    def __init__(self, master=None):
        tk.Frame.__init__(self, master)
        self.master=master
        self.pack(fill="both", expand=True)
        self.createWidgets()

    def createWidgets(self):
        menu = tk.Menu(self.master)
        self.master.config(menu=menu)
        file=tk.Menu(menu)
        file.add_command(label="Exit", command=self.client_exit)
        menu.add_cascade(label='File', menu=file)
        settings=tk.Menu(menu)
        settings.add_command(label="Audio Folder", command=self.set_AudioFolder)
        settings.add_command(label="Analysis Folder", command=self.set_AnalysisFolder)
        settings.add_command(label="Spectrogram Settings", command=self.set_SpectrogramSettings)
        settings.add_command(label="show parameters", command = self.showparam)
        menu.add_cascade(label="Settings", menu=settings)
        #self.menubar = tk.Frame(self, bg='#333')
        
        #self.quitButton = tk.Button(self.menubar, text='Quit', command=self.quit)
        #self.settingsButton(self.menubar, text="Settings", command=self.doSettings)
        #self.loadButton = tk.Button(self.menubar, text="Load", command = self.loadSpectrogram)      
        #self.quitButton.grid()
        #self.loadButton.grid(column=1,row=0)
        #self.menubar.grid()
        self.audioframe=tk.Frame(self,bg='#fff')
        self.audioframe.pack(fill="x", expand=True)
#        self.audioframe.grid(sticky=tk.W+tk.E)
        self.audiofiles_lb = tk.Listbox(self.audioframe)
        self.audiofiles_lb.grid(row = 0, column=1, rowspan=4, sticky=tk.N+tk.S)
        self.audiofiles_sb = tk.Scrollbar(self.audioframe)
        self.audiofiles_sb.grid(row = 0, column=2, rowspan=4, sticky=tk.N+tk.S)
        self.audiofiles_lb.config( yscrollcommand = self.audiofiles_sb.set)
        self.audiofiles_lb.bind('<<ListboxSelect>>',self.selectAudio)
        self.audiofiles_sb.config(command=self.audiofiles_lb.yview)
        self.audioframe.grid_columnconfigure(0, weight=1)
        self.lbl_temp = tk.Label(self.audioframe, text='No audio file selected')
        self.lbl_temp.grid(row=0, column=0, sticky=tk.E+tk.W)
        self.audiofiles_lb.insert(tk.END, "No audio files loaded")
        # analysis summary.
        self.analysisblock= tk.Frame(self.audioframe,bg='#ddb')
        self.analysisblock.grid(sticky=tk.N+tk.S+tk.W+tk.E, row=3)
        self.analysissummary = tk.Label(self.analysisblock,text='No analysis file loaded')
        self.analysissummary.grid(row=0, column=0, columnspan=2, sticky=tk.E+tk.W)
        self.analysisthreshold = tk.Label(self.analysisblock, text='Threshold: 0.5')
        self.analysisthreshold.grid(row=1, column=0)
        self.thresholdslider = tk.Scale(self.analysisblock,from_=0.0, to=1.0, 
                                        resolution=0.05, orient=tk.HORIZONTAL, command=self.setthreshold)
        self.thresholdslider.set(0.8)
        self.thresholdslider.grid(row=1, column=1, sticky=tk.E+tk.W)
        
        
        self.imageframe=tk.Frame(self,bg='#fff')
#        self.imageframe.grid(sticky=tk.N+tk.S+tk.W+tk.E)
        self.imageframe.pack(fill="both", expand=True)
        self.sview=tk.Canvas(self.imageframe, bg='#f00', height=400, width=800)
#        self.sview.grid(sticky=tk.N+tk.S+tk.W+tk.E)#        
        self.sview.pack(fill="both", expand=True)
        
    def setthreshold(self,evt):
        self.analysisthreshold.config(text="Threshold: {}".format(evt))
        if hasattr(self,'wavfilename'):
            self.setThresholdSummary()
        
    def selectAudio (self,evt):
        Audiofile = str(self.audiofiles_lb.get(self.audiofiles_lb.curselection()))
        if Audiofile in self.audiofiles:
            self.loadSpectrogram(Audiofile)
            
    def showparam (self):
        '''
            Prints the height and width of the image window canvas
        Returns
        -------
        None.

        '''
        self.master.update()
        print('Imagesize height {} width {}'.format(self.sview.winfo_height(), self.sview.winfo_width()))
    def getspecsize(self):
        '''
        Calculates the size of the image for matplotlib to produce 

        Returns
        -------
        None.

        '''
        self.master.update()
        return (self.sview.winfo_width(), self.sview.winfo_height())
    
    def client_exit(self):
        self.master.destroy()
        #exit()
        
    def set_AudioFolder(self):
        '''
        Generates a file dialogue to set the audio folder

        Returns
        -------
        None.

        '''
        gafd = tkfd.askdirectory(title="Folder containing Audio files")
        self.audiodirectory = gafd
        self.audiofiles={}
        self.audiofiles_lb.delete(0,"end")
        for file in os.listdir(self.audiodirectory):
            if file.upper()[-4:]=='.WAV':
                self.audiofiles[file[:-4]] ={'audio': file}
                self.audiofiles_lb.insert(tk.END,file[:-4])
        
        print(self.audiodirectory)
        self.lbl_temp.config(text='{} audio files found'.format(len(self.audiofiles)))
        
    def set_AnalysisFolder(self):
        '''
        Generates a file dialogue to set the analysis folder

        Returns
        -------
        None.

        '''
        gafd = tkfd.askdirectory(title="Folder containing batdetect analysis (.csv) output files")
        self.analysisdirectory = gafd
        count = 0
        for file in os.listdir(self.analysisdirectory):
            if file[-4:]=='.csv':
                if file[:-14] in self.audiofiles:
                    self.audiofiles[file[:-14]]['analysis'] = file
                    count += 1
        print(self.analysisdirectory)
        print("{} anlaysis files found and linked".format(count))
        
    def set_SpectrogramSettings():
        '''
        Launches a settings window

        Returns
        -------
        None.

        '''    
    def loadSpectrogram(self, fileroot):
        '''
        Uses a load dialogue to get an audio file, check if spectrogram exists and create if not.
        Produces a spectrogram image
        Overlays boxes for the Batdetect identifications.

        Returns
        -------
        None.
https://stackoverflow.com/questions/8598673/how-to-save-a-pylab-figure-into-in-memory-file-which-can-be-read-into-pil-image
        '''
        if fileroot in self.audiofiles:
            self.loadaudiofile(os.path.join(self.audiodirectory, self.audiofiles[fileroot]['audio']))
            self.displayaudioinfo()
            self.draw_spectrogram()
            self.clear_analysis()
            if 'analysis' in self.audiofiles[fileroot]:
                print('found analysis')
                self.load_analysis(fileroot)
            else:
                self.observations=None
                
            
            
    def loadaudiofile(self, filename):
        '''
        Opens filename as a WAV file and retrieves the relevant information

        Parameters
        ----------
        filename : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        self.wavfilename = filename
        self.wavfile = wave.open(filename)
        self.audioparams=self.wavfile.getparams()
        self.limits=(0, self.audioparams.nframes/self.audioparams.framerate, 0, self.audioparams.framerate/2)
        self.plotlimits = self.limits[:]
        data = self.wavfile.readframes(self.audioparams.nframes)
        self.audio = struct.unpack('{}h'.format(self.audioparams.nframes),data)
        fh = open(self.wavfilename, 'rb')
        head = fh.read(500)
        self.audiocomment = ''
        try: 
            info = head.find(b'INFOICMT')+12
            iart = head.find(b'IART ')
            if info > 12:
                self.audiocomment =head[info:iart].replace(b'\x00', b'').decode('utf-8')
                # add some re here to extract the pertinent information from the comment
        except Exception as e:
            print('Error extracting header', e)
        # create spectrogram
        
        
    def displayaudioinfo(self):
        '''
        Utility method to package audio information for display.

        Returns
        -------
        None.

        '''
        self.lbl_temp.grid_forget()
        self.lbl_filename = tk.Label(self.audioframe, text=self.wavfilename)
        self.lbl_filename.grid(sticky=tk.W+tk.E, column=0, row=0)
        paramtxt = "; ".join(["{}: {}".format(p, getattr(self.audioparams, p)) for p in ('nchannels', 'sampwidth', 'framerate', 'nframes')])
            
        self.lbl_params = tk.Label(self.audioframe, text=paramtxt)
        self.lbl_params.grid(sticky=tk.E+tk.W, column=0, row=1)
        self.lbl_comment = tk.Label(self.audioframe, text=self.audiocomment, wraplength=500, justify=tk.LEFT)
        self.lbl_comment.grid(sticky=tk.E+tk.W, column=0, row=2)
    
    def draw_spectrogram(self):
        #get size for the canvas
        print('foo')
        dims = self.getspecsize()
        fig=plt.figure(dpi=100, figsize=((dims[0]-10)/100, (dims[1]-10)/100))
        ax=fig.add_subplot(1,1,1)
        if hasattr(self, 'specimg'):
            self.sview.delete(self.specimg)
        txt=self.sview.create_text(dims[0]/2, dims[1]/2, text='Generating Spectrogram. Please wait ... ')
        self.sview.pack()

        p,freqs,bins,im = ax.specgram(self.audio, NFFT=1024, Fs=self.audioparams.framerate, noverlap=512)
        print('foobar')
        self.imbounds=im.get_window_extent().extents
        
        ax.set_xlim(self.plotlimits[0],self.plotlimits[1])
        ax.set_ylim(self.plotlimits[2],self.plotlimits[3])
        self.fullrange=im.get_window_extent().extents
        buf = io.BytesIO()
        print('foobar2')
        fig.savefig(buf, format='png')
        buf.seek(0)
        self.specim = Image.open(buf)
        print(self.specim)
        #self.specim.show()
        self.specpim=ImageTk.PhotoImage(self.specim)
        print(self.specpim)
        
        self.specimg =self.sview.create_image(dims[0]//2,dims[1]//2,image=self.specpim)
        print(self.specimg)
        self.sview.delete(txt)
        self.sview.pack()
    
    def clear_analysis(self):
        '''
        Removes all analysis objects from spectrogram

        Returns
        -------
        None.

        '''
        self.sview.delete('analysis')
        self.sview.pack()
        
    def load_analysis(self, fileroot):
        '''
        Loads csv file with output from batdetect and overlays on the spectrogram

        Parameters
        ----------
        fileroot : TYPE
            DESCRIPTION.

        Returns
        -------
        None.

        '''
        print('loading analysis')
        cr = csv.reader(open(os.path.join(app.analysisdirectory, app.audiofiles[fileroot]['analysis']), newline=''))
        header=next(cr)
        dr =csv.DictReader(open(os.path.join(app.analysisdirectory, app.audiofiles[fileroot]['analysis']), newline=''),fieldnames=header)
        next(dr)
        self.observations=[]
        for obs in dr:
            self.observations.append({'start':float(obs['LabelStartTime_Seconds']),'end':float(obs['LabelEndTime_Seconds']),'score':float(obs['DetectorConfidence'])})
        self.setThresholdSummary()
        
    def setThresholdSummary(self):
        if self.observations is not None:
            self.analysissummary.config(text='{} bat calls detected ({} above threshold)'.format(len(self.observations), 
                                                                                                  len([x for x in self.observations if x['score']>=self.thresholdslider.get()])))
        else:
            if hasattr(self, 'wavfilename'):
                self.analysissummary.config(text='No analysis available for {}'.format(self.wavfilename))
            else:
                self.analysissummary.config(text='No soundfile loaded')
    def plot_analysis(self):
        '''
        Plot the observed calls as boxes for those that are above the threshold

        Returns
        -------
        None.

        '''
#if __name__ == "main":
root = tk.Tk() 
app = SpecViewer(root)
app.master.title('Simple Spectrogram viewer')
app.mainloop()