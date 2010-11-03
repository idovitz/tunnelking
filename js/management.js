

function loadStatus(){
	var d = loadJSONDoc("/cm/getStatus");
	d.addCallbacks(onLoadStatus, onFault);
}

function onLoadStatus(res){
	var statusDiv = document.getElementById("statusDiv");
	
	var runningText = "";
	if(res["result"]["running"]){
		runningText = "server is running";
	}else{
		runningText = "server is not running";
	}
	
	var ccount = 0;
	for(i in res["result"]["connections"]){
		ccount++;
	}
	
	if(ccount == 1)
		runningText += "<a href=\"/monitor\"><br/>"+ccount+" user logged in</a>";
	else if(ccount > 1)
		runningText += "<a href=\"/monitor\"><br/>"+ccount+" users logged in</a>";
	
	statusDiv.innerHTML = runningText;
}

function stoprestart(action){
	if(confirm("Really "+action+" this configuration?")) {
		var d = loadJSONDoc("/cm/stoprestart", {'action':action});
		d.addCallbacks(onStoprestart, onFault);
	}
}

function onStoprestart(res){
	loadStatus();
}

function savePushOptions(){
	var options = new Array();
	
	if(document.getElementById("routesField").value != ""){
		var routes = document.getElementById("routesField").value.split("\n");
		
		for(var i=0; i<routes.length; i++){
			if(strip(routes[i]) != "")
				options.push("route "+strip(routes[i]));
		}
	}
	
	if(strip(document.getElementById("dnsField1").value) != "")
		options.push("dhcp-option DNS "+strip(document.getElementById("dnsField1").value));
	if(strip(document.getElementById("dnsField2").value) != "")
		options.push("dhcp-option DNS "+strip(document.getElementById("dnsField2").value));
	if(strip(document.getElementById("winsField1").value) != "")
		options.push("dhcp-option WINS "+strip(document.getElementById("winsField1").value));
	if(strip(document.getElementById("winsField2").value) != "")
		options.push("dhcp-option WINS "+strip(document.getElementById("winsField2").value));
	if(strip(document.getElementById("domainField").value) != "")
		options.push("dhcp-option DOMAIN "+strip(document.getElementById("domainField").value));
	
	if(document.getElementById("customsField").value != ""){
		var customs = document.getElementById("customsField").value.split("\n");
		
		for(var i=0; i<customs.length; i++){
			if(strip(customs[i]) != "")
				options.push(strip(customs[i]));
		}
	}
	
	var d = loadJSONDoc("/cm/savePushOptions", {optionContainer:serializeJSON({options:options})});
	d.addCallbacks(onSavePushOptions, onFault);
}

function onSavePushOptions(res){
	
}

function loadPushOptions(){
	var d = loadJSONDoc("/cm/loadPushOptions");
	d.addCallbacks(onLoadPushOptions, onFault);
}

function onLoadPushOptions(res){
	document.getElementById("routesField").value = "";
	document.getElementById("customsField").value = "";
	dnsCount = 1;
	winsCount = 1;
	
	for(var i=0; i<res["result"].length; i++){
		if(res["result"][i].search("route") != -1 && res["result"][i].search("route-") == -1){
			document.getElementById("routesField").value += res["result"][i].replace("route ", "")+"\n";
		}else if(res["result"][i].search("dhcp-option DNS") != -1 && dnsCount < 3){
			document.getElementById("dnsField"+dnsCount).value = res["result"][i].replace("dhcp-option DNS ", "");
			dnsCount++;
		}else if(res["result"][i].search("dhcp-option WINS") != -1 && winsCount < 3){
			document.getElementById("winsField"+winsCount).value = res["result"][i].replace("dhcp-option WINS ", "");
			winsCount++;
		}else if(res["result"][i].search("dhcp-option DOMAIN") != -1){
			document.getElementById("domainField").value = res["result"][i].replace("dhcp-option DOMAIN ", "");
		}else{
			document.getElementById("customsField").value += res["result"][i]+"\n";
		}
	}
}