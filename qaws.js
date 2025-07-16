// log function
function append(text) {
  console.log(text);
}

// Global variable for websocket
var websocket = null;

// connection function
function wsrobot_init(ip, port) {
    var url = "ws://" + ip + ":" + port + "/modimwebsocketserver";
    websocket = new WebSocket(url);

    websocket.onmessage = function(event) {
        console.log("message received: " + event.data);
        const v = event.data.split('_');
        let messageValue = v.slice(3).join('_');

        // management command
        if (v[0] == 'display') {
            if (v[1] == 'text') {
                // Check if it is a special command for the warning bar
                if (v[2] === 'attentionscore') {
                    // Call the global function defined in index.html
                    if (typeof updateAttentionScore === 'function') {
                        const score = parseInt(messageValue) || 0;
                        updateAttentionScore(score);
                    }
                } else {
                    // Otherwise, it is plain text
                    const elementId = v[1] + '_' + v[2];
                    if (document.getElementById(elementId)) {
                        document.getElementById(elementId).innerHTML = messageValue;
                    }
                }
            } else if (v[1] == 'image') {
                let p = v.slice(3).join('_');
                document.getElementById('image_default').src = p;
            } else if (v[1] == 'button') {
                var b = document.createElement("button"); 
                b.className = "btn bg-rose-600 hover:bg-rose-700 text-white text-lg py-3 px-6 rounded-xl m-2 transition";
                let p = v.slice(2).join('_');
                let vp = p.split('$');
                b.id = vp[0];
                b.textContent = vp[1]; 
                b.onclick = function(event) { button_fn(event) };

                var bdiv = document.getElementById("buttons");
                bdiv.appendChild(b);
            }
        } else if (v[0] == 'remove' && v[1] == 'buttons') {
            var bdiv = document.getElementById("buttons");
            while (bdiv.firstChild) {
                bdiv.removeChild(bdiv.firstChild);
            }
        }
    };

    websocket.onopen = function() {
        append("connection received");
        document.getElementById("status").innerHTML = "<font color='green'>OK</font>";
    };
    websocket.onclose = function() {
        append("connection closed");
        document.getElementById("status").innerHTML = "<font color='red'>NOT CONNECTED</font>";
    };
    websocket.onerror = function() {
        append("!!!connection error!!!");
    };
}

// Function to send data
function wsrobot_send(data) {
  if (websocket != null)
    websocket.send(data);
}

// Button click management function
function button_fn(event) {
  var bsrc = event.currentTarget; 
  console.log('websocket button ' + bsrc.id);
  wsrobot_send(bsrc.id);
}