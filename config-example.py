
# global
basemap = "/opt/tunnelking/"
logging = 1

# SMS
#smsHandler = "curl"
#smsOptions = {
#				"url":"http://sms.gateway.example.com/send.php",
#				"data":"userid=sdfs&passw=sdfsd&gsm=%number&text=%msg&sender=tunnelking"
#			}

smsHandler = "mail"
smsOptions = {
				"smtphost":"localhost",
				"recipient":"%number",
				"sender":"tunnelking@example.com",
				"msg":"SUBJECT: Tunnelking key\n%msg"
			}

# DATABASE
databaseUserName = "tunnelking"
databasePassword = "dsfdfsfgsdfdsfd"
databaseName = "tunnelking"

iptPath= "/sbin/iptables"