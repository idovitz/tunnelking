

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