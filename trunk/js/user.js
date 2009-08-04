
function getUsers() {
	var d = loadJSONDoc("/um/getUserNames");
	d.addCallbacks(onGetUserNames, onFault);
}

function onGetUserNames(res) {
	var uDiv = document.getElementById("userDiv");
	var users = res["result"];
	
	html = "";
	for(i in users) {
		html += '<div id="userDiv_'+users[i]["id"]+'" class="userNameDiv">'+
				users[i]["name"]+
				'<div class="userControlDiv">' +
					'<button type="button" onclick="userGet('+users[i]["id"]+');">download</button>' +
					'<button type="button" onclick="userEdit();">edit</button>' +
					'<button type="button" onclick="userDelete('+users[i]["id"]+');">delete</button>' +
				'</div>'+
			'</div>';
	}
	
	uDiv.innerHTML = html;
}

function displayAddUserDiv() {
	var addDiv = document.getElementById("addDiv");
	document.getElementById("addForm").reset();
	
	if(addDiv.style.display == "inline"){
		addDiv.style.display = "none";
	}else{
		addDiv.style.display = "inline";
	}
}

function addUser() {
	if(document.getElementById("userAddPass").value == document.getElementById("userAddPass2").value){
		console.log("addUser");
		
		var formdata = {
			name: document.getElementById("userAddName").value,
			password: document.getElementById("userAddPass").value
		}
		
		var d = loadJSONDoc("/um/addUser", formdata);
		d.addCallbacks(onAddUser, onFault);
	}else{
		console.log("ww != ww");
	}
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
	
}

function onFault(error) {
	console.log(error);
}