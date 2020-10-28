var socket;
var timeoutID = 0;

function init() {

  if (typeof API_Key === "undefined") {
    $("body").html("No API Key found or load!<br>Rightclick on the script in ChatBot and select \"Insert API Key\"");
    $("body").css({"font-size": "20px", "color": "#ff8080", "text-align": "center"});
  } else {
    connectWebsocket();
  }
  configure()
};

function connectWebsocket() {
  socket = new WebSocket("ws://127.0.0.1:3337/streamlabs");
  socket.onopen = onOpen;
  socket.onmessage = onMessage;
  socket.onerror = (error) => console.log("Error: " + error);
  socket.onclose = () => {
    // Clear socket to avoid multiple ws objects and EventHandlings
    socket = null;
    // Try to reconnect every 5s
    setTimeout(connectWebsocket, 5000);
  };
}

function onOpen() {
  var auth = {
    author: "WillDBot",
    website: "twitch.tv",
    api_key: API_Key,
    events: [settings.WSEventName]
  };
  console.log(auth);
  socket.send(JSON.stringify(auth));
}


function onMessage(socketMessage) {
  var message = JSON.parse(socketMessage.data);
  console.log(message);

  // Remove any Previous instances of img or source
  $('img').remove();
  $('source').attr('src', '');
  $('video').css('visibility', 'hidden');

  if (message.event === settings.WSEventName) {
    var eventData = JSON.parse(message.data);
    console.log(eventData);

    var image_url = `../Images/${eventData.ImageFile}`;
    if (image_url.endsWith(".webm")) {
      var video = $('video');
      var source = video.get(0);
      source.src = image_url;
      video.on("canplaythrough", (e) => {
        source.play();
        $('video').css('visibility', 'visible');
        alert(eventData);
      });
      source.load();
    } else if (image_url.endsWith(".gif") || image_url.endsWith(".jpg") || image_url.endsWith(".png")) {
      loadImg({ src: image_url }, function (status) {
        if (!status.err) {
          console.log("Loaded image", status);
          $('#alert').prepend($(status.img));
          alert(eventData)
        } else {
          $('p').text(status.err);
          console.log("image error", status.err);
        }
      });
    }
  }
};

function alert(eventData) {
  var duration = parseInt(eventData.Duration) || 5;
  var transType = eventData.TransitionType || "Scale";
  var message = eventData.Message || "";
  var expandDirection = eventData.ExpandDirection || "center";
  var alignHorizontal = parseInt(eventData.AlignHorizontal) || 50;
  var alignVertical = parseInt(eventData.AlignVertical) || 50;
  var font = eventData.Font || "bold 70px japanese2020";
  var color = eventData.Color || "red";

  $('#text').text('');
  try { clearTimeout(timeoutID); } catch(error) {}
  $("#text").text(message);

  $("#counter").removeClass().addClass(expandDirection + "expand");
  $("#text").css({
    "text-align": expandDirection,
    "word-wrap": "break-word",
    "font": font,
    "color": color,
    "text-shadow": "2px 2px #000"
  });

  if (expandDirection === "right"){
    $(".rightexpand").css("left", alignHorizontal + "%")
    $(".rightexpand").css("top", alignVertical + "%")
  } else if (expandDirection === "center") {
    $(".centerexpand").css("left", alignHorizontal + "%")
    $(".centerexpand").css("top", alignVertical + "%")
  } else {
    var rightAlign = 100 - alignHorizontal;
    $(".leftexpand").css("right", rightAlign + "%")
    $(".leftexpand").css("top", alignVertical + "%")
  }
  $("#alert").removeClass(`${transType}Out initialHide`).addClass(`${transType}In`);
  var next = () => $("#alert").removeClass(`${transType}In`).addClass(`${transType}Out`);
  timeoutID = setTimeout(next, duration * 1000);
}

function loadImg(options, callback) {
  var seconds = 0,
  maxSeconds = 10,
  complete = false,
  done = false;

  if (options.maxSeconds) {
    maxSeconds = options.maxSeconds;
  }

  function tryImage() {
    if (done) { return; }
    if (seconds >= maxSeconds) {
      callback({ err: 'timeout' });
      done = true;
      return;
    }
    if (complete && img.complete) {
      if (img.width && img.height) {
        callback({ img: img });
        done = true;
        return;
      }
      callback({ err: '404' });
      done = true;
      return;
    } else if (img.complete) {
      complete = true;
    }
    seconds++;
    callback.tryImage = setTimeout(tryImage, 1000);
  }

  var img = new Image();
  img.onload = tryImage();
  img.src = options.src;
  tryImage();
}

// $('button').click(function () {});

function configure() {

}

$(document).ready(init)
