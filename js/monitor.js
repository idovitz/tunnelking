
function loadStatus(){
	var d = loadJSONDoc("/cm/getStatus");
	d.addCallbacks(onLoadStatus, onFault);
}

function onLoadStatus(res){	
	var connections = res["result"]["connections"];
	
	var ccount = 0;
	var html = "";
	html += '<div id="conDiv_header" '+style+' class="connectionDiv">'+
				'<div style="width: 120px; float: left; margin-left: 4px; font-weight: bold;">'+
					"Name"+
				'</div>'+
				'<div style="width: 160px; float: left; margin-left: 4px; font-weight: bold;">'+
					"Initial time"+
				'</div>'+
				'<div style="width: 160px; float: left; margin-left: 4px; font-weight: bold;">'+
					"Last activity"+
				'</div>'+
				'<div style="width: 100px; float: left; margin-left: 4px; font-weight: bold;">'+
					"up/down"+
				'</div>'+
				'<div style="width: 180px; float: left; margin-left: 4px; font-weight: bold;">'+
					"VPN/Remote ip"+
				'</div>'+
			'</div>';
	
	for(i in connections){
		
		if(ccount % 2)
			var style = "style='background-color: #EEEEEE;'";
		else
			var style = "style='background-color: #DDDDDD;'";
		
		html += '<div id="conDiv_'+i+'" '+style+' class="connectionDiv">'+
					'<div style="float: left; width: 120px; margin-left: 4px;">'+
						connections[i][0][0]+
					'</div>'+
					'<div style="float: left; width: 160px; margin-left: 4px;">'+
						connections[i][0][4]+
					'</div>'+
					'<div style="float: left; width: 160px; margin-left: 4px;">'+
						connections[i][1][3]+
					'</div>'+
					'<div style="float: left; width: 100px; margin-left: 4px;">'+
						bitsToByteString(parseInt(connections[i][0][2]))+"/"+bitsToByteString(parseInt(connections[i][0][3]))+
					'</div>'+
					'<div style="float: left; width: 180px; margin-left: 4px;">'+
						connections[i][1][0]+"/"+connections[i][1][2].split(":")[0]+
					'</div>'+
					'<div style="float: right;">' +
						'<img src="img/kill.png" onclick="kill(\''+i+'\')" />' +
					'</div>'+
				'</div>';
		ccount++;
	}
	
	connectionsDiv = document.getElementById("connectionsDiv");
	
	connectionsDiv.innerHTML = html;
}

function bitsToByteString(bits){
	if(bits < 1000000){
		return Math.round(bits/1024, 1)+"Kb";
	}else{
		return Math.round(bits/1024/1024*10)/10+"Mb";
	}
}

function kill(cid) {
	if(confirm("Really kill this connection?")) {
		var d = loadJSONDoc("/cm/killConnection", {cid:cid});
		d.addCallbacks(onKill, onFault);
	}
}

function onKill(res) {
	loadStatus();
}
