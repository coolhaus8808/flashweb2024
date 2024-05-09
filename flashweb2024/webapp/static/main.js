var socket = io.connect('http://localhost:5555');


socket.on('connect', function () {
    console.log('Connected');
});

