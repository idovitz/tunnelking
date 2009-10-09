import wx, time, urllib, sys, os, pickle, tarfile, subprocess, socket, traceback

socket.setdefaulttimeout(10)

class Updater:
	def __init__(self, ip, appname, version, gauge, procentLabel, tmpdir=""):
		self.gauge = gauge
		self.label = procentLabel
		url = "https://%s:8080/apps/%s/%s.tar.bz2" % (ip, appname, version)
		
		urllib.urlretrieve(url, "%s%s.tar.bz2" % (tmpdir, appname), self.reporthook)
	
	def reporthook(self, blocks, blocksize, filesize):
		if filesize > blocksize:
			size = blocks*blocksize
			done = float(size)/float(filesize)
			pos = int(done*1000)
		else:
			pos = 1000
			
		self.gauge.SetValue(pos)
		self.label.SetLabel("%s%%" % (pos/10))
		self.gauge.GetParent().GetParent().app.Yield()

class UserInfo:
	def get(self, ip, id):
		try:
			return self.getInfo(ip, id)
		except Exception, e:
			return self.get(ip, id)
	
	def getInfo(self, ip, id):
		url = "https://%s:8080/getuserini?id=%s" % (ip, id)
		f = urllib.urlopen(url)
		output = pickle.loads(f.read())
		f.close()
		return output
		
class Uzip:
	def __init__(self, gauge, statusLabel, percentLabel):
		self.gauge = gauge
		self.statusLabel = statusLabel
		self.percentLabel = percentLabel
		
	def extract(self, filepath, path):
		try:
			zf = tarfile.open(filepath, "r:bz2")
			names = zf.getnames()
			total = len(names)
			self.gauge.SetRange(total)
			self.gauge.SetValue(0)
		except Exception, e:
			print "open bzip", type(e), e
		
		try:
			i = 0
			for filename in names:
				i += 1
				zf.extract(filename, path)
				self.gauge.SetValue(i)
				self.gauge.GetParent().GetParent().app.Yield()
				self.percentLabel.SetLabel("%s files done" % i)
			zf.close()
		except Exception, e:
			print "extract bzip", type(e), e
		
class AppInfo:
	def __init__(self, appname, tmpdir=""):
		self.appname = appname
		self.tmpdir = tmpdir
	
	def getstarter(self):
		base = "%s\..\..\..\.."  % sys.path[0]
		filepath = "%s\\%s\\_start_" % (base, self.appname)
		f = open(filepath, "r")
		starter = f.readlines()[0].strip()
		return starter
	
	def getversion(self):
		try:
			base = "%s\..\..\..\.."  % sys.path[0]
			filepath = "%s\\%s\\_version_" % (base, self.appname)
			f = open(filepath, "r")
			version = f.readlines()[0].strip()
		except:
			version = -1
		return version
	
	def install(self, uzip):
		try:
			base = "%s\..\..\..\.."  % sys.path[0]
			path = "%s\\%s\\" % (base, self.appname)
			filepath = "%s%s.tar.bz2" % (self.tmpdir, self.appname)
			uzip.extract(filepath, path)
			os.remove(filepath)
		except Exception, e:
			return False

class SmsDialog(wx.Frame):
	def __init__(self, parent, ip, id, gauge, procentLabel, statusLabel):
		self.gauge = gauge
		self.label = procentLabel
		self.statusLabel = statusLabel
		self.procentLabel = procentLabel
		self.ip = ip
		self.id = id
		wx.Frame.__init__(self, parent=parent, title="sms code", style=wx.FRAME_NO_TASKBAR | wx.CAPTION)
		
		self.smsPanel = wx.Panel(self, -1, name="smssen")
		vBox = wx.BoxSizer(wx.VERTICAL)
		vBox.Add(self.smsPanel, 1, wx.EXPAND | wx.ALL, 10)
		self.SetSizer(vBox)
		
		self.SetBackgroundColour(self.smsPanel.GetBackgroundColour())
		
		smsGridSizer = wx.GridBagSizer(hgap=20, vgap=20)
		self.smsPanel.SetSizer(smsGridSizer)
		
		self.stLabel = wx.StaticText(parent=self.smsPanel, label="vul de sms code in en klik op check")
		smsGridSizer.Add(self.stLabel, border=2, pos=(0,0), span=(1,3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
		
		smsLabel = wx.StaticText(parent=self.smsPanel, label="sms code")
		smsGridSizer.Add(smsLabel, pos=(1,0), flag=wx.ALIGN_CENTER_HORIZONTAL | wx.ALIGN_CENTER_VERTICAL, border=10)
		
		self.smsInput = wx.TextCtrl(parent=self.smsPanel)
		smsGridSizer.Add(self.smsInput, pos=(1,1), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
		self.smsInput.Bind(wx.EVT_KEY_UP, self.keyUp)
		
		smsCheckButton = wx.Button(parent=self.smsPanel, label="check")
		smsCheckButton.Bind(wx.EVT_BUTTON, self.checkSMS)
		smsGridSizer.Add(smsCheckButton, pos=(1,2), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL)
		
		f = wx.Font(10, wx.FONTFAMILY_DEFAULT, wx.NORMAL, wx.NORMAL, underline=True)
		
		self.newSmsLabel = wx.StaticText(parent=self.smsPanel, label="nieuwe sms")
		self.newSmsLabel.SetFont(f)
		smsGridSizer.Add(self.newSmsLabel, border=2, pos=(2,0), span=(1,3), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT)
		self.newSmsLabel.Bind(wx.EVT_LEFT_UP, self.newSms)
		
		self.smsPanel.Fit()
		self.Fit()
	
	def keyUp(self, event):
		if event.GetKeyCode() == 13:
			self.checkSMS(event)
	
	def checkSMS(self, event):
		self.statusLabel.SetLabel("checking key..")
		self.GetParent().app.Yield()
		try:
			url = "https://%s:8080/checkOTPKey?key=%s&id=%s" % (self.ip, self.smsInput.GetValue(), self.id)
			self.gauge.SetValue(0)
			self.procentLabel.SetLabel("0%")
			f = urllib.urlopen(url)
			output = pickle.loads(f.read())
			
			self.gauge.SetValue(1000)
			self.procentLabel.SetLabel("100%")
			
			f.close()
			
			if output:
				self.Close()
				self.GetParent().handleApps()
			else:
				self.stLabel.SetLabel("de smscode is niet juist")
				self.stLabel.SetForegroundColour(wx.Colour(255,0,0))
				self.smsInput.SetValue("")
			
		except Exception, e:
			print type(e), e
			sys.exit(1)
			
	def newSms(self, event):
		self.newSmsLabel.Disable()
		self.newSmsLabel.Hide()
		
		self.timer = wx.Timer(self, 100)
		self.timer.Start(10000)
		self.Bind(wx.EVT_TIMER, self.showNew)
		
		try:
			url = "https://%s:8080/newSms?id=%s" % (self.ip, self.id)
			f = urllib.urlopen(url)
			output = pickle.loads(f.read())
			f.close()
			
			if output:
				dlg = wx.MessageDialog(None, "Nieuwe sms is verstuurd.", 'SMS', wx.ICON_INFORMATION)
				dlg.ShowModal()
			else:
				dlg = wx.MessageDialog(None, "Er ging iets fout met het versturen van de sms", 'SMS', wx.ICON_ERROR)
				dlg.ShowModal()
		except Exception, e:
			traceback.print_exc()
			sys.exit(1)

	def showNew(self, event):
		self.newSmsLabel.Enable()
		self.newSmsLabel.Show()

class MainWindow(wx.Frame):
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, size=(300,100), style=wx.FRAME_NO_TASKBAR | wx.CAPTION)
		self.mainPanel = wx.Panel(self, -1)
		
		vBox = wx.BoxSizer(wx.VERTICAL)
		vBox.Add(self.mainPanel, 1, wx.EXPAND | wx.ALL, 10)
		self.SetSizer(vBox)
		
		self.SetBackgroundColour(self.mainPanel.GetBackgroundColour())
				
		self.gauge = wx.Gauge(parent=self.mainPanel, range=1000, pos=(10, 30), size=(200, 15))
		self.label = wx.StaticText(parent=self.mainPanel, label="0%", pos=(220, 30))
		
		statusText = wx.StaticText(parent=self.mainPanel, label="status:", pos=(10, 10))
		self.statusLabel = wx.StaticText(parent=self.mainPanel, label="", pos=(60, 10))
		
		self.Bind(wx.EVT_CLOSE, self.closeWindow)
		self.Show(True)
	
	def init(self):
		self.statusLabel.SetLabel("downloading user information")
		self.ip, self.id = sys.argv[1], sys.argv[2]
		self.app.Yield()
		time.sleep(0.1)
		keyisnotchecked = False
		
		userinfo = UserInfo()
		initdict = userinfo.get(self.ip, self.id)
#		print initdict
		self.gauge.SetValue(1000)
		self.label.SetLabel("100%")
		
		self.apps = initdict["apps"]
		
		if initdict["getSms"]:
			self.smsDialog = SmsDialog(self, self.ip, self.id, self.gauge, self.label, self.statusLabel)
			
			keyisnotchecked = True
			self.smsDialog.Show()
		else:
			self.handleApps()
	
	def handleApps(self):
		starter = False
		for app in self.apps:
			appinf = AppInfo(app["appname"], "..\\")
			myversion = appinf.getversion()
			
			if myversion != app["currentversion"]:
				if myversion == -1:
					self.statusLabel.SetLabel("downloading %s" % app["appname"])
					upd = Updater(self.ip, app["appname"], app["currentversion"], self.gauge, self.label, "..\\")
					self.statusLabel.SetLabel("installing %s" % app["appname"])
					uzip = Uzip(self.gauge, self.statusLabel, self.label)
					appinf.install(uzip)
				elif int(myversion) < int(app["currentversion"]):
					self.statusLabel.SetLabel("downloading new %s" % app["appname"])
					upd = Updater(self.ip, app["appname"], app["currentversion"], self.gauge, self.label, "..\\")
					self.statusLabel.SetLabel("updating %s" % app["appname"])
					uzip = Uzip(self.gauge, self.statusLabel, self.label)
					appinf.install(uzip)
		
			if app["autostart"] == 1:
				try:
					self.statusLabel.SetLabel("start %s" % app["appname"])
					starter = appinf.getstarter()
				except Exception, e:
					starter = False
			
		if starter:
			try:
				subprocess.call([starter], shell=True)
			except Exception, e:
				s = False
		
		sys.exit()
	
	def closeWindow(self, event):
#		self.Destroy()
		sys.exit()
				
	def setApp(self, app):
		self.app = app
		
class MyApp(wx.App):
	def OnInit(self):
		frame = MainWindow(None, wx.ID_ANY, 'Tunnelking updater')
		frame.setApp(self)
		self.SetTopWindow(frame)
		frame.init()
		return True

app = MyApp(False, "log.txt")
app.MainLoop()