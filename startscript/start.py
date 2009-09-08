import wx, time, urllib, sys, os, pickle, tarfile, subprocess, socket

socket.setdefaulttimeout(30)

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
		self.gauge.GetParent().app.Yield()

class UserInfo:
	def get(self, ip, id):
		try:
			url = "https://%s:8080/getuserini?id=%s" % (ip, id)
			time.sleep(2)
			f = urllib.urlopen(url)
			output = pickle.loads(f.read())
			f.close()
			return output
		except Exception, e:
			return False
		
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
				self.gauge.GetParent().app.Yield()
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


class MainWindow(wx.Frame):
	""" We simply derive a new class of Frame. """
	def __init__(self, parent, id, title):
		wx.Frame.__init__(self, parent, id, title, size=(300,120))
		#self.SetBackgroundStyle(wx.BG_STYLE_SYSTEM)
		self.SetBackgroundColour(wx.Colour(255,255,255))
				
		self.gauge = wx.Gauge(parent=self, range=1000, pos=(10, 30), size=(200, 15))
		self.label = wx.StaticText(parent=self, label="0%", pos=(220, 30))
		
		statusText = wx.StaticText(parent=self, label="status:", pos=(10, 10))
		self.statusLabel = wx.StaticText(parent=self, label="", pos=(60, 10))
		
		self.Bind(wx.EVT_CLOSE, self.closeWindow)
		self.Show(True)
	
	def init(self):
		self.statusLabel.SetLabel("downloading user information")
		ip, id = sys.argv[1], sys.argv[2]
		self.app.Yield()
		time.sleep(0.1)
		
		userinfo = UserInfo()
		apps = userinfo.get(ip, id)
		self.gauge.SetValue(1000)
		self.label.SetLabel("100%")
		
		starter = False
		for app in apps:
			appinf = AppInfo(app["appname"], "..\\")
			myversion = appinf.getversion()
			
			if myversion != app["currentversion"]:
				if myversion == -1:
					self.statusLabel.SetLabel("downloading %s" % app["appname"])
					upd = Updater(ip, app["appname"], app["currentversion"], self.gauge, self.label, "..\\")
					self.statusLabel.SetLabel("installing %s" % app["appname"])
					uzip = Uzip(self.gauge, self.statusLabel, self.label)
					appinf.install(uzip)
				elif int(myversion) < int(app["currentversion"]):
					self.statusLabel.SetLabel("downloading new %s" % app["appname"])
					upd = Updater(ip, app["appname"], app["currentversion"], self.gauge, self.label, "..\\")
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

app = MyApp()
app.MainLoop()