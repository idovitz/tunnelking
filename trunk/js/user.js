var editUserId = 0;
var userArr;
var autostart = "";
var depends;

function getUsers(sort) {
	var d = loadJSONDoc("/um/getUserNames", {sort:sort});
	d.addCallbacks(onGetUserNames, onFault);
}

function onGetUserNames(res) {
	var users = res["result"];
	userArr = users;
	
	drawUsers(users, "");
}

function drawUsers(users, filter) {
	var uDiv = document.getElementById("userDiv");
	
	html = "";
	for(i in users) {
		if(filter == "" || users[i]["name"].search(filter) != -1) {
			if(users[i]["lastlogin"]){
				var lastlogintext = 'last login: '+users[i]["lastlogin"];
			}else{
				var lastlogintext = 'never logged in';
			}
			html += '<div id="userDiv_'+users[i]["id"]+'" class="userDiv">'+
						'<div class="userNameDiv">'+users[i]["name"]+'</div>' +
						'<div class="userControlDiv">' +
							'<img src="img/apps.png" onclick="displayAppsDiv('+users[i]["id"]+');" />' +
							'<img src="img/userdownload.png" onclick="userGet('+users[i]["id"]+');" />' +
							'<img src="img/useredit.png" onclick="getUserType('+users[i]["id"]+');" />' +
							'<img src="img/userdelete.png" onclick="userDelete('+users[i]["id"]+');" />' +
							'<img src="img/info.png" onclick="userAppInfo('+users[i]["id"]+');" />' +
						'</div>'+
						'<div class="userLastLoginDiv">'+lastlogintext+' | expires on '+users[i]["expiredate"]+'</div>' +
					'</div>';
		}
	}
	
	uDiv.innerHTML = html;
}

function filterUsers() {
	var filter = document.getElementById("userSearchField").value;
	
	drawUsers(userArr, filter);
}

function getUserType(id) {
	if(id){
		var d = loadJSONDoc("/cm/getUserType", {id:id});
		d.addCallbacks(onGetUserTypeEdit, onFault);
	}else{
		var d = loadJSONDoc("/cm/getUserType");
		d.addCallbacks(onGetUserType, onFault);
	}
}

function onGetUserType(res) {
	if(res["result"]["ldap"] == "True" || res["result"]["ldap"] == true){
		MochiKit.Visual.appear('addLdapDiv');
	}else{
		MochiKit.Visual.appear('addDiv');
	}
}

function displayAddUserDiv(name) {
	var addDiv = document.getElementById(name);
	
	document.getElementById("addForm").reset();
	document.getElementById("addLdapForm").reset();
	
	if(addDiv.style.display == "inline"){
		MochiKit.Visual.slideUp(name);
//		addDiv.style.display = "none";
	}else{
		MochiKit.Visual.slideDown(name);
//		addDiv.style.display = "inline";
	}
}

function ldapSearch(){
	var value = document.getElementById("searchName").value;
	
	if(value.length > 2){
		var d = loadJSONDoc("/cm/searchLdapUsers", {str:value});
		d.addCallbacks(onSearchLdapUsers, onFault);
	}
}

function onSearchLdapUsers(res){
	var select = document.getElementById("userSelect");
	select.innerHTML = "";
	var users = res["result"];
	
	for(i in users){
		var name = ""+users[i][1]['sAMAccountName'][0];
		appendChildNodes(select, OPTION(null, name.toLowerCase()));
	}
}

function onGetUserTypeEdit(res){
	document.getElementById("editDiv").style.display = "inline";
	document.getElementById("editForm").reset();
	
	if(res["result"]["ldap"] == "True" || res["result"]["ldap"] == true){
		document.getElementById("passwordTR").style.display = "none";
		document.getElementById("passwordTR2").style.display = "none";
	}else{
		document.getElementById("passwordTR").style.display = "table-row";
		document.getElementById("passwordTR2").style.display = "table-row";
	}
	
	var d = loadJSONDoc("/um/getUserInfo", {id:res["result"]["id"]});
	d.addCallbacks(onGetUserInfo, onFault);
}

function onGetUserInfo(res) {
	var userArr = res["result"];
	editUserId = userArr["id"];
	
	document.getElementById("userEditName").innerHTML = "<b>"+userArr["name"]+"</b>";
	
	document.getElementById("userLocalEditTestDriverCheck").checked = (parseInt(userArr["testdriver"]) == 1);
	
	document.getElementById("userLocalEditPinCheck").checked = userArr["keypin"];
	showTR(['pincodeEditTR', 'pincodeEditTR2'], 'userLocalEditPinCheck');
	
	document.getElementById("userLocalEditOTPCheck").checked = (userArr["otpRecipient"] != "");
	showTR(['otpEditTR'], 'userLocalEditOTPCheck');
	document.getElementById("otpEditRecipient").value = userArr["otpRecipient"];
}

function showTR(sElementNames, cBoxName) {
	var cBox = document.getElementById(cBoxName);
	
	for(sElementName in sElementNames) {
		var sElement = document.getElementById(sElementNames[sElementName]);
		
		if(cBox.checked == false){
			sElement.style.display = "none";
		}else{
			sElement.style.display = "table-row";
		}
	}
	
}

function saveUser() {
	var editDiv = document.getElementById("editDiv");
	
	var formdata = {};
	
	if(document.getElementById("userLocalEditTestDriverCheck").checked)
	{
		formdata['testdriver'] = 1;
	}else{
		formdata['testdriver'] = 0;
	}
	
	if(document.getElementById("userLocalEditPinCheck").checked)
		formdata['keypin'] = document.getElementById("userEditKeyPin").value;
	
	formdata['password'] = document.getElementById("userEditPass").value;
	
	if(document.getElementById("userLocalEditOTPCheck").checked)
		formdata['otpRecipient'] = document.getElementById("otpEditRecipient").value;
	
	var checkFields = ["userEditKeyPin", "userEditPass"];
	
	if(checkPassFields(checkFields, 'editDiv')){
		editDiv.style.display = "none";
		document.getElementById("editForm").reset();
		
		var d = loadJSONDoc("/um/saveUser", {id:editUserId, formdata:serializeJSON(formdata)});
		d.addCallbacks(onSaveUser, onFault);
	}
}

function onSaveUser() {
	
}

function addUser(formname) {
	if(formname == "addForm"){
		var addDiv = document.getElementById("addDiv");
		
		if(document.getElementById("userLocalAddTestDriverCheck").checked)
		{
			var testdriverValue = 1;
		}else{
			var testdriverValue = 0;
		}
		
		var formdata = {
			name: document.getElementById("userAddName").value,
			keypin: document.getElementById("userAddKeyPin").value,
			password: document.getElementById("userAddPass").value,
			otpRecipient: document.getElementById("otpLocalRecipient").value,
			testdriver: testdriverValue
		}
		
		var checkFields = ["userAddKeyPin", "userAddPass"];
	}else{
		var addDiv = document.getElementById("addLdapDiv");
		
		if(document.getElementById("userAddTestDriverCheck").checked)
		{
			var testdriverValue = 1;
		}else{
			var testdriverValue = 0;
		}
		
		var formdata = {
			name: document.getElementById("userSelect").value,
			keypin: document.getElementById("userAddLdapKeyPin").value,
			otpRecipient: document.getElementById("otpLdapRecipient").value,
			testdriver: testdriverValue
		}
		var checkFields = ["userAddLdapKeyPin"];
	}
	
	if(checkPassFields(checkFields, addDiv)){
		addDiv.style.display = "none";
		document.getElementById(formname).reset();
		document.getElementById("userSelect").innerHTML = "";
		
		if(formdata.name != "")
		{
			var d = loadJSONDoc("/um/addUser", {formdata:serializeJSON(formdata)});
			d.addCallbacks(onAddUser, onFault);
		}
	}
}

function checkPassFields(passfields, divname){
	var rs = true;
	
	for(p in passfields){
		if(document.getElementById(passfields[p]).value != document.getElementById(passfields[p]+"2").value){
			rs = false;
			document.getElementById(passfields[p]).style.border = "2px solid red";
			document.getElementById(passfields[p]+"2").style.border = "2px solid red";
			MochiKit.Visual.pulsate(passfields[p], {pulses:4});
			MochiKit.Visual.pulsate(passfields[p]+"2", {pulses:4});
		}else{
			document.getElementById(passfields[p]).style.border = "";
			document.getElementById(passfields[p]+"2").style.border = "";
		}
		
	}
	
	return rs;
}

function onAddUser(res){
	getUsers();
	document.getElementById("addForm").reset();
	document.getElementById("addDiv").style.display = "none";
}

function userDelete(id) {
	if(confirm("Really delete this user?")) {
		var d = loadJSONDoc("/um/delUser", {id:id});
		d.addCallbacks(onUserDelete, onFault);
	}
}

function onUserDelete(res) {
	getUsers();
}

function userGet(id) {
	var d = loadJSONDoc("/um/getUserPackage", {id:id});
	d.addCallbacks(onUserGet, onFault);
}

function onUserGet(res) {
	window.open(res["result"],'Download'); 
}

function displayAppsDiv(userid) {
	editUserId = userid;
	var appsDiv = document.getElementById("appsDiv");
	
	if(appsDiv.style.display == "inline"){
		appsDiv.style.display = "none";
	}else{
		appsDiv.style.display = "inline";
	}
	
	var d = loadJSONDoc("/um/getUserApps", {id:userid});
	d.addCallbacks(onGetUserApps, onFault);
}

function onGetUserApps(res) {
	var asel = document.getElementById("availApps");
	var usel = document.getElementById("userApps");
	autostart = res["result"]["autostart"];
	depends = res["result"]["depends"];
	
	asel.innerHTML = "";
	var apps = res["result"]["availapps"];
	
	for(i in apps){
		appendChildNodes(asel, OPTION(null, apps[i]));
	}
	
	usel.innerHTML = "";
	var apps = res["result"]["userapps"];
	
	for(i in apps){
		appendChildNodes(usel, OPTION(null, apps[i]));
	}
	
	var astart = document.getElementById("autostartInput");
	astart.checked = false;
}

function checkAutoStart() {
	var usel = document.getElementById("userApps");
	var astart = document.getElementById("autostartInput");
	
	if(usel.value == autostart){
		astart.checked = true;
	}else{
		astart.checked = false;
	}
}

function changeAutostart(){
	var usel = document.getElementById("userApps");
	var astart = document.getElementById("autostartInput");
	
	if(astart.checked == false){
		autostart = "";
	}else{
		autostart = usel.value;
	}
}

function inOptions(options, value) {
	for(var i=0; i<options.length; i++){
		if(options[i].text == value) {
			return true;
		}
	}
	return false;
}

function addApp() {
	var asel = document.getElementById("availApps");
	var usel = document.getElementById("userApps");
	
	if(asel.value != undefined){
		var avalue = asel.options[asel.selectedIndex].value;
				
		if(!inOptions(usel.options, avalue)) {
			appendChildNodes(usel, OPTION(null, avalue));
		}
		
		for(var i=0; i<asel.options.length; i++){
			if(asel.options[i].value == asel.value){
				asel.remove(i);
				break;
			}
		}
		
		if(depends[avalue]){
			if(!inOptions(usel.options, depends[avalue])) {
				appendChildNodes(usel, OPTION(null, depends[avalue]));
				
				for(var i=0; i<asel.options.length; i++){
					if(asel.options[i].value == depends[avalue]){
						asel.remove(i);
						break;
					}
				}
			}
		}
	}
}

function delApp() {
	var asel = document.getElementById("availApps");
	var usel = document.getElementById("userApps");
	var uvalue = usel.value;
	
	if(uvalue != undefined ){
		if(!inOptions(asel.options, uvalue)) {
			appendChildNodes(asel, OPTION(null, uvalue));
		}
		
		for(var i=0; i<usel.options.length; i++){
			if(usel.options[i].value == uvalue){
				usel.remove(i);
				break;
			}
		}
	}
	
	for(key in depends){
		if(depends[key] == uvalue){
			for(var i=0; i<usel.options.length; i++){
				if(usel.options[i].value == key){
					usel.remove(i);
					
					if(!inOptions(asel.options, key)) {
						appendChildNodes(asel, OPTION(null, key));
					}
					
					break;
				}
			}
		}
	}
}

function saveApps() {
	
	var usel = document.getElementById("userApps");
	var apps = {'names':[]};
	
	for(var i=0; i<usel.options.length; i++){
		apps['names'].push(usel.options[i].text);
	}
	
	var d = loadJSONDoc("/um/saveUserApps", {id:editUserId, apps:serializeJSON(apps), autostart:autostart});
	d.addCallbacks(onSaveApps, onFault);
}

function onSaveApps(res){
	var appsDiv = document.getElementById("appsDiv");
	
	appsDiv.style.display = "none";
}

function userAppInfo(id){
	var d = loadJSONDoc("/um/getUserAppInfo", {id:id});
	d.addCallbacks(onUserAppInfo, onFault);
}

function onUserAppInfo(res){
	var userInfoNameDiv = document.getElementById("userInfoNameDiv");
	var appVersionsDiv = document.getElementById("appVersionsDiv");
	var userExpiresDiv = document.getElementById("userExpiresDiv");
	MochiKit.Visual.appear("infoDiv");
	
	userInfoNameDiv.innerHTML = res["result"]["name"];
	
	var versions = res["result"]["appversions"]
	
	var html = "<table style='border: 1px solid;'><th>app</th><th>version</th>";
	for(appname in versions){
		html += "<tr><td>"+appname+"</td><td style='text-align: center;'>"+versions[appname]+"</td></tr>";
	}
	html += "</table>";
	
	appVersionsDiv.innerHTML = html;
	
	
	var html = "certificate expires on "+res["result"]["expiredate"];
	userExpiresDiv.innerHTML = html;
}

function closeInfo(){
	MochiKit.Visual.fade("infoDiv");
}

function onFault(error) {
	console.log(error);
}
