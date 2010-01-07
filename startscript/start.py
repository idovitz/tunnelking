import wx, time, urllib, sys, os, pickle, tarfile, subprocess, socket, traceback, tempfile, shutil
import win32api, win32pdhutil, win32con
from distutils import dir_util
from optparse import OptionParser

socket.setdefaulttimeout(10)

class Updater:
	def __init__(self, ip, appname, version, gauge, procentLabel):
		self.gauge = gauge
		self.label = procentLabel
		url = "https://%s:8080/apps/%s/%s.tar.bz2" % (ip, appname, version)
		
		self.gauge.SetValue(0)
		self.gauge.SetRange(1000)
		urllib.urlretrieve(url, "%s\\%s.tar.bz2" % (tempfile.gettempdir(), appname), self.reporthook)
	
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
		self.ip = ip
		self.id = id		
		
		return self.getInfo(ip, id)
	
	def getInfo(self, ip, id):
		url = "https://%s:8080/getuserini?id=%s" % (ip, id)
		print "url"+url
		f = urllib.urlopen(url)
		output = pickle.loads(f.read())
		print output
		f.close()
		return output
	
	def putversions(self, versions):
		url = "https://%s:8080/putversions?id=%s&versions=%s" % (self.ip, self.id, urllib.quote(pickle.dumps(versions)))
		print "url"+url
		f = urllib.urlopen(url)
		f.close()
		return 1
		
class Uzip:
	def __init__(self, gauge, statusLabel, percentLabel):
		self.gauge = gauge
		self.statusLabel = statusLabel
		self.percentLabel = percentLabel
		
	def extract(self, filepath, path, filter=None):
		try:
			zf = tarfile.open(filepath, "r:bz2")
			names = zf.getnames()
			
			if filter != None:
				names = self.filternames(names, filter)
			
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
	
	def filternames(self, names, filter):
		newnames = []
		for name in names:
			if filter in name:
				newnames.append(name)
		
		return newnames
			
class AppInfo:
	def __init__(self, appname):
		self.appname = appname
	
	def getstarter(self):
		base = "%s\..\..\..\.."  % sys.path[0]
		filepath = "%s\\%s\\_start_" % (base, self.appname)
		f = open(filepath, "r")
		starter = f.readlines()[0].strip()
		return starter
	
	def getversion(self):
		try:
			base = "%s\..\..\..\.."  % sys.path[0]
			
			if self.appname != "__base__":
				filepath = "%s\\%s\\_version_" % (base, self.appname)
			else:
				filepath = "%s\\..\\_version_" % (base)
			f = open(filepath, "r")
			version = f.readlines()[0].strip()
		except:
			version = -1
		return version
	
	def install(self, uzip):
		try:
			# unpack and remove bzip
			base = "%s\..\..\..\.."  % sys.path[0]
			path = "%s\\%s\\" % (base, self.appname)
			filepath = "%s\\%s.tar.bz2" % (tempfile.gettempdir(), self.appname)
			uzip.extract(filepath, path)
			os.remove(filepath)
		except Exception, e:
			return False
	
	def installBase(self, uzip, stickpath):
		try:
			# unpack and remove bzip
			filepath = "%s\\%s.tar.bz2" % (tempfile.gettempdir(), self.appname)
			uzip.extract(filepath, stickpath)
			os.remove(filepath)
		except Exception, e:
			return False
			
	def installStarter(self, uzip):
		try:
			base = tempfile.gettempdir()
			path = "%s\\%s\\" % (base, self.appname)
			filepath = "%s\\%s.tar.bz2" % (base, self.appname)
			startpath = "%s\\%s\\PortableApps\\OpenVPNPortable\\data\\start" % (base, self.appname)
		
			# try to remove tmp dirs
			try:
				shutil.rmtree(path)
			except:
				print "remove failed"
		
			# Unpack and remove bzip
			uzip.extract(filepath, path, "PortableApps/OpenVPNPortable/data/start/")
			
			return startpath
			
		except Exception, e:
			print "installStarter failed: %s (%s)" % (type(e), e)
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
		print "Frame __init__"
		wx.Frame.__init__(self, parent, id, title, size=(300,100), style=wx.RESIZE_BORDER | wx.SYSTEM_MENU | wx.CAPTION |	 wx.CLOSE_BOX)
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
		# options
		parser = OptionParser()
		parser.add_option("--mo", dest="mode", help="updater | baseupdate", metavar="MODE")
		parser.add_option("--id", dest="id", help="userid in tunnelking", metavar="USERID")
		parser.add_option("--ip", dest="ip", help="ip address via tunnel", metavar="IP")
		parser.add_option("--sp", dest="stickpath", help="path stick (g:)", metavar="PATH")
		
		(options, args) = parser.parse_args()
		print options
		
		#self.ip = options.ip
		self.ip = os.environ["ROUTE_VPN_GATEWAY"]
		self.id = options.id
	
		if options.mode == "updater":
			self.statusLabel.SetLabel("downloading user information")
			self.app.Yield()
			
			time.sleep(4)
			self.app.Yield()
			
			keyisnotchecked = False
			
			self.userinfo = UserInfo()
			try:
				initdict = self.userinfo.get(self.ip, self.id)
			except:
				try:
					self.statusLabel.SetLabel("downloading user information 2")
					initdict = self.userinfo.get(self.ip, self.id)
				except Exception, e:
					print "second time failed: %s (%s)" % (type(e), e)
					self.killProcess("openvpn.exe")
					sys.exit(1)
			
			
			self.gauge.SetValue(1000)
			self.label.SetLabel("100%")
			
			self.apps = initdict["apps"]
			
			if initdict["getSms"]:
				self.smsDialog = SmsDialog(self, self.ip, self.id, self.gauge, self.label, self.statusLabel)
				
				keyisnotchecked = True
				self.smsDialog.Show()
			else:
				self.handleApps()
		elif options.mode == "baseupdate":
			self.killProcess("openvpn.exe")
			self.killProcess("openvpn-gui.exe")
			self.killProcess("OpenVPNPortable.exe")
			self.killProcess("PortableAppsPlatform.exe")
			
			self.statusLabel.SetLabel("update base software")
			self.app.Yield()
			time.sleep(2)
			
			appinf = AppInfo("__base__")
			uzip = Uzip(self.gauge, self.statusLabel, self.label)
			tmpstartdir = appinf.installBase(uzip, options.stickpath)
			
			subprocess.call(["start /B %sStartPortableApps.exe" % options.stickpath], shell=True)
			
			sys.exit(0)
			
	def killProcess(self, processname):
		from win32com.client import GetObject
		WMI = GetObject('winmgmts:')
		processes = WMI.InstancesOf('Win32_Process')
		process_list = [(p.Properties_("ProcessID").Value, p.Properties_("Name").Value) for p in processes]
		
		for pr in process_list:
			if pr[1] == processname:
				handle = win32api.OpenProcess( win32con.PROCESS_TERMINATE, 0, pr[0])
				win32api.TerminateProcess(handle, 0)
				win32api.CloseHandle(handle)
				
		print "killed %s" % processname
	
	def handleApps(self):
		starter = ""
		versions = {}
		
		for app in self.apps:
			print "handleApps app %s" % app
			appinf = AppInfo(app["appname"])
			myversion = appinf.getversion()
			
			if app["appname"] != "__base__" :
				if myversion == -1:
					self.statusLabel.SetLabel("downloading %s" % app["appname"])
					upd = Updater(self.ip, app["appname"], app["currentversion"], self.gauge, self.label)
					self.statusLabel.SetLabel("installing %s" % app["appname"])
					uzip = Uzip(self.gauge, self.statusLabel, self.label)
					appinf.install(uzip)
				elif int(myversion) < int(app["currentversion"]):
					self.statusLabel.SetLabel("downloading new %s" % app["appname"])
					upd = Updater(self.ip, app["appname"], app["currentversion"], self.gauge, self.label)
					self.statusLabel.SetLabel("updating %s" % app["appname"])
					uzip = Uzip(self.gauge, self.statusLabel, self.label)
					appinf.install(uzip)
			else:
				if int(myversion) < int(app["currentversion"]):
					ret = wx.MessageBox("Wilt u tunnelking upgraden?", "Base upgrade", wx.YES_NO | wx.ICON_QUESTION)
					print "%s == %s" % (ret, wx.ID_YES)
					if ret == wx.YES:
						self.statusLabel.SetLabel("downloading new base")
						upd = Updater(self.ip, app["appname"], app["currentversion"], self.gauge, self.label)
						self.statusLabel.SetLabel("extracting new updater")
						uzip = Uzip(self.gauge, self.statusLabel, self.label)
						tmpstartdir = appinf.installStarter(uzip)
						stickpath = "%s:\\" % sys.path[0].split(":")[0]
						print time.localtime()
						startapp = app["appname"]
						starter = "start /B %s\\start.exe --ip %s --id %s --mo baseupdate --sp %s" % (tmpstartdir, self.ip, self.id, stickpath)
						print time.localtime()
						print starter
			
			versions[app["appname"]] = appinf.getversion()
		
			if app["autostart"] == 1 and "start /B" not in starter:
				try:
					startapp = app["appname"]
					starter = appinf.getstarter()
				except Exception, e:
					starter = False
		
		self.userinfo.putversions(versions)
			
		if starter:
			try:
				self.statusLabel.SetLabel("start %s" % startapp)
				subprocess.call([starter], shell=True)
			except Exception, e:
				s = False
		
		sys.exit(0)
	
	def closeWindow(self, event):
#		self.Destroy()
		self.killProcess("openvpn.exe")
		sys.exit()
				
	def setApp(self, app):
		self.app = app
		
class MyApp(wx.App):
	def OnInit(self):
		print "App onInit"
		frame = MainWindow(None, wx.ID_ANY, 'Tunnelking updater')
		frame.setApp(self)
		self.SetTopWindow(frame)
		frame.init()
		return True

f = open("..\\log.txt", "w")
sys.stdout = f
sys.stderr = f

app = MyApp(False)
app.MainLoop()
f.close()