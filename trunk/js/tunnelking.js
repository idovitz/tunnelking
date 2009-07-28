
function getConfigNames() {
	var d = loadJSONDoc("/cm/getConfigurationNames");
	d.addCallbacks(onGetConfigNames, onFault);
}

function onGetConfigNames(res) {
	if(res["result"] != false && res["result"][0].length > 0){
		console.log("fill conf");
		var selector = document.getElementById("configSelect");
		
		replaceChildNodes(selector);
		for(i in res["result"][0]){
			if(i == res["result"][1]){
				attr = {"value":res["result"][0][i]["confid"], "selected":"selected"}
			}else{
				attr = {"value":res["result"][0][i]["confid"]};
			}
			
			appendChildNodes(selector, OPTION(attr, res["result"][0][i]["name"]));
		}
	}else if(window.location.href.search("newconf") == -1){
		window.location.href = "newconf";
	}
	
	initPage();
}

function configChange() {
	var selector = document.getElementById("configSelect");
	
	var d = loadJSONDoc("/cm/setConfiguration", {"confid": selector.options[selector.selectedIndex].value});
	d.addCallbacks(onSetConfigurationResult, onFault);
}

function onSetConfigurationResult(res) {
	initPage()
}

function newConfig() {
	var formdata = {
		configname: document.getElementById("form_configname").value,
		domain: document.getElementById("form_domain").value,
		o: document.getElementById("form_o").value,
		ou: document.getElementById("form_ou").value,
		c: document.getElementById("form_c").value,
		st: document.getElementById("form_st").value,
		l: document.getElementById("form_l").value
	};
	
	var d = loadJSONDoc("/cm/newConfiguration", formdata);
	d.addCallbacks(onNewConfig, onFault);
}

function onNewConfig(res) {
	getConfigNames();
	window.location.href = "";
}

function delConf(){
	var selector = document.getElementById("configSelect");
	
	var d = loadJSONDoc("/cm/delConfiguration", {"confid": selector.options[selector.selectedIndex].value});
	d.addCallbacks(onDelConfig, onFault);
}

function onDelConfig(){
	getConfigNames();
}

function onFault(error) {
	console.log(error);
}