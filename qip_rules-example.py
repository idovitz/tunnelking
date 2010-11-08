# IMPORTANT !
# Rename to qip_rules and set rights for this file to 600 for root!
# > chmod 700 <file>

rules = {
	"__base__":[
				{'dest':'x.x.x.x', 'proto':'udp', 'sport':None, 'dport':'53'},
				{'dest':'x.x.x.x', 'proto':'tcp', 'sport':None, 'dport':'53'}
	],
	"intranet":[
				{'dest':'x.x.x.x', 'proto':'tcp', 'sport':None, 'dport':'80'}
	],
	"full_access":[
				{'dest':None, 'proto':None, 'sport':None, 'dport':None},
				{'dest':None, 'proto':None, 'sport':None, 'dport':None}
	]
}